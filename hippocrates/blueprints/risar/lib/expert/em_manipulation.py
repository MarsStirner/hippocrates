# -*- coding: utf-8 -*-

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import func, and_

from blueprints.risar.lib.utils import format_action_data
from blueprints.risar.lib.expert.utils import em_final_status_list

from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action, update_action, safe_datetime
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter


class EventMeasureController(BaseModelController):

    def get_selecter(self):
        return EventMeasureSelecter()

    def cancel(self, em):
        em.status = MeasureStatus.cancelled[0]
        return em

    def make_assigned(self, em):
        if em.status == MeasureStatus.created[0]:
            em.status = MeasureStatus.assigned[0]
        return em

    def get_new_appointment(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.scheme_measure.measure.appointmentAt_id
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
        action_type_id = em.scheme_measure.measure.resultAt_id
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
        self.make_assigned(em)
        return em_result

    def update_em_result(self, em, em_result, json_data):
        json_data = format_action_data(json_data)
        em_result = update_action(em_result, **json_data)
        em.result_action = em_result
        return em_result

    def calc_event_measure_stats(self, event):
        sel = self.get_selecter()
        sel.set_calc_event_stats(event.id)
        data = sel.get_one()
        lab_total = data.count_lab_test if data is not None else 0
        lab_complete = data.count_lab_test_completed if data is not None else 0
        lab_pct = round(lab_complete * 100 / lab_total if (lab_total != 0 and lab_complete != 0) else 0)
        func_total = data.count_func_test if data is not None else 0
        func_complete = data.count_func_test_completed if data is not None else 0
        func_pct = round(func_complete * 100 / func_total if (func_total != 0 and func_complete != 0) else 0)
        checkup_total = data.count_checkup if data is not None else 0
        checkup_complete = data.count_checkup_completed if data is not None else 0
        checkup_pct = round(checkup_complete * 100 / checkup_total if (checkup_total != 0 and checkup_complete != 0) else 0)
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
            }
        }


class EventMeasureSelecter(BaseSelecter):

    def __init__(self):
        query = self.model_provider.get_query('EventMeasure')  #.query.filter(EventMeasure.event_id == self.event.id)
        super(EventMeasureSelecter, self).__init__(query)

    def apply_filter(self, action_id=None, **flt):
        EventMeasure = self.model_provider.get_query('EventMeasure')
        ExpertSchemeMeasureAssoc = self.model_provider.get_query('ExpertSchemeMeasureAssoc')
        Measure = self.model_provider.get_query('Measure')
        rbMeasureType = self.model_provider.get_query('rbMeasureType')

        if 'id' in flt:
            self.query = self.query.filter(EventMeasure.id == flt['id'])
            return self
        if action_id:
            self.query = self.query.filter(EventMeasure.sourceAction_id == action_id)
        if 'measure_type_id_list' in flt:
            self.query = self.query.join(
                ExpertSchemeMeasureAssoc, Measure, rbMeasureType
            ).filter(rbMeasureType.id.in_(flt['measure_type_id_list']))
        if 'beg_date_from' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime >= safe_datetime(flt['beg_date_from']))
        if 'beg_date_to' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime <= safe_datetime(flt['beg_date_to']))
        if 'end_date_from' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime >= safe_datetime(flt['end_date_from']))
        if 'end_date_to' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime <= safe_datetime(flt['end_date_to']))
        if 'measure_status_id_list' in flt:
            self.query = self.query.filter(EventMeasure.status.in_(flt['measure_status_id_list']))
        return self

    def apply_sort_order(self, **order_options):
        EventMeasure = self.model_provider.get_query('EventMeasure')
        Action = self.model_provider.get_query('Action')

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
        # TODO: look at fetcher
        EventMeasure = self.model_provider.get('EventMeasure')
        ExpertSchemeMeasureAssoc = self.model_provider.get('ExpertSchemeMeasureAssoc')
        Measure = self.model_provider.get('Measure')
        rbMeasureType = self.model_provider.get('rbMeasureType')
        self.query = self.query.join(
            ExpertSchemeMeasureAssoc,
            Measure,
            rbMeasureType
        ).filter(
            EventMeasure.event_id == event_id,
            EventMeasure.deleted == 0,
        ).with_entities(
            EventMeasure.id
        ).add_columns(
            # todo: code in const
            func.sum(func.IF(rbMeasureType.code == 'lab_test', 1, 0)).label('count_lab_test'),
            func.sum(func.IF(and_(rbMeasureType.code == 'lab_test',
                                  EventMeasure.status.in_(em_final_status_list)
                                  ), 1, 0)).label('count_lab_test_completed'),
            func.sum(func.IF(rbMeasureType.code == 'func_test', 1, 0)).label('count_func_test'),
            func.sum(func.IF(and_(rbMeasureType.code == 'func_test',
                                  EventMeasure.status.in_(em_final_status_list)
                                  ), 1, 0)).label('count_func_test_completed'),
            func.sum(func.IF(rbMeasureType.code == 'checkup', 1, 0)).label('count_checkup'),
            func.sum(func.IF(and_(rbMeasureType.code == 'checkup',
                                  EventMeasure.status.in_(em_final_status_list)
                                  ), 1, 0)).label('count_checkup_completed'),
        )
