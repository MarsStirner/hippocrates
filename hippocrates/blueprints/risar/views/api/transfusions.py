# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.utils import action_as_dict, get_action_type_id
from hippocrates.blueprints.risar.risar_config import transfusion_apt_codes, risar_anamnesis_transfusion
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


# Переливания


@module.route('/api/0/anamnesis/transfusions/')
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['GET'])
@api_method
def api_0_transfusions_get(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'Переливание не найдено')
    return dict(
        action_as_dict(action, transfusion_apt_codes),
        id=action_id
    )


@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_transfusions_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'Переливание не найдено')
    if action.deleted:
        raise ApiException(400, u'Переливание уже было удалено')
    action.deleted = 1
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/transfusions/<int:action_id>/undelete', methods=['POST'])
@api_method
def api_0_transfusions_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, u'Переливание не найдено')
    if not action.deleted:
        raise ApiException(400, u'Переливание не является удалённым')
    action.deleted = 0
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/transfusions/', methods=['POST'])
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['POST'])
@api_method
def api_0_transfusions_post(action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_transfusion)
    event_id = request.args.get('event_id', None)
    if action_id is None:
        if event_id is None:
            raise ApiException(400, u'Event не определен')
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id)
        if action is None:
            raise ApiException(404, u'Action не найден')
    json = request.get_json()
    for key in transfusion_apt_codes:
        action.propsByCode[key].value = json.get(key)
    db.session.add(action)
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return dict(
        action_as_dict(action, transfusion_apt_codes),
        id=action.id
    )