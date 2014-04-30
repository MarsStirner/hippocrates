# -*- coding: utf-8 -*-
import datetime

from flask import request
from flask.ext.login import current_user

from application.models.actions import ActionType
from application.models.client import Client
from application.models.event import Event, EventType, EventType_Action, Diagnosis, Diagnostic
from application.systemwide import db
from application.lib.utils import (jsonify, safe_traverse, get_new_uuid,
                                   string_to_datetime, get_new_event_ext_id)
from blueprints.event.app import module
from application.models.exists import (Organisation, )
from application.lib.jsonify import EventVisualizer


@module.route('/api/event_info.json')
def api_event_info():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    vis = EventVisualizer()
    return jsonify({
        'event': vis.make_event(event),
        'diagnoses': vis.make_diagnoses(event),
    })


@module.route('/api/event_new.json', methods=['GET'])
def api_event_new_get():
    client_id = int(request.args['client_id'])
    event = Event()
    event.eventType = EventType.get_default_et()
    event.organisation = Organisation.query.filter_by(infisCode='500').first()
    event.client = Client.query.get(client_id)
    v = EventVisualizer()
    return jsonify(v.make_event(event))


@module.route('api/event_save.json', methods=['POST'])
def api_event_save():
    data = request.json
    now = datetime.datetime.now()
    event_id = data.get('id')
    if event_id:
        event = Event.query.get(event_id)
        event.modifyDatetime = now
        event.modifyPerson_id = current_user.get_id() or 1  # todo: fix
        event.deleted = data['deleted']
        event.eventType = EventType.query.get(data['event_type']['id'])
        event.execPerson_id = data['exec_person']['id']
        event.setDate = string_to_datetime(data['set_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        event.execDate = string_to_datetime(data['exec_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        # event.contract = None
        event.isPrimaryCode = data['is_primary']['id']
        event.order = data['order']['id']
        event.orgStructure_id = data['org_structure']['id']
        event.result_id = data['result']['id'] if data.get('result') else None
        event.rbAcheResult_id = data['ache_result']['id'] if data.get('ache_result') else None
        event.note = ''
    else:
        event = Event()
        event.createDatetime = event.modifyDatetime = now
        event.createPerson_id = event.modifyPerson_id = event.setPerson_id = current_user.get_id() or 1  # todo: fix
        event.deleted = 0
        event.version = 0
        event.eventType = EventType.query.get(data['event_type']['id'])
        event.client_id = data['client_id']
        event.execPerson_id = data['exec_person']['id']
        event.setDate = string_to_datetime(data['set_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        event.execDate = string_to_datetime(data['exec_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        # event.contract = None
        event.isPrimaryCode = data['is_primary']['id']
        event.order = data['order']['id']
        event.org_id = data['organisation']['id']
        event.orgStructure_id = data['org_structure']['id']
        event.note = ''
        event.payStatus = 0
        event.uuid = get_new_uuid()
    # todo: Event_Persons, Visit, ...
    db.session.add(event)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

    return jsonify(int(event))


@module.route('/api/events/diagnosis.json', methods=['POST'])
def api_diagnosis_save():
    current_datetime = datetime.datetime.now()
    data = request.json
    diagnosis_id = data.get('diagnosis_id')
    diagnostic_id = data.get('diagnostic_id')
    if diagnosis_id:
        diagnosis = Diagnosis.query.get(diagnosis_id)
    else:
        diagnosis = Diagnosis()
        diagnosis.createDatetime = current_datetime
    if diagnostic_id:
        diagnostic = Diagnostic.query.get(diagnostic_id)
    else:
        diagnostic = Diagnostic()
        diagnostic.createDatetime = current_datetime

    diagnosis.modifyDatetime = current_datetime
    diagnostic.modifyDatetime = current_datetime

    diagnosis.client_id = data['client_id']
    diagnosis.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnosis.character_id = safe_traverse(data, 'character', 'id')
    diagnosis.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnosis.traumaType_id = safe_traverse(data, 'trauma', 'id')
    diagnosis.MKB = safe_traverse(data, 'mkb', 'code') or ''
    diagnosis.MKBEx = safe_traverse(data, 'mkb_ex', 'code') or ''
    if not diagnosis.endDate:
        diagnosis.endDate = current_datetime
    db.session.add(diagnosis)

    diagnostic.event_id = data['event_id']
    diagnostic.diagnosis = diagnosis
    diagnostic.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnostic.character_id = safe_traverse(data, 'character', 'id')
    diagnostic.stage_id = safe_traverse(data, 'stage', 'id')
    diagnostic.phase_id = safe_traverse(data, 'phase', 'id')
    diagnostic.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnostic.traumaType_id = safe_traverse(data, 'trauma', 'id')
    diagnostic.healthGroup_id = safe_traverse(data, 'health_group', 'id')
    diagnostic.result_id = safe_traverse(data, 'result', 'id')
    diagnostic.notes = data.get('notes', '')
    diagnostic.rbAcheResult_id = safe_traverse(data, 'ache_result', 'id')
    if not diagnostic.setDate:
        diagnostic.setDate = current_datetime
    db.session.add(diagnostic)

    db.session.commit()
    return jsonify(None)


@module.route('/api/events/diagnosis.json', methods=['DELETE'])
def api_diagnosis_delete():
    data = request.json
    if data['diagnosis_id']:
        Diagnosis.query.filter(Diagnosis.id == data['diagnosis_id']).update({'deleted': 1})
    if data['diagnostic_id']:
        Diagnostic.query.filter(Diagnostic.id == data['diagnostic_id']).update({'deleted': 1})
    db.session.commit()


@module.route('/api/service/service_price.json', methods=['GET'])
def api_search_services():
    value = request.args['q']
    q = EventType_Action.query.join(ActionType).join(ActionType.service).filter(ActionType.name.like('%%%s%%' % value)).\
        filter(EventType_Action.eventType_id == 70).filter(ActionType.deleted == 0).all()

    def make_r(x):
        return {
            'at_code': x.actionType.code,
            'at_name': x.actionType.name,
            'service_name': x.actionType.service.name,
            'price': 0
        }
    return jsonify([make_r(res) for res in q])