# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.sql.expression import func, and_, or_

from hippocrates.blueprints.risar.lib.utils import format_action_data, get_action_by_id
from hippocrates.blueprints.risar.lib.expert.utils import em_stats_status_list, em_final_status_list
from hippocrates.blueprints.risar.lib.expert.em_generation import EventMeasureGenerator
from hippocrates.blueprints.risar.lib.diagnosis import get_inspection_primary_diag_mkb, DiagnosesSystemManager, \
    AdjasentInspectionsState
from hippocrates.blueprints.risar.lib.expert.em_diagnosis import get_measure_result_mkbs
from hippocrates.blueprints.risar.lib.datetime_interval import DateTimeInterval
from hippocrates.blueprints.risar.risar_config import inspections_span_flatcodes

from nemesis.models.expert_protocol import EventMeasure, Measure, rbMeasureCancelReason
from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action, update_action
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_datetime, safe_traverse, safe_int, safe_traverse_attrs, db_non_flushable
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class EventMeasureException(Exception): pass


class EventMeasureController(BaseModelController):
    error_message = None
    exception = None

    ds_emr_apt_codes = ('MainDiagnosis', 'FinalDiagnosis')

    def get_selecter(self):
        return EventMeasureSelecter()

    def regenerate(self, action):
        gen = EventMeasureGenerator.get_for_pregnancy(action)
        try:
            gen.generate_measures()
        except Exception, e:
            logger.error(u'Ошибка генерации мероприятий для action с id={0}'.format(action.id), exc_info=True)
            self.error_message = u'Ошибка генерации мероприятий'
            self.exception = e

    def regenerate_gyn(self, action):
        gen = EventMeasureGenerator.get_for_gynecol(action)
        try:
            gen.generate_measures()
        except Exception, e:
            logger.error(u'Ошибка генерации мероприятий для action с id={0}'.format(action.id), exc_info=True)
            self.error_message = u'Ошибка генерации мероприятий'
            self.exception = e

    def delete_in_action(self, action):
        gen = EventMeasureGenerator.get(action)
        gen.clear_existing_measures()

    def execute(self, em):
        em.status = MeasureStatus.performed[0]
        return em

    def cancel(self, em, data=None):
        em.status = MeasureStatus.cancelled[0]
        if data and 'cancel_reason' in data:
            cr_id = safe_traverse(data, 'cancel_reason', 'id')
            em.cancel_reason = rbMeasureCancelReason.query.get(cr_id) if cr_id else None
        return em

    def delete(self, em):
        em.deleted = 1
        return em

    def restore(self, em):
        em.deleted = 0
        return em

    def make_assigned(self, em):
        if em.status in (MeasureStatus.created[0], MeasureStatus.upon_med_indications[0]):
            em.status = MeasureStatus.assigned[0]
        return em

    def make_performed(self, em):
        if em.status != MeasureStatus.performed[0]:
            em.status = MeasureStatus.performed[0]
        return em

    def get_new_appointment(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.measure.appointmentAt_id
        if not action_type_id:
            raise EventMeasureException(u'Невозможно создать направление, не указан `appointmentAt_id`')
        appointment = create_action(action_type_id, event_id, properties=action_props, data=action_data)
        return appointment

    def fill_new_appointment(self, appointment, data):
        """Заполнить новое направление данными по умолчанию"""
        event = org = cur_inspection = None
        if 'em' in data:
            event = data['em'].event
            org = event.execPerson.organisation
        if 'checkup_id' in data:
            cur_inspection = get_action_by_id(data['checkup_id'])

        if org and 'LPUDirection' in appointment.propsByCode:
            appointment['LPUDirection'].value = org
        if cur_inspection and 'DateDirection' in appointment.propsByCode:
            appointment['DateDirection'].value = cur_inspection.begDate
        if cur_inspection and 'DirectionDate' in appointment.propsByCode:
            appointment['DirectionDate'].value = cur_inspection.begDate
        if cur_inspection and 'DiagnosisDirection' in appointment.propsByCode:
            appointment['DiagnosisDirection'].value = get_inspection_primary_diag_mkb(cur_inspection)
        return appointment

    def create_appointment(self, em, json_data):
        json_data = format_action_data(json_data)
        if 'properties' in json_data:
            props = json_data.pop('properties')
        else:
            props = []
        appointment = self.get_new_appointment(em, json_data, props)
        em.appointment_action = appointment
        self.make_assigned(em)
        return appointment

    def update_appointment(self, em, appointment, json_data):
        json_data = format_action_data(json_data)
        appointment = update_action(appointment, **json_data)
        em.appointment_action = appointment
        return appointment

    def get_new_em_result(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.measure.resultAt_id
        em_result = create_action(action_type_id, event_id, properties=action_props, data=action_data)
        return em_result

    def create_em_result(self, em, json_data):
        json_data = format_action_data(json_data)
        if 'properties' in json_data:
            props = json_data.pop('properties')
        else:
            props = []
        em_result = self.get_new_em_result(em, json_data, props)
        self._set_emr_data(em_result)
        em.result_action = em_result
        self.make_performed(em)
        return em_result

    def update_em_result(self, em, em_result, json_data):
        json_data = format_action_data(json_data)
        em_result = update_action(em_result, **json_data)
        self._set_emr_data(em_result)
        em.result_action = em_result
        self.make_performed(em)
        if 'attached_files' in json_data:
            em_result = self.edit_emr_attach_files(em_result, json_data['attached_files'])
        return em_result

    def edit_emr_attach_files(self, action, attach_data):
        cur_attaches = dict((attach.id, attach) for attach in action.attach_files)
        for at_data in attach_data:
            attach = cur_attaches.pop(at_data['id'], None)
            if attach is not None:
                fm = attach.file_meta
                fm.name = at_data['file_meta']['name']
        for attach in cur_attaches.values():
            attach.deleted = 1
            attach.file_meta.deleted = 1
        return action

    def get_new_event_measure(self, data):
        em = EventMeasure()
        em.begDateTime = safe_datetime(data.get('beg_datetime')) or datetime.datetime.now()
        em.endDateTime = safe_datetime(data.get('end_datetime'))
        default_status_id = MeasureStatus.created[0]
        em.status = safe_traverse(data, 'status', 'id', default=default_status_id)
        em.event_id = safe_int(data['event_id'])
        measure_id = safe_traverse(data, 'measure', 'id')
        if not measure_id:
            measure_id = data['measure_id']
        measure = Measure.query.get(measure_id)
        em.measure_id = measure.id
        em.manual_measure = measure
        return em

    def save_list(self, event, data):
        res = []
        for em_data in data:
            em_id = em_data.get('id')
            if em_id:
                raise NotImplementedError('cannot save event_measure list')
            else:
                new_em = self.get_new_event_measure(em_data['data'])
            res.append(new_em)
        return res

    def _set_emr_data(self, em_result):
        if 'CheckupDate' in em_result.propsByCode:
            new_date = safe_datetime(em_result.propsByCode['CheckupDate'].value)
        elif 'IssueDate' in em_result.propsByCode:
            new_date = safe_datetime(em_result.propsByCode['IssueDate'].value)
        else:
            new_date = None
        if 'Doctor' in em_result.propsByCode:
            new_doctor = em_result.propsByCode['Doctor'].value
        else:
            new_doctor = None
        self.modify_emr(em_result, new_date, new_doctor)

    def get_measures_in_event(self, event, args, paginate=False):
        event_id = event.id if event is not None else args.get('event_id')
        if not event_id:
            raise ValueError('`event` argument or `event_id` in `args` required')
        args.update({
            'event_id': event_id
        })
        if paginate:
            return self.get_paginated_data(args)
        else:
            return self.get_listed_data(args)

    def get_measures_in_action(self, action, args=None):
        if not action.id:
            return []
        if args is None:
            args = {}
        start_date = safe_datetime(action.begDate)
        next_date_property = action.propsByCode.get('next_date')
        end_date = safe_datetime(next_date_property.value) if next_date_property else None
        if end_date:
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            end_date = action.endDate
        args.update({
            'event_id': action.event_id,
            'end_date_from': start_date
        })
        if end_date:
            args['beg_date_to'] = end_date
        return self.get_selecter().get_measures_in_action(args)

    def get_measure(self, measure_id):
        return self.get_selecter().get_measure(measure_id)

    def calc_event_measure_stats(self, event):
        sel = self.get_selecter()
        sel.set_calc_event_stats(event.id)
        data = sel.get_one()
        lab_total = data.count_lab_test or 0
        lab_complete = data.count_lab_test_completed or 0
        lab_pct = round(lab_complete * 100 / lab_total if (lab_total != 0 and lab_complete != 0) else 0)
        func_total = data.count_func_test or 0
        func_complete = data.count_func_test_completed or 0
        func_pct = round(func_complete * 100 / func_total if (func_total != 0 and func_complete != 0) else 0)
        checkup_total = data.count_checkup or 0
        checkup_complete = data.count_checkup_completed or 0
        checkup_pct = round(checkup_complete * 100 / checkup_total if (checkup_total != 0 and checkup_complete != 0) else 0)
        hosp_total = data.count_hosp or 0
        hosp_complete = data.count_hosp_completed or 0
        hosp_pct = round(hosp_complete * 100 / hosp_total if (hosp_total != 0 and hosp_complete != 0) else 0)
        return {
            'lab': {
                'complete': lab_complete,
                'total': lab_total,
                'percent': lab_pct,
            },
            'func': {
                'complete': func_complete,
                'total': func_total,
                'percent': func_pct,
            },
            'checkups': {
                'complete': checkup_complete,
                'total': checkup_total,
                'percent': checkup_pct,
            },
            'hosp': {
                'complete': hosp_complete,
                'total': hosp_total,
                'percent': hosp_pct,
            }
        }

    def update_patient_diagnoses(self, em_result, create_mode=False, old_mr_data=None):
        """
        См. CheckupsXForm.update_diagnoses_system
        """
        if not create_mode and not old_mr_data:
            raise ValueError('`old_mr_data` required')
        new_mr_data = self.get_emr_data_for_diags(em_result)
        # prepare data
        if not create_mode:
            emr_data = {
                'old_mkbs': old_mr_data['mkbs'],
                'new_mkbs': new_mr_data['mkbs'],
                'old_beg_date': old_mr_data['beg_date'],
                'new_beg_date': new_mr_data['beg_date'],
                'old_person': old_mr_data['person'],
                'new_person': new_mr_data['person']
            }
            emr_data['changed'] = any(emr_data[o] != emr_data[n] for o, n in (
                ('old_mkbs', 'new_mkbs'), ('old_beg_date', 'new_beg_date'), ('old_person', 'new_person')
            ))
        else:
            emr_data = {
                'new_mkbs': new_mr_data['mkbs']
            }

        ais = AdjasentInspectionsState(inspections_span_flatcodes, create_mode)

        measure_mkbs = emr_data['new_mkbs']
        new_diags = [dict(kind='associated', mkbs=measure_mkbs)]

        # recalc for previous state
        if not create_mode and emr_data['changed']:
            target = self.modify_emr(em_result, emr_data['old_beg_date'], emr_data['old_person'])
            ais.refresh(em_result)

            diag_sys = DiagnosesSystemManager.get_for_measure_result(
                target, 'final', None, ais)
            fut_interval = DateTimeInterval(emr_data['new_beg_date'], emr_data['new_beg_date'])
            diag_sys.refresh_with_measure_result_old_state(new_diags, fut_interval)
            new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()

            create_or_update_diagnoses(em_result, new_diagnoses)
            for d in new_oa_diagnoses:
                create_or_update_diagnoses(d['action'], [d['data']])
            db.session.add_all(changed_diagnoses)
            db.session.flush()
            self.modify_emr(em_result, emr_data['new_beg_date'], emr_data['new_person'])

        ais.refresh(em_result)

        diag_sys = DiagnosesSystemManager.get_for_measure_result(
            em_result, 'final', None, ais)
        diag_sys.refresh_with_measure_result(new_diags)
        new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(em_result, new_diagnoses)
        for d in new_oa_diagnoses:
            create_or_update_diagnoses(d['action'], [d['data']])
        db.session.add_all(changed_diagnoses)
        db.session.flush()

    def emr_changes_diagnoses_system(self, emr):
        return any(prop_code in self.ds_emr_apt_codes for prop_code in emr.propsByCode)

    def get_emr_data_for_diags(self, em_result):
        mkbs = get_measure_result_mkbs(em_result, self.ds_emr_apt_codes)
        return {
            'mkbs': mkbs,
            'beg_date': em_result.begDate,
            'person': em_result.person
        }

    def modify_emr(self, em_result, new_date, new_person):
        if new_date:
            em_result.begDate = em_result.endDate = new_date
        if new_person:
            em_result.person = new_person
        return em_result

    @db_non_flushable
    def save_appointment_list(self, item_list, action):
        """Сохраняет списоок мероприятий, создаёт направляения, проставляет им LPUDirection"""
        result = []
        org = action.event.execPerson.organisation
        cur_beg_date = action.begDate
        cur_main_diag = get_inspection_primary_diag_mkb(action)
        for em_id in item_list:
            em = EventMeasure.query.get(em_id)
            if not em:
                raise ApiException(404, u'Не найдено EM с id = '.format(em_id))

            if not em.appointmentAction_id:
                try:
                    appointment = self.get_new_appointment(em)
                except EventMeasureException:
                    continue
                if 'LPUDirection' in appointment.propsByCode:
                    appointment['LPUDirection'].value = org
                if 'DateDirection' in appointment.propsByCode:
                    appointment['DateDirection'].value = cur_beg_date
                if 'DirectionDate' in appointment.propsByCode:
                    appointment['DirectionDate'].value = cur_beg_date
                if 'DiagnosisDirection' in appointment.propsByCode:
                    appointment['DiagnosisDirection'].value = cur_main_diag

                em.appointment_action = appointment
                self.make_assigned(em)
            else:
                appointment = em.appointment_action

            if appointment:
                result.append(em)
        return result

    def close_all_unfinished_ems(self, action):
        event = action.event

        db.session.query(EventMeasure).filter(
            EventMeasure.event_id == event.id,
            EventMeasure.status.notin_(em_final_status_list),
        ).update({
            EventMeasure.status: MeasureStatus.cancelled[0]
        }, synchronize_session=False)

    def store_appointments(self, em_list, silent=False):
        """Сохранить список направлений по мероприятиям (список Action).

        Используются SQL Savepoint (или виртуальные транзакции sqlalchemy) для того,
        чтобы можно было провести транзакцию даже, если при сохранении части
        направлений будет формироваться контролируемое исключение (например, при
        создании направлений на госпитализацию будет сформировано исключение на уровне
        триггеров в бд, если не выполнятся проверки в триггерах таблицы Action,
        см. RIMIS-1820 , RIMIS-1857).
        """
        # новые объекты не должны быть в сессии, чтобы можно было вызвать flush
        # каждого insert Action по отдельности
        self.session.expunge_all()

        for em in em_list:
            self.session.begin_nested()  # savepoint , неявно вызовет вызовет flush
            try:
                self.session.add(em)
                self.session.flush()
            except Exception, e:
                # possible exception from db trigger (RIMIS-1820 , RIMIS-1857)
                # expected (pymysql.err.InternalError) (1644, '...')
                exc_info = safe_traverse_attrs(e, 'orig', 'args')
                if isinstance(exc_info, tuple) and exc_info[0] == 1644:
                    text = exc_info[1]
                    if silent:
                        self.session.rollback()  # rollback to savepoint
                        logger.warning(u'При сохранении списка направлений направление '
                                       u'по мероприятию с id={0} не было создано: {1}'.format(em.id, text))
                        continue
                    else:
                        raise ApiException(422, text)
                else:
                    raise e
            else:
                self.session.commit()  # release savepoint

        self.session.commit()


class EventMeasureSelecter(BaseSelecter):

    def __init__(self):
        query = self.model_provider.get_query('EventMeasure')
        super(EventMeasureSelecter, self).__init__(query)

    def apply_filter(self, **flt):
        EventMeasure = self.model_provider.get('EventMeasure')
        ExpertSchemeMeasureAssoc = self.model_provider.get('ExpertSchemeMeasureAssoc')
        Measure = self.model_provider.get('Measure')

        if 'id' in flt:
            self.query = self.query.filter(EventMeasure.id == flt['id'])
            return self
        if 'event_id' in flt:
            self.query = self.query.filter(EventMeasure.event_id == flt['event_id'])
        if 'action_id' in flt:
            self.query = self.query.filter(EventMeasure.sourceAction_id == flt['action_id'])
        if 'action_id_list' in flt:
            self.query = self.query.filter(EventMeasure.sourceAction_id.in_(flt['action_id_list']))
        if 'measure_id_list' in flt:
            self.query = self.query.outerjoin(ExpertSchemeMeasureAssoc).join(
                Measure, or_(
                    Measure.id == ExpertSchemeMeasureAssoc.measure_id,
                    Measure.id == EventMeasure.measure_id,
                )
            ).filter(Measure.id.in_(flt['measure_id_list']))
        if 'measure_type_id_list' in flt:
            if not self.is_joined(self.query, ExpertSchemeMeasureAssoc):
                self.query = self.query.outerjoin(ExpertSchemeMeasureAssoc).join(
                    Measure, or_(
                        Measure.id == ExpertSchemeMeasureAssoc.measure_id,
                        Measure.id == EventMeasure.measure_id,
                    ))
            self.query = self.query.filter(Measure.measureType_id.in_(flt['measure_type_id_list']))
        if 'beg_date_from' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime >= safe_datetime(flt['beg_date_from']))
        if 'beg_date_to' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime <= safe_datetime(flt['beg_date_to']))

        if 'end_date_from' in flt:
            self.query = self.query.filter(or_(EventMeasure.endDateTime >= safe_datetime(flt['end_date_from']),
                                               EventMeasure.endDateTime == None))
        if 'end_date_to' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime <= safe_datetime(flt['end_date_to']))
        if 'measure_status_id_list' in flt:
            self.query = self.query.filter(EventMeasure.status.in_(flt['measure_status_id_list']))
        if 'with_deleted_hand_measures' in flt:
            self.query = self.query.filter(
                func.IF(EventMeasure.measure_id.isnot(None), 1, EventMeasure.deleted == 0)
            )
        else:
            self.query = self.query.filter(EventMeasure.deleted == 0)
        return self

    def apply_sort_order(self, **order_options):
        EventMeasure = self.model_provider.get('EventMeasure')
        ExpertSchemeMeasureAssoc = self.model_provider.get('ExpertSchemeMeasureAssoc')
        Measure = self.model_provider.get('Measure')
        rbMeasureType = self.model_provider.get('rbMeasureType')

        order_options = order_options.get('order', {})
        desc_order = order_options.get('order', 'ASC') == 'DESC'

        if order_options:
            # not implemented
            pass
        else:
            joined_tables = {mapper.class_ for mapper in self.query._join_entities}
            if rbMeasureType not in joined_tables:
                if Measure not in joined_tables:
                    self.query = self.query.outerjoin(ExpertSchemeMeasureAssoc).join(
                        Measure, or_(Measure.id == ExpertSchemeMeasureAssoc.measure_id,
                                     Measure.id == EventMeasure.measure_id)
                    )
                self.query = self.query.join(rbMeasureType)
            self.query = self.query.order_by(
                EventMeasure.begDateTime,
                rbMeasureType.id,
                EventMeasure.id
            )
        return self

    def get_measures_in_action(self, args):
        EventMeasure = self.model_provider.get('EventMeasure')

        self.apply_filter(**args)
        self.apply_sort_order(**args)
        self.query = self.query.options(
            (joinedload(EventMeasure._scheme_measure).
             joinedload('schedule', innerjoin=True).
             joinedload('additional_mkbs')
             ),
            joinedload(EventMeasure._scheme_measure).joinedload('scheme', innerjoin=True),
            (joinedload(EventMeasure._scheme_measure).
             joinedload('measure', innerjoin=True).
             joinedload('measure_type', innerjoin=True)
             ),
            joinedload(EventMeasure._measure).joinedload('measure_type', innerjoin=True),
        )
        return self.get_all()

    def get_measure(self, measure_id):
        EventMeasure = self.model_provider.get('EventMeasure')

        self.query = self.query.options(
            (joinedload(EventMeasure._scheme_measure).
             joinedload('schedule', innerjoin=True).
             joinedload('additional_mkbs')
             ),
            joinedload(EventMeasure._scheme_measure).joinedload('scheme', innerjoin=True),
            (joinedload(EventMeasure._scheme_measure).
             joinedload('measure', innerjoin=True).
             joinedload('measure_type', innerjoin=True)
             ),
            joinedload(EventMeasure._measure).joinedload('measure_type', innerjoin=True),
        )
        return self.get_by_id(measure_id)

    def set_calc_event_stats(self, event_id):
        EventMeasure = self.model_provider.get('EventMeasure')
        ExpertSchemeMeasureAssoc = self.model_provider.get('ExpertSchemeMeasureAssoc')
        Measure = self.model_provider.get('Measure')
        rbMeasureType = self.model_provider.get('rbMeasureType')
        self.query = self.query.outerjoin(ExpertSchemeMeasureAssoc).join(
            Measure, or_(
                Measure.id == ExpertSchemeMeasureAssoc.measure_id,
                Measure.id == EventMeasure.measure_id,
            )
        ).join(
            rbMeasureType, rbMeasureType.id == Measure.measureType_id
        ).filter(
            EventMeasure.event_id == event_id,
            EventMeasure.deleted == 0,
            EventMeasure.status.in_(tuple(em_stats_status_list))
        ).with_entities(
            EventMeasure.id
        ).add_columns(
            # todo: code in const
            func.sum(func.IF(rbMeasureType.code == 'lab_test', 1, 0)).label('count_lab_test'),
            func.sum(func.IF(and_(rbMeasureType.code == 'lab_test',
                                  EventMeasure.status == MeasureStatus.performed[0]
                                  ), 1, 0)).label('count_lab_test_completed'),
            func.sum(func.IF(rbMeasureType.code == 'func_test', 1, 0)).label('count_func_test'),
            func.sum(func.IF(and_(rbMeasureType.code == 'func_test',
                                  EventMeasure.status == MeasureStatus.performed[0]
                                  ), 1, 0)).label('count_func_test_completed'),
            func.sum(func.IF(rbMeasureType.code == 'checkup', 1, 0)).label('count_checkup'),
            func.sum(func.IF(and_(rbMeasureType.code == 'checkup',
                                  EventMeasure.status == MeasureStatus.performed[0]
                                  ), 1, 0)).label('count_checkup_completed'),
            func.sum(func.IF(rbMeasureType.code == 'hospitalization', 1, 0)).label('count_hosp'),
            func.sum(func.IF(and_(rbMeasureType.code == 'hospitalization',
                                  EventMeasure.status == MeasureStatus.performed[0]
                                  ), 1, 0)).label('count_hosp_completed'),
        )
