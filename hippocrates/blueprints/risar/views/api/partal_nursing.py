# -*- coding: utf-8 -*-

import datetime

from flask import request
from blueprints.risar.lib.utils import close_open_partal_nursing, get_action_type_by_flatcode
from blueprints.risar.risar_config import nursing

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.partal_nursing import represent_partal_nursing, \
    represent_partal_nursing_list
from nemesis.lib.apiutils import api_method, ApiException

from nemesis.lib.utils import safe_int, safe_datetime
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.person import Person
from nemesis.systemwide import db


@module.route('/api/0/nursing/<flatcode>/', methods=['POST'])
@module.route('/api/0/nursing/<flatcode>/<int:action_id>', methods=['POST', 'GET'])
@api_method
def api_0_partal_nursing(flatcode, action_id=None):
    actionType = get_action_type_by_flatcode(flatcode)

    if flatcode not in nursing:
        raise ApiException(400, u'В патронажах нет такого flatCoda')

    actionType_id = actionType.id
    event_id = request.args.get('event_id', None)
    json = request.get_json()
    new_action = action_id is None
    if new_action:
        if event_id is None:
            raise ApiException(400, u'Event не определен')
        close_open_partal_nursing(event_id, flatcode)
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
            raise ApiException(404, u'Данный тип Action не похож на %s' % actionType.name)
        elif action.event_id != safe_int(event_id):
            raise ApiException(404, u'Запрашиваемый патронаж не относится к данной карте')

    if request.method == 'POST':
        for field in nursing.get(flatcode):
            action.propsByCode[field].value = json.get(field)

        db.session.add(action)
        db.session.commit()

    return represent_partal_nursing(action, flatcode)


@module.route('/api/0/nursing/<flatcode>_list/<int:event_id>', methods=['GET'])
@api_method
def api_0_partal_nursing_list(flatcode, event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    if flatcode == 'prepartal_all':
        # введён 'вирутуальный' flatcode, возвращаем все дородовые
        return {'prepartal_all_list': represent_partal_nursing_list(card, 'prepartal_nursing') +
                                 represent_partal_nursing_list(card, 'prepartal_nursing_repeat')}
    return {
        '{0}_list'.format(flatcode): represent_partal_nursing_list(card, flatcode),
    }


@module.route('/api/0/partal_nursing/delete/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_partal_nursing_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/partal_nursing/undelete/<int:action_id>', methods=['POST'])
@api_method
def api_0_partal_nursing_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'не найдено')
    action.deleted = 0
    db.session.commit()
    return True
