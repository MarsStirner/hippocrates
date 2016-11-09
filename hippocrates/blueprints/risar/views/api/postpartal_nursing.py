# -*- coding: utf-8 -*-

import datetime

from flask import request
from blueprints.risar.lib.utils import get_action_type_id, close_open_postpartal_nursing
from blueprints.risar.risar_config import postpartal_nursing, postpartal_nursing_code

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.postpartal_nursing import represent_postpartal_nursing, \
    represent_postpartal_nursing_list
from nemesis.lib.apiutils import api_method, ApiException

from nemesis.lib.utils import safe_int, safe_datetime
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.person import Person
from nemesis.systemwide import db



@module.route('/api/0/postpartal_nursing/', methods=['POST'])
@module.route('/api/0/postpartal_nursing/<int:action_id>', methods=['POST', 'GET'])
@api_method
def api_0_postpartal_nursing(action_id=None):
    actionType_id = get_action_type_id(postpartal_nursing_code)
    event_id = request.args.get('event_id', None)
    json = request.get_json()
    new_action = action_id is None
    if new_action:
        if event_id is None:
            raise ApiException(400, u'Event не определен')
        close_open_postpartal_nursing(event_id)
        action = create_action(actionType_id, event_id)
        person_data = json.pop('person', None)
        if person_data:
            person = Person.query.get(person_data['id'])
        else:
            event = Event.query.get(event_id)
            person = event.execPerson
        action.begDate = safe_datetime(json.get('date', datetime.datetime.now()))
        action.person = person
    else:
        action = Action.query.get(action_id)
        if action is None:
            raise ApiException(404, u'Action не найден')
        elif action.actionType_id != actionType_id:
            raise ApiException(404, u'Данный тип Action не является послеродовым патронажем')
        elif action.event_id != safe_int(event_id):
            raise ApiException(404, u'Запрашиваемый послеродовой патронаж не относится к данной карте')

    if request.method == 'POST':
        for field in postpartal_nursing:
            action.propsByCode[field].value = json.get(field)

        db.session.add(action)
        db.session.commit()

    return represent_postpartal_nursing(action)


@module.route('/api/0/postpartal_nursing_list/<int:event_id>', methods=['GET'])
@api_method
def api_0_postpartal_nursing_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return {
        'postpartal_nursing_list': represent_postpartal_nursing_list(card),
    }


@module.route('/api/0/postpartal_nursing/delete/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_postpartal_nursing_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/postpartal_nursing/undelete/<int:action_id>', methods=['POST'])
@api_method
def api_0_postpartal_nursing_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 0
    db.session.commit()
    return True
