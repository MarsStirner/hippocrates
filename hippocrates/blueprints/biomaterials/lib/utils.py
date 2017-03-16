# -*- coding: utf-8 -*-
from nemesis.lib.jsonify import ActionVisualizer

__author__ = 'plakrisenko'


class TTJVisualizer(object):
    def make_ttj_record(self, ttj, actions, actions_pay_data):
        """
        @type ttj: nemesis.models.actions.TakenTissueJournal
        @type actions: list|set
        @type events: list|set
        @param ttj:
        @param actions:
        @param events:
        @return:
        """
        avis = ActionVisualizer()
        externalId = ttj.event.externalId if ttj.event else None
        return {
            'id': ttj.id,
            'externalId': externalId,
            'datetime_planned': ttj.datetimePlanned,
            'datetime_taken': ttj.datetimeTaken,
            'client': ttj.event.client if ttj.event else None,
            'execPerson': ttj.execPerson,
            'tissueType': ttj.tissueType,
            'testTubeType': ttj.testTubeType,
            'amount': ttj.amount,
            'unit': ttj.unit,
            'status': ttj.status,
            'isUrgent': any(map(lambda a: a.isUrgent, actions)),
            'actions': [
                avis.make_small_action_info(action, actions_pay_data.get(action.id))
                for action in actions
            ],
            'set_persons': sorted({action.setPerson for action in actions if action.setPerson}),
            'org_str': ttj.event.current_org_structure if ttj.event else None
        }
