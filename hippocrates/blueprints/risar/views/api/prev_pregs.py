# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import AbstractCard, PreviousPregnancy
from hippocrates.blueprints.risar.lib.prev_children import create_or_update_prev_children
from hippocrates.blueprints.risar.lib.represent.common import represent_pregnancy
from hippocrates.blueprints.risar.lib.utils import action_as_dict, get_action_type_id
from nemesis.lib.utils import bail_out
from hippocrates.blueprints.risar.risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy
from hippocrates.blueprints.risar.views.api.pregnancies.anamnesis import logger
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action
from nemesis.models.actions import Action
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


_base = '/api/0/any/<int:event_id>/anamnesis/pregnancies/'

# Беременности


@module.route(_base + '<int:action_id>', methods=['GET'])
@api_method
def api_0_pregnancies_get(event_id, action_id):
    action = Action.query.get(action_id) or bail_out(ApiException(404, u'Беременность не найдена'))
    return dict(
        action_as_dict(action, pregnancy_apt_codes),
        id=action_id
    )


@module.route(_base + '<int:action_id>', methods=['DELETE'])
@api_method
def api_0_pregnancies_delete(event_id, action_id):
    action = Action.query.get(action_id) or bail_out(ApiException(404, u'Беременность не найдена'))
    if action.deleted:
        raise ApiException(400, u'Беременность уже была удалена')
    action.deleted = 1
    db.session.commit()
    card = AbstractCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route(_base + '<int:action_id>/undelete', methods=['POST'])
@api_method
def api_0_pregnancies_undelete(event_id, action_id):
    action = Action.query.get(action_id) or bail_out(ApiException(404, u'Беременность не найдена'))
    if not action.deleted:
        raise ApiException(400, u'Беременность не является удалённой')
    action.deleted = 0
    db.session.commit()
    card = AbstractCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route(_base, methods=['POST'])
@module.route(_base + '<int:action_id>', methods=['POST'])
@api_method
def api_0_pregnancies_post(event_id, action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_pregnancy)
    if action_id is None:
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id) or bail_out(ApiException(404, u'Action не найден'))
        if action.event_id != event_id:
            raise ApiException(404, u'Action не найден')
    card = AbstractCard.get_for_event(action.event)
    json = request.get_json()

    newborn_inspections = json.pop('newborn_inspections', [])

    # prev pregnancy
    for code in pregnancy_apt_codes:
        action.set_prop_value(code, json.get(code))

    # prev pregnancy children
    new_children, deleted_children = create_or_update_prev_children(action, newborn_inspections)
    for dc in deleted_children:
        db.session.delete(dc)
    db.session.add(action)
    db.session.add_all(new_children)
    db.session.commit()

    card.reevaluate_card_attrs()
    db.session.commit()
    return represent_pregnancy(PreviousPregnancy(action))