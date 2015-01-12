from flask import request

from ...app import module
from application.lib.utils import jsonify
from application.models.event import Event
from application.models.actions import Action
from application.systemwide import db
from ...lib.represent import get_action, represent_epicrisis, get_action_by_id, risar_newborn_inspection
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

        for child_inspection in request.json['newborn_inspections']:
            if child_inspection:
                child_action = get_action_by_id(child_inspection.get('id'), event,  risar_newborn_inspection, True)
                for code, value in child_inspection.iteritems():
                    if code not in ('id', ) and code in child_action.propsByCode:
                        child_action.propsByCode[code].value = value
                db.session.add(child_action)
        db.session.commit()
    return jsonify(represent_epicrisis(event, action))


@module.route('/api/0/epicrisis/newborn_inspection/')
@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>', methods=['DELETE'])
def api_0_newborn_inspection_delete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        return jsonify(None, 404, 'inspection not found')
    if inspection.deleted:
        return jsonify(None, 400, 'inspection already deleted')
    inspection.deleted = 1
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>/undelete', methods=['POST'])
def api_0_newborn_inspection_undelete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        return jsonify(None, 404, 'Transfusion not found')
    if not inspection.deleted:
        return jsonify(None, 400, 'Transfusion not deleted')
    inspection.deleted = 0
    db.session.commit()
    return jsonify(True)