# -*- coding: utf-8 -*-
from nemesis.lib.jsonify import ActionVisualizer

__author__ = 'plakrisenko'


class TTJVisualizer(object):
    def make_ttj_record(self, ttj, actions, events):
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
        events = list(events)
        event = events[0] if events else None
        externalId = event.externalId if event else None  # предполагается, что все actions из одного event
        return {
            'id': ttj.id,
            'externalId': externalId,
            'datetime_planned': ttj.datetimePlanned,
            'datetime_taken': ttj.datetimeTaken,
            'client': ttj.client,
            'execPerson': ttj.execPerson,
            'tissueType': ttj.tissueType,
            'testTubeType': ttj.testTubeType,
            'amount': ttj.amount,
            'unit': ttj.unit,
            'status': ttj.status,
            'isUrgent': any(map(lambda a: a.isUrgent, actions)),
            'actions': map(avis.make_small_action_info, actions),
            'set_persons': sorted({action.setPerson for action in actions if action.setPerson}),
            'org_str': event.current_org_structure if event else None
        }
