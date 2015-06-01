# -*- encoding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.event import Event
from nemesis.models.actions import Action
from nemesis.systemwide import db
from ...app import module
from blueprints.risar.lib.card_attrs import reevaluate_card_attrs
from ...lib.represent import represent_checkup
from blueprints.risar.lib.utils import get_action_by_id
from blueprints.risar.lib.expert.protocols import measure_manager_factory


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
            if code not in ('id', 'flatCode', 'person', 'beg_date', 'diag', 'diag2', 'diag3') and code in action.propsByCode:
                action.propsByCode[code].value = value
            elif code in ('diag', 'diag2', 'diag3') and value:
                property = action.propsByCode[code]
                property.value = value
        db.session.commit()
        reevaluate_card_attrs(event)
        db.session.commit()

        measure_mng = measure_manager_factory('generate', action)
        measure_mng.generate_measures()
    return represent_checkup(action, True)


@module.route('/api/0/measure/generate/', methods=['GET', 'POST'])
@module.route('/api/0/measure/generate/<int:action_id>', methods=['GET', 'POST'])
@api_method
def api_0_measure_generate(action_id):
    action = Action.query.get_or_404(action_id)
    measure_mng = measure_manager_factory('generate', action)
    measure_mng.generate_measures()
    return measure_mng.represent_measures()