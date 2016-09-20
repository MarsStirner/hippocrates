# -*- coding: utf-8 -*-

from hippocrates.blueprints.risar.lib.represent.common import represent_file_meta
from hippocrates.blueprints.risar.lib.expert.utils import can_edit_em_result
from nemesis.lib.utils import safe_dict
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.models.enums import ActionStatus


class EmResultRepr(object):

    def represent_em_result(self, action):
        aviz = ActionVisualizer()
        event_measure = action.em_result
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
            'ro': not can_edit_em_result(event_measure) if event_measure is not None else False,
            'layout': aviz.make_action_layout(action),
            'attached_files': [
                self.represent_action_file(action_attach)
                for action_attach in action.attach_files
            ]
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

    def represent_action_file(self, action_attach):
        res = safe_dict(action_attach)
        res.update({
            'file_meta': represent_file_meta(action_attach.file_meta)
        })
        return res
