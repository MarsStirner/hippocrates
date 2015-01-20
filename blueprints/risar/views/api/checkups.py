# -*- encoding: utf-8 -*-
from flask import request

from application.lib.apiutils import api_method, ApiException
from application.lib.utils import safe_datetime
from application.models.event import Event
from application.systemwide import db
from ...app import module
from blueprints.risar.lib.card_attrs import reevaluate_card_attrs
from ...lib.represent import represent_checkup
from blueprints.risar.lib.utils import get_action_by_id


@module.route('/api/0/checkup/', methods=['GET', 'POST'])
@module.route('/api/0/checkup/<int:event_id>', methods=['GET', 'POST'])
@api_method
def api_0_checkup(event_id):
    event = Event.query.get(event_id)
    data = request.get_json()
    checkup_id = data.get('id')
    action = get_action_by_id(checkup_id, event, data['flat_code'], request.method != 'GET')
    if request.method == 'GET':
        if not action:
            raise ApiException(404, 'Action not found')
    else:
        action.begDate = safe_datetime(data['beg_date'])
        for code, value in data.iteritems():
            if code not in ('id', 'flatCode', 'person', 'beg_date') and code in action.propsByCode:
                action.propsByCode[code].value = value
        db.session.commit()
        reevaluate_card_attrs(event)
        db.session.commit()
    return represent_checkup(action)