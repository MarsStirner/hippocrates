# -*- coding: utf-8 -*-

from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import GynecologicCard
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.represent.common import represent_measures
from hippocrates.blueprints.risar.lib.represent.gyn import represent_gyn_checkup
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups, bail_out, \
    set_action_apt_values
from hippocrates.blueprints.risar.risar_config import gynecological_ticket_25
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.systemwide import db


__author__ = 'viruzzz-kun'


_base = '/api/0/gyn/<int:event_id>/checkups/'


@module.route(_base, methods=['POST'])
@api_method
def api_0_gyn_checkup(event_id):
    data = request.get_json()
    checkup_id = data.pop('id', None)
    flat_code = data.pop('flat_code', None)
    beg_date = safe_datetime(data.pop('beg_date', None))
    person = data.pop('person', None)
    diagnoses = data.pop('diagnoses', [])

    if not flat_code:
        raise ApiException(400, 'flat_code required')

    event = Event.query.get(event_id)
    card = GynecologicCard.get_for_event(event)
    action = get_action_by_id(checkup_id, event, flat_code, True)

    if not checkup_id:
        close_open_checkups(event_id)

    action.begDate = beg_date

    def set_ticket(prop, value):
        ticket = get_action_by_id(prop.value, event, gynecological_ticket_25, True)
        set_action_apt_values(ticket, value)
        ticket.begDate = value.get('beg_date')
        ticket.endDate = value.get('end_date')

    set_action_apt_values(action, data, {'ticket_25': set_ticket})

    create_or_update_diagnoses(action, diagnoses)

    db.session.commit()
    card.reevaluate_card_attrs()
    db.session.commit()

    em_ctrl = EventMeasureController()
    em_ctrl.regenerate(action)

    result = represent_gyn_checkup(action)
    result['measures'] = represent_measures(action)
    if em_ctrl.exception:
        result['em_error'] = u'Произошла ошибка формирования списка мероприятий'
    return result


@module.route(_base + '<int:checkup_id>', methods=['GET'])
@api_method
def api_0_gyn_checkup_get(event_id, checkup_id):
    action = get_action_by_id(checkup_id) or bail_out(ApiException(404, 'Action with id {0} not found'.format(checkup_id)))
    if action.event_id != event_id:
        raise ApiException(404, 'Action with id {0} does not belong to Event with id {1}'.format(checkup_id, event_id))
    return represent_gyn_checkup(action)


@module.route(_base + 'new/<flat_code>', methods=['GET'])
def api_0_gyn_checkup_get_new(event_id, flat_code):
    event = Event.query.get(event_id) or bail_out(ApiException(404, 'Event with id {0} not found'.format(event_id)))
    action = get_action_by_id(None, event, flat_code, True)
    result = represent_gyn_checkup(action)
    return result


@module.route(_base, methods=['GET'])
@api_method
def api_0_gyn_checkup_list(event_id):
    event = Event.query.get(event_id)
    card = GynecologicCard.get_for_event(event)
    return {
        'checkups': map(represent_gyn_checkup, card.checkups)
    }
