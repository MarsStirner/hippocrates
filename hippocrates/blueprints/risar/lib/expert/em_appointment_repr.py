# -*- coding: utf-8 -*-

from nemesis.lib.utils import safe_unicode
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.models.enums import ActionStatus


class EmAppointmentRepr(object):

    def represent_appointment(self, action):
        aviz = ActionVisualizer()
        return {
            'id': action.id,
            'action_type': self.represent_action_type(action.actionType),
            'event_id': action.event_id,
            'client_id': action.event.client_id,
            'direction_date': action.directionDate,
            'beg_date': action.begDate,
            'end_date': action.endDate,
            'planned_end_date': action.plannedEndDate,
            'status': ActionStatus(action.status),
            'set_person': action.setPerson,
            'person': action.person,
            'note': action.note,
            'office': action.office,
            'amount': action.amount,
            'uet': action.uet,
            'pay_status': action.payStatus,
            'account': action.account,
            'is_urgent': action.isUrgent,
            'coord_date': action.coordDate,
            'properties': [
                aviz.make_property(prop)
                for prop in action.properties
            ],
            'ro': False,
            'layout': aviz.make_action_layout(action),
        }

    def represent_action_type(self, action_type):
        return {
            'id': action_type.id,
            'name': action_type.name,
            'code': action_type.code,
            'flat_code': action_type.flatCode,
            'class': action_type.class_,
            'context_name': action_type.context
        }