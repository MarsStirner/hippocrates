# -*- encoding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_checkup_puerpera
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups_puerpera
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.systemwide import db


@module.route('/api/0/checkup_puerpera/', methods=['POST'])
@module.route('/api/0/checkup_puerpera/<int:event_id>', methods=['POST'])
@api_method
def api_0_checkup_puerpera(event_id):
    data = request.get_json()
    checkup_id = data.pop('id', None)
    flat_code = data.pop('flat_code', None)
    beg_date = safe_datetime(data.pop('beg_date', None))
    diagnoses = data.pop('diagnoses', None)

    if not flat_code:
        raise ApiException(400, 'flat_code required')

    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    action = get_action_by_id(checkup_id, event, flat_code, True)

    if not checkup_id:
        close_open_checkups_puerpera(event_id)
    db.session.add(action)

    action.begDate = beg_date

    for code, value in data.iteritems():
        if code in action.propsByCode:
            action.propsByCode[code].value = value

    create_or_update_diagnoses(action, diagnoses)

    db.session.commit()
    from hippocrates.blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
    reevaluate_card_fill_rate_all(card)
    db.session.commit()

    return represent_checkup_puerpera(action)


@module.route('/api/0/checkup_puerpera/')
@module.route('/api/0/checkup_puerpera/<int:checkup_id>')
@api_method
def api_0_checkup_puerpera_get(checkup_id=None):
    action = get_action_by_id(checkup_id)
    if not action:
        raise ApiException(404, 'Action with id {0} not found'.format(checkup_id))
    return represent_checkup_puerpera(action)


@module.route('/api/0/checkup_puerpera/new/', methods=['POST'])
@module.route('/api/0/checkup_puerpera/new/<int:event_id>', methods=['POST'])
@api_method
def api_0_checkup_puerpera_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, 'flat_code required')
    event = Event.query.get(event_id)
    action = get_action_by_id(None, event, flat_code, True)
    result = represent_checkup_puerpera(action)
    return result


@module.route('/api/0/checkup_puerpera_list/')
@module.route('/api/0/checkup_puerpera_list/<int:event_id>')
@api_method
def api_0_checkup_puerpera_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return {
        'checkups': map(represent_checkup_puerpera, card.checkups_puerpera)
    }
