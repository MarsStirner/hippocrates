# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.sql.expression import func, and_, or_

from hippocrates.blueprints.risar.lib.utils import format_action_data
from hippocrates.blueprints.risar.lib.expert.utils import em_stats_status_list
from hippocrates.blueprints.risar.lib.expert.em_generation import EventMeasureGenerator

from nemesis.models.expert_protocol import EventMeasure, Measure
from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action, update_action
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.lib.utils import safe_datetime, safe_traverse, safe_int


logger = logging.getLogger('simple')


class EventMeasureController(BaseModelController):
    error_message = None
    exception = None

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

    def cancel(self, em):
        em.status = MeasureStatus.cancelled[0]
        return em

    def delete(self, em):
        em.deleted = 1
        return em

    def restore(self, em):
        em.deleted = 0
        return em

    def make_assigned(self, em):
        if em.status == MeasureStatus.created[0]:
            em.status = MeasureStatus.assigned[0]
        return em

    def make_performed(self, em):
        if em.status != MeasureStatus.performed[0]:
            em.status = MeasureStatus.performed[0]
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
        em.result_action = em_result
        self.make_performed(em)
        return em_result

    def update_em_result(self, em, em_result, json_data):
        json_data = format_action_data(json_data)
        em_result = update_action(em_result, **json_data)
        em.result_action = em_result
        self.make_performed(em)
        return em_result

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
        if not end_date:
            end_date = action.endDate
        args.update({
            'event_id': action.event_id,
            'end_date_from': start_date
        })
        if end_date:
            args['beg_date_to'] = end_date
        return self.get_selecter().get_measures_in_action(args)

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
