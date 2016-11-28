# -*- coding: utf-8 -*-

import datetime

from flask import request
from hippocrates.blueprints.risar.lib.utils import get_action_type_by_flatcode
from hippocrates.blueprints.risar.risar_config import nursing

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.partal_nursing import represent_partal_nursing_list, \
    represent_partal_nursing_with_anamnesis
from nemesis.lib.apiutils import api_method, ApiException

from nemesis.lib.utils import safe_int
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.systemwide import db
from hippocrates.blueprints.risar.lib.partal_nursing import PartalNursingController


@module.route('/api/0/nursing/<flatcode>/', methods=['POST'])
@module.route('/api/0/nursing/<flatcode>/<int:action_id>', methods=['POST', 'GET'])
@api_method
def api_0_partal_nursing(flatcode, action_id=None):
    if flatcode not in nursing:
        raise ApiException(400, u'В патронажах нет такого flatCoda')

    actionType = get_action_type_by_flatcode(flatcode)
    event_id = request.args.get('event_id', None)
    if event_id is None:
        raise ApiException(400, u'Event не определен')
    event = Event.query.get(event_id)
    jsn = request.get_json()
    pp_nursing = jsn.get('pp_nursing', {}) if jsn else {}
    card = PregnancyCard.get_for_event(event)
    pp = PartalNursingController(flatcode, action_id)
    new_action = action_id is None
    if new_action:
        action = pp.create_nursing(actionType.id, event, pp_nursing)
    else:
        action = pp.get(action_id)
        if action is None:
            raise ApiException(404, u'Action не найден')
        elif action.actionType_id != actionType.id:
            raise ApiException(404, u'Данный тип Action не похож на %s' % actionType.name)
        elif action.event_id != safe_int(event_id):
            raise ApiException(404, u'Запрашиваемый патронаж не относится к данной карте')

    if request.method == 'POST':
        pp.fill_own_fields(action, flatcode, json_data=pp_nursing)
        if flatcode == "prepartal_nursing":
            pp.fill_anamnesis_fields(card, json_data=jsn)

        db.session.add(action)
        db.session.commit()
    return represent_partal_nursing_with_anamnesis(action, flatcode, card)


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
