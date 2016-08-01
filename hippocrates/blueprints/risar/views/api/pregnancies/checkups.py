# -*- encoding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.fetus import create_or_update_fetuses
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_wm, represent_fetuses
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups, \
    copy_attrs_from_last_action
from hippocrates.blueprints.risar.lib.utils import notify_checkup_changes
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.systemwide import db


@module.route('/api/0/pregnancy/checkup/', methods=['POST'])
@module.route('/api/0/pregnancy/checkup/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup(event_id):
    data = request.get_json()
    checkup_id = data.pop('id', None)
    flat_code = data.pop('flat_code', None)
    beg_date = safe_datetime(data.pop('beg_date', None))
    person = data.pop('person', None)
    diagnoses = data.pop('diagnoses', [])
    fetuses = data.pop('fetuses', [])

    if not flat_code:
        raise ApiException(400, 'flat_code required')

    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    action = get_action_by_id(checkup_id, event, flat_code, True)

    notify_checkup_changes(card, action, data.get('pregnancy_continuation'))

    if not checkup_id:
        close_open_checkups(event_id)

    action.begDate = beg_date

    for code, value in data.iteritems():
        if code in action.propsByCode:
            action.propsByCode[code].value = value

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
    if not action:
        raise ApiException(404, 'Action with id {0} not found'.format(checkup_id))
    return represent_pregnancy_checkup_wm(action)


@module.route('/api/0/pregnancy/checkup/new/', methods=['POST'])
@module.route('/api/0/pregnancy/checkup/new/<int:event_id>', methods=['POST'])
@api_method
def api_0_pregnancy_checkup_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, 'flat_code required')
    event = Event.query.get(event_id)
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