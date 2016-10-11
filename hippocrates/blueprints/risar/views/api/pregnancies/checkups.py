# -*- encoding: utf-8 -*-

from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.fetus import create_or_update_fetuses, calc_fisher_ktg_info
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_wm, represent_fetuses
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups, \
    copy_attrs_from_last_action, set_action_apt_values
from hippocrates.blueprints.risar.lib.utils import notify_checkup_changes
from hippocrates.blueprints.risar.lib.diagnosis import validate_diagnoses
from hippocrates.blueprints.risar.risar_config import gynecological_ticket_25
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.models.person import Person
from nemesis.systemwide import db


@module.route('/api/0/pregnancy/checkup/', methods=['POST'])
@module.route('/api/0/pregnancy/checkup/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup(event_id):
    data = request.get_json()
    checkup_id = data.pop('id', None)
    flat_code = data.pop('flat_code', None)
    beg_date = safe_datetime(data.pop('beg_date', None))
    person_data = data.pop('person', None)
    diagnoses_changed = data.pop('diagnoses_changed', None)
    if person_data:
        person = Person.query.get(person_data['id'])
    else:
        person = None
    diagnoses = data.pop('diagnoses', [])
    if diagnoses_changed:
        validate_diagnoses(diagnoses)
    fetuses = data.pop('fetuses', [])

    if not flat_code:
        raise ApiException(400, u'необходим flat_code')

    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    action = get_action_by_id(checkup_id, event, flat_code, True)
    action.update_action_integrity()

    notify_checkup_changes(card, action, data.get('pregnancy_continuation'))

    if not checkup_id:
        close_open_checkups(event_id)

    action.begDate = beg_date
    action.person = person

    ticket = action.propsByCode['ticket_25'].value or get_action_by_id(None, event, gynecological_ticket_25, True)
    db.session.add(ticket)
    if not ticket.id:
        # Я в душе не знаю, как избежать нецелостности, и мне некогда думать
        db.session.commit()

    def set_ticket(prop, value):
        set_action_apt_values(ticket, value)
        ticket.begDate = safe_datetime(value.get('beg_date'))
        ticket.endDate = safe_datetime(value.get('end_date'))
        ticket.person = person
        prop.set_value(ticket.id, True)

    with db.session.no_autoflush:
        set_action_apt_values(action, data, {'ticket_25': set_ticket})
        create_or_update_diagnoses(action, diagnoses)
        create_or_update_fetuses(action, fetuses)

    db.session.commit()
    card.reevaluate_card_attrs()
    db.session.commit()

    em_ctrl = EventMeasureController()
    em_ctrl.regenerate(action)

    result = represent_pregnancy_checkup_wm(action)
    if em_ctrl.exception:
        result['em_error'] = u'Произошла ошибка формирования списка мероприятий'
    return result


@module.route('/api/0/pregnancy/checkup/')
@module.route('/api/0/pregnancy/checkup/<int:checkup_id>')
@api_method
def api_0_pregnancy_checkup_get(checkup_id=None):
    action = get_action_by_id(checkup_id)
    action.update_action_integrity()
    if not action:
        raise ApiException(404, u'Action c id {0} не найден'.format(checkup_id))
    return represent_pregnancy_checkup_wm(action)


@module.route('/api/0/pregnancy/checkup/new/', methods=['POST'])
@module.route('/api/0/pregnancy/checkup/new/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, u'необходим flat_code')
    event = Event.query.get(event_id)

    with db.session.no_autoflush:
        action = get_action_by_id(None, event, flat_code, True)
        copy_attrs_from_last_action(event, flat_code, action, (
            'fetus_first_movement_date',
        ))
        result = represent_pregnancy_checkup_wm(action)
        result['pregnancy_week'] = get_pregnancy_week(event)
    return result


@module.route('/api/0/pregnancy/checkup_list/')
@module.route('/api/0/pregnancy/checkup_list/<int:event_id>')
@api_method
def api_0_pregnancy_checkup_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    for action in card.checkups:
        action.update_action_integrity()
    return {
        'checkups': map(represent_pregnancy_checkup_wm, card.checkups)
    }


@module.route('/api/0/pregnancy/fetus_list/')
@module.route('/api/0/pregnancy/fetus_list/<int:event_id>')
@api_method
def api_0_fetus_list(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return represent_fetuses(card)


@module.route('/api/0/fetus/calc_fisher_ktg/', methods=['POST'])
@api_method
def api_0_fetus_calc_fisher_ktg():
    data = request.get_json()
    points, rate = calc_fisher_ktg_info(data)
    return {
        'points': points,
        'fisher_ktg_rate': rate
    }
