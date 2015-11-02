# -*- coding: utf-8 -*-

from sqlalchemy.orm import aliased

from nemesis.lib.utils import safe_int, safe_datetime, safe_bool
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (EventMeasure, ExpertSchemeMeasureAssoc, rbMeasureType, Measure)
from nemesis.models.enums import MeasureStatus, EventMeasureActuality
from blueprints.risar.lib.expert.utils import can_edit_em_appointment, can_edit_em_result


class EventMeasureSelecter(object):

    def __init__(self, event, action=None):
        self.event = event
        self.query = EventMeasure.query.filter(EventMeasure.event_id == self.event.id)

    def apply_filter(self, action_id=None, **flt):
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

    def get_all(self):
        return self.query.all()

    def paginate(self, per_page=20, page=1):
        return self.query.paginate(page, per_page, False)


class EventMeasureRepr(object):

    def represent_by_action(self, action):
        if not action.id:
            return []
        em_selecter = EventMeasureSelecter(action.event, action)
        # em_selecter.apply_filter(action_id=action.id)
        em_data = em_selecter.get_all()
        return [
            self.represent_em_full(event_measure) for event_measure in em_data
        ]

    def represent_by_event(self, event, query_filter=None):
        em_selecter = EventMeasureSelecter(event)
        if query_filter is not None:
            paginate = safe_bool(query_filter.get('paginate', True))
            per_page = safe_int(query_filter.get('per_page')) or 20
            page = safe_int(query_filter.get('page')) or 1
            em_selecter.apply_filter(**query_filter)
        else:
            paginate = True
            per_page = 20
            page = 1
        em_selecter.apply_sort_order()

        if paginate:
            return self._paginate_data(em_selecter, per_page, page)
        else:
            return self._list_data(em_selecter)

    def _paginate_data(self, selecter, per_page, page):
        em_data = selecter.paginate(per_page, page)
        return {
            'count': em_data.total,
            'total_pages': em_data.pages,
            'measures': [
                self.represent_event_measure(event_measure) for event_measure in em_data.items
            ]
        }

    def _list_data(self, selecter):
        em_data = selecter.get_all()
        return {
            'measures': [
                self.represent_event_measure(event_measure) for event_measure in em_data
            ]
        }

    def represent_em_full(self, em):
        em_data = self.represent_event_measure(em)
        return {
            'data': em_data,
            'access': {
                'can_edit_appointment': can_edit_em_appointment(em),
                'can_edit_result': can_edit_em_result(em),
                'can_cancel': False
            },
            'additional_info': self._make_em_addtional_info(em)
        }

    def represent_event_measure(self, measure):
        return {
            'id': measure.id,
            'event_id': measure.event_id,
            'beg_datetime': measure.begDateTime,
            'end_datetime': measure.endDateTime,
            'status': MeasureStatus(measure.status),
            'source_action': self.represent_source_action(measure.source_action),
            'appointment_action_id': measure.appointmentAction_id,
            'result_action_id': measure.resultAction_id,
            'is_actual': EventMeasureActuality(measure.is_actual),
            'scheme_measure': self.represent_scheme_measure(measure.scheme_measure),
            'create_datetime': measure.createDatetime,
            'modify_datetime': measure.modifyDatetime,
            'create_person': measure.create_person,
            'modify_person': measure.modify_person
        }

    def _make_em_addtional_info(self, em):
        sm = em.scheme_measure
        parts = []

        additional_text = sm.schedule.additionalText
        if additional_text:
            parts.append(additional_text)

        additional_mkbs = sm.schedule.additional_mkbs
        if additional_mkbs:
            text = u'Дополнительные диагнозы: {0}'.format(
                u', '.join([
                    u'<span tooltip="{0}"><span class="bottom_dotted">{1}</span></span>'.format(
                        mkb.DiagName, mkb.DiagID
                    )
                    for mkb in additional_mkbs
                ])
            )
            parts.append(text)
        return u'<br>'.join(parts)

    def represent_scheme_measure(self, scheme_measure):
        return {
            'scheme': self.represent_scheme(scheme_measure.scheme),
            'measure': self.represent_measure_rb(scheme_measure.measure)
        }

    def represent_scheme(self, scheme):
        return {
            'id': scheme.id,
            'code': scheme.code,
            'name': scheme.name,
            'number': scheme.number
        }

    def represent_measure_rb(self, measure):
        return {
            'id': measure.id,
            'code': measure.code,
            'name': measure.name,
            'measure_type': measure.measure_type
        }

    def represent_source_action(self, action):
        return {
            'id': action.id,
            'beg_date': action.begDate
        }