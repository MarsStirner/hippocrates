# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import func, and_, or_

from blueprints.risar.lib.utils import format_action_data
from blueprints.risar.lib.expert.utils import em_stats_status_list
from blueprints.risar.lib.expert.em_generation import EventMeasureGenerator
from blueprints.risar.lib.expert.em_diagnosis import get_measure_result_mkbs
from blueprints.risar.lib.datetime_interval import DateTimeInterval
from blueprints.risar.lib.diagnosis import DiagnosesSystemManager, AdjasentInspectionsState
from blueprints.risar.risar_config import inspections_span_flatcodes

from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action, update_action, safe_datetime
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class EMGenerateException(Exception):
    pass


class EventMeasureController(BaseModelController):

    ds_emr_apt_codes = ('MainDiagnosis', 'FinalDiagnosis')

    def get_selecter(self):
        return EventMeasureSelecter()

    def regenerate(self, action):
        gen = EventMeasureGenerator(action)
        try:
            gen.generate_measures()
        except Exception, e:
            logger.error(u'Ошибка генерации мероприятий для action с id={0}'.format(action.id), exc_info=True)
            raise EMGenerateException(u'Ошибка генерации мероприятий')

    def delete_in_action(self, action):
        gen = EventMeasureGenerator(action)
        gen.clear_existing_measures()

    def execute(self, em):
        em.status = MeasureStatus.performed[0]
        return em

    def cancel(self, em):
        em.status = MeasureStatus.cancelled[0]
        return em

    def make_assigned(self, em):
        if em.status == MeasureStatus.created[0]:
            em.status = MeasureStatus.assigned[0]
        return em

    def get_new_appointment(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.measure.appointmentAt_id
        appointment = create_action(action_type_id, event_id, properties=action_props, data=action_data)
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
        self.make_assigned(em)
        return em_result

    def update_em_result(self, em, em_result, json_data):
        json_data = format_action_data(json_data)
        em_result = update_action(em_result, **json_data)
        self._set_emr_data(em_result)
        em.result_action = em_result
        return em_result

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

    def get_measures_in_action(self, action):
        if not action.id:
            return []
        start_date = safe_datetime(action.begDate)
        end_date = safe_datetime(action.propsByCode['next_date'].value)
        if not end_date:
            end_date = action.endDate
        if not end_date:
            end_date = start_date
        args = {
            'event_id': action.event_id,
            'beg_date_to': end_date,
            'end_date_from': start_date
        }
        return self.get_listed_data(args)

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
            new_diagnoses, changed_diagnoses = diag_sys.get_result()

            create_or_update_diagnoses(em_result, new_diagnoses)
            db.session.add_all(changed_diagnoses)
            db.session.flush()
            self.modify_emr(em_result, emr_data['new_beg_date'], emr_data['new_person'])

        ais.refresh(em_result)

        diag_sys = DiagnosesSystemManager.get_for_measure_result(
            em_result, 'final', None, ais)
        diag_sys.refresh_with_measure_result(new_diags)
        new_diagnoses, changed_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(em_result, new_diagnoses)
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
        if 'measure_type_id_list' in flt:
            self.query = self.query.outerjoin(ExpertSchemeMeasureAssoc).join(
                Measure, or_(
                    Measure.id == ExpertSchemeMeasureAssoc.measure_id,
                    Measure.id == EventMeasure.measure_id,
                )
            ).filter(Measure.measureType_id.in_(flt['measure_type_id_list']))
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
        self.query = self.query.filter(EventMeasure.deleted == 0)
        return self

    def apply_sort_order(self, **order_options):
        EventMeasure = self.model_provider.get('EventMeasure')
        Action = self.model_provider.get('Action')

        desc_order = order_options.get('order', 'ASC') == 'DESC'
        if order_options:
            pass
        else:
            source_action = aliased(Action, name='SourceAction')
            self.query = self.query.join(
                source_action, EventMeasure.sourceAction_id == source_action.id
            ).order_by(
                source_action.begDate.desc(),
                EventMeasure.begDateTime.desc(),
                EventMeasure.id.desc()
            )
        return self

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
