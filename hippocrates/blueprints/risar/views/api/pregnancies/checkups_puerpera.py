# -*- encoding: utf-8 -*-

from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_puerpera
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups_puerpera, set_action_apt_values
from hippocrates.blueprints.risar.lib.diagnosis import validate_diagnoses
from hippocrates.blueprints.risar.risar_config import gynecological_ticket_25
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime
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
    diagnoses = data.pop('diagnoses', None)
    wizard_step = data.pop('wizard_step', None)
    if wizard_step == 'conclusion':
        validate_diagnoses(diagnoses)

    person_data = data.pop('person', None)
    if person_data:
        person = Person.query.get(person_data['id'])
    else:
        person = None

    if not flat_code:
        raise ApiException(400, u'необходим flat_code')

    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    action = get_action_by_id(checkup_id, event, flat_code, True)
    action.update_action_integrity()

    if not checkup_id:
        close_open_checkups_puerpera(event_id)
    db.session.add(action)

    action.begDate = beg_date
    action.person = person

    ticket = action.propsByCode['ticket_25'].value or get_action_by_id(None, event, gynecological_ticket_25, True)
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
    from hippocrates.blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
    reevaluate_card_fill_rate_all(card)
    db.session.commit()

    return represent_pregnancy_checkup_puerpera(action)


@module.route('/api/0/checkup_puerpera/')
@module.route('/api/0/checkup_puerpera/<int:checkup_id>')
@api_method
def api_0_pregnancy_checkup_puerpera_get(checkup_id=None):
    action = get_action_by_id(checkup_id)
    action.update_action_integrity()
    if not action:
        raise ApiException(404, u'Action с id {0} не найден'.format(checkup_id))
    return represent_pregnancy_checkup_puerpera(action)


@module.route('/api/0/checkup_puerpera/new/', methods=['POST'])
@module.route('/api/0/checkup_puerpera/new/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup_puerpera_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, u'необходим flat_code')
    event = Event.query.get(event_id)
    action = get_action_by_id(None, event, flat_code, True)
    result = represent_pregnancy_checkup_puerpera(action)
    return result


@module.route('/api/0/checkup_puerpera_list/')
@module.route('/api/0/checkup_puerpera_list/<int:event_id>')
@api_method
def api_0_pregnancy_checkup_puerpera_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    for action in card.checkups_puerpera:
        action.update_action_integrity()
    return {
        'checkups': map(represent_pregnancy_checkup_puerpera, card.checkups_puerpera)
    }
