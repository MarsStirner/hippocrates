# -*- coding: utf-8 -*-
from nemesis.lib.jsonify import ActionVisualizer

__author__ = 'plakrisenko'


class TTJVisualizer(object):
    def make_ttj_record(self, ttj):
        avis = ActionVisualizer()
        event = ttj.actions[0].event
        externalId = event.externalId if ttj.actions else None  # предполагается, что все actions из одного event
        return {
            'id': ttj.id,
            'externalId': externalId,
            'datetime': ttj.datetimeTaken,
            'client': ttj.client,
            'execPerson': ttj.execPerson,
            'tissueType': ttj.tissueType,
            'testTubeType': ttj.testTubeType,
            'amount': ttj.amount,
            'unit': ttj.unit,
            'status': ttj.status,
            'isUrgent': True if filter(lambda a: a.isUrgent, ttj.actions) else False,
            'actions': [avis.make_small_action_info(action) for action in ttj.actions],
            'set_persons': sorted({action.setPerson for action in ttj.actions if action.setPerson}),
            'org_str': event.current_org_structure if ttj.actions else None
        }
