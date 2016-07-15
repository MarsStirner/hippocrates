# -*- encoding: utf-8 -*-
from hippocrates.blueprints.risar.lib.epicrisis_children import create_or_update_newborns
from flask import request

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.utils import get_action, get_action_by_id, close_open_checkups
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.systemwide import db
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent import represent_epicrisis, represent_chart_for_epicrisis
from hippocrates.blueprints.risar.risar_config import risar_epicrisis, risar_newborn_inspection


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
        create_or_update_newborns(action, newborn_inspections)

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