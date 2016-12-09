# -*- coding: utf-8 -*-

import datetime

from hippocrates.blueprints.risar.lib.utils import close_open_partal_nursing
from hippocrates.blueprints.risar.risar_config import nursing

from nemesis.lib.utils import safe_datetime
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.models.person import Person


class PartalNursingController(object):

    def __init__(self, flatcode, action_id=None):
        self.flatcode = flatcode
        self.action_id = action_id
        self.created = False

    def get(self, action_id=None):
        action_id = action_id or self.action_id
        return Action.query.get(self.action_id)

    def create_nursing(self, action_type, event, json_data):
        self.close_opened(event)
        action = create_action(action_type, event.id)
        person_data = json_data.pop('person', None)
        if person_data:
            person = Person.query.get(person_data['id'])
        else:
            person = event.execPerson
        action.begDate = safe_datetime(json_data.get('date', datetime.datetime.now()))
        action.person = person
        self.created = True
        return action

    def close_opened(self, event):
        close_open_partal_nursing(event.id, self.flatcode)

    @staticmethod
    def fill_own_fields(action, flatcode, json_data):
        action.update_action_integrity()
        for field in nursing.get(flatcode):
            action.propsByCode[field].value = json_data.get(field)

    @staticmethod
    def fill_anamnesis_fields(card, json_data):
        mother = json_data.get("mother_anamnesis", {})
        father = json_data.get('father_anamnesis', {})
        for field, value in mother.items():
            card.anamnesis.mother.propsByCode[field].value = value
        for field, value in father.items():
            card.anamnesis.father.propsByCode[field].value = value
