# -*- encoding: utf-8 -*-
from flask import request

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.utils import get_action, get_action_by_id, close_open_checkups
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.systemwide import db
from ...app import module
from ...lib.represent import represent_epicrisis, represent_chart_for_epicrisis
from ...risar_config import risar_epicrisis, risar_newborn_inspection


@module.route('/api/0/chart/<int:event_id>/epicrisis', methods=['GET', 'POST'])
@api_method
def api_0_chart_epicrisis(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    if not event:
        raise ApiException(404, 'Event not found')
    if request.method == 'GET':
        action = get_action(event, risar_epicrisis, True)
    else:
        data = request.get_json()
        action_id = data.pop('id', None)
        newborn_inspections = filter(None, data.pop('newborn_inspections', []))
        diagnoses = data.pop('diagnoses', [])
        action = get_action(event, risar_epicrisis, True)

        if not action.id:
            close_open_checkups(event_id)  # закрыть все незакрытые осмотры
        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value
        create_or_update_diagnoses(action, diagnoses)

        child_inspection_actions = []
        for child_inspection in newborn_inspections:
            child_id = child_inspection.pop('id', None)
            child_action = get_action_by_id(child_id, event,  risar_newborn_inspection, True)
            for code, value in child_inspection.iteritems():
                if code != 'sex' and code in child_action.propsByCode:
                    child_action.propsByCode[code].value = value
                elif code == 'sex' and value:
                    child_action.propsByCode['sex'].value = 1 if value['code'] == 'male' else 2
            db.session.add(child_action)
            db.session.commit()
            if not child_action.deleted:
                child_inspection_actions.append({'id': child_action.id})

        action.propsByCode['newborn_inspections'].value = child_inspection_actions
        db.session.commit()
        card.reevaluate_card_attrs()
        db.session.commit()
    return {
        'chart': represent_chart_for_epicrisis(event),
        'epicrisis': represent_epicrisis(event, action) if action else None
    }


@module.route('/api/0/epicrisis/newborn_inspection/')
@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>', methods=['DELETE'])
@api_method
def api_0_newborn_inspection_delete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        raise ApiException(404, 'inspection not found')
    if inspection.deleted:
        raise ApiException(400, 'inspection already deleted')
    inspection.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>/undelete', methods=['POST'])
@api_method
def api_0_newborn_inspection_undelete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        raise ApiException(404, 'Transfusion not found')
    if not inspection.deleted:
        raise ApiException(400, 'Transfusion not deleted')
    inspection.deleted = 0
    db.session.commit()
    return True