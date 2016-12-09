# -*- coding: utf-8 -*-

import datetime

from flask import request, make_response
from hippocrates.blueprints.risar.lib.utils import get_action_type_id
from hippocrates.blueprints.risar.risar_config import soc_prof_codes

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.soc_prof_help import represent_soc_prof_help, represent_soc_prof_item
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_int, safe_datetime
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.person import Person
from nemesis.systemwide import db


@module.route('/api/0/soc_prof_help/<flat_code>/', methods=['POST'])
@module.route('/api/0/soc_prof_help/<flat_code>/<int:action_id>', methods=['POST'])
@api_method
def api_0_soc_prof_post(flat_code, action_id=None):

    if flat_code not in soc_prof_codes:
        return ApiException(u'нет такого flat_coda %s' % flat_code)

    actionType_id = get_action_type_id(flat_code)
    event_id = request.args.get('event_id', None)
    json = request.get_json()

    if action_id is None:
        if event_id is None:
            raise ApiException(400, u'Event не определен')
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

    fields = soc_prof_codes[flat_code]
    for key in fields:
        action.propsByCode[key].value = json.get(key)

    db.session.add(action)
    db.session.commit()

    return represent_soc_prof_item(action, fields)


@module.route('/api/0/soc_prof_help/<int:event_id>', methods=['GET'])
@api_method
def api_0_soc_prof_help_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return {
        'soc_prof_help': represent_soc_prof_help(card),
    }

@module.route('/api/0/soc_prof_help/delete/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_soc_prof_help_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 1
    db.session.commit()
    return True

@module.route('/api/0/soc_prof_help/undelete/<int:action_id>', methods=['POST'])
@api_method
def api_0_soc_prof_help_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 0
    db.session.commit()
    return True