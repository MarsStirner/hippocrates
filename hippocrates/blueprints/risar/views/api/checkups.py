# -*- encoding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.card_attrs import reevaluate_card_attrs
from blueprints.risar.lib.represent import represent_checkup, represent_checkups
from blueprints.risar.lib.utils import get_action_by_id, close_open_checkups
from blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from blueprints.risar.lib.expert.em_generation import EventMeasureGenerator


@module.route('/api/0/checkup/', methods=['POST'])
@module.route('/api/0/checkup/<int:event_id>', methods=['POST'])
@api_method
def api_0_checkup(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, 'flat_code required')
    event = Event.query.get(event_id)
    checkup_id = data.get('id')
    action = get_action_by_id(checkup_id, event, flat_code, request.method != 'GET')
    if request.method == 'GET':
        if not action:
            raise ApiException(404, 'Action not found')
    else:
        # if not checkup_id:
        #     close_open_checkups(event_id)
        action.begDate = safe_datetime(data['beg_date'])
        for code, value in data.iteritems():
            if code not in ('id', 'flat_code', 'person', 'beg_date', 'diag', 'diag2', 'diag3') and code in action.propsByCode:
                action.propsByCode[code].value = value
            elif code in ('diag', 'diag2', 'diag3') and value:
                property = action.propsByCode[code]
                property.value = value
        db.session.commit()
        reevaluate_card_attrs(event)
        db.session.commit()

        # measure_mng = EventMeasureGenerator(action)
        # measure_mng.generate_measures()
    return represent_checkup(action)


@module.route('/api/0/checkup/')
@module.route('/api/0/checkup/<int:checkup_id>')
@api_method
def api_0_checkup_get(checkup_id=None):
    action = get_action_by_id(checkup_id)
    if not action:
        raise ApiException(404, 'Action with id {0} not found'.format(checkup_id))
    return represent_checkup(action)


@module.route('/api/0/checkup/new/', methods=['POST'])
@module.route('/api/0/checkup/new/<int:event_id>', methods=['POST'])
@api_method
def api_0_checkup_new(event_id):
    data = request.get_json()
    flat_code = data.get('flat_code')
    if not flat_code:
        raise ApiException(400, 'flat_code required')
    event = Event.query.get(event_id)
    action = get_action_by_id(None, event, flat_code, True)
    result = represent_checkup(action)
    result['pregnancy_week'] = get_pregnancy_week(event)
    return result


@module.route('/api/0/checkup_list/')
@module.route('/api/0/checkup_list/<int:event_id>')
@api_method
def api_0_checkup_list(event_id):
    event = Event.query.get(event_id)
    return {
        'checkups': represent_checkups(event)
    }
