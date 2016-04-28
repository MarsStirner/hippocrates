# -*- coding: utf-8 -*-

from nemesis.models.enums import MeasureStatus, EventMeasureActuality
from blueprints.risar.lib.expert.utils import can_edit_em_appointment, can_edit_em_result


class EventMeasureRepr(object):

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
            'source_action': measure.source_action and self.represent_source_action(measure.source_action),
            'appointment_action_id': measure.appointmentAction_id,
            'result_action_id': measure.resultAction_id,
            'is_actual': EventMeasureActuality(measure.is_actual),
            'scheme_measure': self.represent_scheme_measure(measure.scheme_measure),
            'hand_measure': self.represent_measure_rb(measure.hand_measure),
            'create_datetime': measure.createDatetime,
            'modify_datetime': measure.modifyDatetime,
            'create_person': measure.create_person,
            'modify_person': measure.modify_person
        }

    def _make_em_addtional_info(self, em):
        sm = em.scheme_measure
        if not sm:
            return None
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
        if not scheme_measure:
            return None
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
        if not measure:
            return None
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

    def represent_paginated_event_measures(self, paginated_data):
        return {
            'count': paginated_data.total,
            'total_pages': paginated_data.pages,
            'measures': [
                self.represent_em_full(event_measure) for event_measure in paginated_data.items
            ],
        }

    def represent_listed_event_measures(self, em_list):
        return [
            self.represent_em_full(event_measure) for event_measure in em_list
        ]

    def represent_listed_event_measures_in_action(self, em_list):
        return [
            self.represent_em_full(event_measure) for event_measure in em_list
        ]