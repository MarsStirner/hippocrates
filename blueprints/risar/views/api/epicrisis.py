from flask import request

from ...app import module
from application.lib.utils import jsonify
from application.models.event import Event
from application.systemwide import db
from ...lib.represent import get_action, represent_epicrisis
from ...risar_config import risar_epicrisis


@module.route('/api/0/chart/<int:event_id>/epicrisis', methods=['GET', 'POST'])
def api_0_chart_epicrisis(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify(None, 404, 'Event not found')
    if request.method == 'GET':
        action = get_action(event, risar_epicrisis)
        if not action:
            return jsonify(None, 404, 'Action not found')
    else:
        action = get_action(event, risar_epicrisis, True)
        for code, value in request.get_json().iteritems():
            if code not in ('id', 'newborn_inspections', ) and code in action.propsByCode:
                action.propsByCode[code].value = value
        db.session.commit()
    return jsonify(represent_epicrisis(event, action))