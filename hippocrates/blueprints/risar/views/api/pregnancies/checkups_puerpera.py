# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.lib import sirius
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_puerpera
from hippocrates.blueprints.risar.lib.represent.common import represent_checkup_access
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups_puerpera, set_action_apt_values
from hippocrates.blueprints.risar.lib.diagnosis import validate_diagnoses
from hippocrates.blueprints.risar.risar_config import gynecological_ticket_25
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, db_non_flushable
from nemesis.models.event import Event
from nemesis.models.person import Person
from nemesis.systemwide import db


@module.route('/api/0/checkup_puerpera/', methods=['POST'])
@module.route('/api/0/checkup_puerpera/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup_puerpera(event_id):
    data = request.get_json()
    checkup_id = data.pop('id', None)
    flat_code = data.pop('flat_code', None)
    beg_date = safe_datetime(data.pop('beg_date', None))
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    diagnoses = data.pop('diagnoses', None)
    diagnoses_changed = data.pop('diagnoses_changed', None)
    if diagnoses_changed:
        validate_diagnoses(diagnoses)

    person_data = data.pop('person', None)
    if person_data:
        person = Person.query.get(person_data['id'])
    else:
        person = event.execPerson

    if not flat_code:
        raise ApiException(400, u'необходим flat_code')

    action = get_action_by_id(checkup_id, event, flat_code, True)

    if not checkup_id:
        close_open_checkups_puerpera(event_id)
    db.session.add(action)

    action.begDate = beg_date
    action.person = person

    ticket = action.get_prop_value('ticket_25') or get_action_by_id(None, event, gynecological_ticket_25, True)
    db.session.add(ticket)
    if not ticket.id:
        # Я в душе не знаю, как избежать нецелостности, и мне некогда думать
        db.session.commit()

    def set_ticket(prop, value):
        if value is None:
            value = {}
        set_action_apt_values(ticket, value)
        ticket.begDate = safe_datetime(value.get('beg_date'))
        ticket.endDate = safe_datetime(value.get('end_date'))
        ticket.person = person
        prop.set_value(ticket.id, True)

    with db.session.no_autoflush:
        set_action_apt_values(action, data, {'ticket_25': set_ticket})
        create_or_update_diagnoses(action, diagnoses)

    db.session.commit()

    em_ctrl = EventMeasureController()
    em_ctrl.regenerate(action)

    result = represent_pregnancy_checkup_puerpera(action)
    if em_ctrl.exception:
        result['em_error'] = u'Произошла ошибка формирования списка мероприятий'

    sirius.send_to_mis(
        sirius.RisarEvents.SAVE_CHECKUP_PUERPERA,
        sirius.RisarEntityCode.CHECKUP_PC_TICKET,
        sirius.OperationCode.READ_ONE,
        'risar.api_checkup_pc_ticket25_get',
        obj=('exam_obs_id', action.id),
        # obj=('external_id', action.id),
        params={'card_id': event_id},
        is_create=not checkup_id,
    )

    return {
        'checkup': result,
        'access': represent_checkup_access(action)
    }


@module.route('/api/0/checkup_puerpera/')
@module.route('/api/0/checkup_puerpera/<int:checkup_id>')
@api_method
def api_0_pregnancy_checkup_puerpera_get(checkup_id=None):
    action = get_action_by_id(checkup_id)
    if not action:
        raise ApiException(404, u'Action с id {0} не найден'.format(checkup_id))
    return {
        'checkup': represent_pregnancy_checkup_puerpera(action),
        'access': represent_checkup_access(action)
    }


@module.route('/api/0/checkup_puerpera/new/', methods=['POST'])
@module.route('/api/0/checkup_puerpera/new/<int:event_id>', methods=['POST'])
@db_non_flushable
@api_method
def api_0_pregnancy_checkup_puerpera_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, u'необходим flat_code')
    event = Event.query.get(event_id)
    action = get_action_by_id(None, event, flat_code, True)
    ta = get_action_by_id(None, event, gynecological_ticket_25, True)
    action.set_prop_value('ticket_25', ta)
    return {
        'checkup': represent_pregnancy_checkup_puerpera(action),
        'access': represent_checkup_access(action)
    }


@module.route('/api/0/checkup_puerpera_list/')
@module.route('/api/0/checkup_puerpera_list/<int:event_id>')
@api_method
def api_0_pregnancy_checkup_puerpera_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    def repr(checkup):
        return {
            'checkup': represent_pregnancy_checkup_puerpera(checkup),
            'access': represent_checkup_access(checkup)
        }
    return {
        'checkups': map(repr, card.checkups_puerpera)
    }
