# -*- coding: utf-8 -*-

__author__ = 'plakrisenko'
from nemesis.lib.jsonify import ActionVisualizer


class TTJVisualizer(object):
    def make_ttj_record(self, ttj):
        avis = ActionVisualizer()
        externalId = ttj.actions[0].event.externalId if ttj.actions else None  # предполагается, что все actions из одного event
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
            'set_persons': self.get_set_persons(ttj.actions)
        }

    def get_set_persons(self, actions):
        set_persons = []
        for action in actions:
            if action.person not in set_persons:
                set_persons.append(action.person)
        return set_persons
