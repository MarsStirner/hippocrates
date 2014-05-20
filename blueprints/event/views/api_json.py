# -*- coding: utf-8 -*-
import datetime

from flask import request, abort
from flask.ext.login import current_user

from application.models.actions import ActionType, Action
from application.models.client import Client
from application.models.enums import EventPrimary, EventOrder
from application.models.event import (Event, EventType, EventType_Action, Diagnosis, Diagnostic, EventPayment)
from application.models.exists import Person, OrgStructure
from application.systemwide import db
from application.lib.utils import (jsonify, safe_traverse, get_new_uuid,
                                   string_to_datetime, get_new_event_ext_id)
from blueprints.event.app import module
from application.models.exists import (Organisation, )
from application.lib.jsonify import EventVisualizer, ClientVisualizer
from blueprints.event.lib.utils import get_local_contract, get_prev_event_payment, create_new_local_contract, \
    get_event_services, create_services
from application.lib.sphinx_search import SearchEventService
from application.lib.data import create_action


@module.route('/api/event_info.json')
def api_event_info():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    vis = EventVisualizer()
    data = {
        'event': vis.make_event(event),
    }
    if current_user.role_in('admin'):
        data['diagnoses'] = vis.make_diagnoses(event)
        data['payment'] = vis.make_event_payment(event.localContract, event_id)
        data['services'] = get_event_services(event_id)
    elif current_user.role_in('doctor'):
        data['diagnoses'] = vis.make_diagnoses(event)
    elif current_user.role_in(('rRegistartor', 'clinicRegistrator')):
        data['payment'] = vis.make_event_payment(event.localContract, event_id)
        data['services'] = get_event_services(event_id)
    return jsonify(data)


@module.route('/api/event_new.json', methods=['GET'])
def api_event_new_get():
    client_id = int(request.args['client_id'])
    event = Event()
    event.eventType = EventType.get_default_et()
    event.organisation = Organisation.query.filter_by(infisCode='500').first()
    event.isPrimaryCode = EventPrimary.primary[0]  # TODO: check previous events
    event.order = EventOrder.planned[0]
    event.client = Client.query.get(client_id)
    event.setDate = datetime.datetime.now()
    v = EventVisualizer()
    return jsonify({
        'event': v.make_event(event),
        'payment': v.make_event_payment(None)
    })


@module.route('api/event_save.json', methods=['POST'])
def api_event_save():
    now = datetime.datetime.now()
    event_data = request.json['event']
    event_id = event_data.get('id')
    if event_id:
        event = Event.query.get(event_id)
        event.modifyDatetime = now
        event.modifyPerson_id = current_user.get_id() or 1  # todo: fix
        event.deleted = event_data['deleted']
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        event.execPerson_id = event_data['exec_person']['id']
        event.setDate = string_to_datetime(event_data['set_date'])
        event.execDate = string_to_datetime(event_data['exec_date'])
        event.contract_id = event_data['contract']['id']
        event.isPrimaryCode = event_data['is_primary']['id']
        event.order = event_data['order']['id']
        event.orgStructure_id = event_data['org_structure']['id']
        event.result_id = event_data['result']['id'] if event_data.get('result') else None
        event.rbAcheResult_id = event_data['ache_result']['id'] if event_data.get('ache_result') else None
        event.note = ''
    else:
        event = Event()
        event.createDatetime = event.modifyDatetime = now
        event.createPerson_id = event.modifyPerson_id = event.setPerson_id = current_user.get_id() or 1  # todo: fix
        event.deleted = 0
        event.version = 0
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        event.client_id = event_data['client_id']
        event.execPerson_id = event_data['exec_person']['id']
        event.setDate = string_to_datetime(event_data['set_date'])
        event.execDate = string_to_datetime(event_data['exec_date'])
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        event.contract_id = event_data['contract']['id']
        event.isPrimaryCode = event_data['is_primary']['id']
        event.order = event_data['order']['id']
        event.org_id = event_data['organisation']['id']
        event.orgStructure_id = event_data['org_structure']['id']
        event.note = ''
        event.payStatus = 0
        event.uuid = get_new_uuid()
        # TODO: обязательность в зависимости от типа события?
        payment_data = request.json['payment']
        if payment_data:
            lcon = get_local_contract(payment_data['local_contract'])
            event.localContract = lcon

    # todo: Event_Persons, Visit, ...
    db.session.add(event)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise
    else:
        services_data = request.json.get('services', [])
        cfinance_id = event_data['contract']['finance']['id']
        create_services(event.id, services_data, cfinance_id)

    return jsonify({
        'id': int(event)
    })


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
    diagnosis.person_id = data['person']['id']
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
    diagnostic.sanatorium = 0
    diagnostic.hospital = 0
    diagnostic.speciality_id = 1
    diagnostic.version = 0
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
    query = request.args['q']
    client_id = request.args['client_id']
    event_type_id = request.args.get('event_type_id')
    contract_id = request.args.get('contract_id')
    person_id = request.args.get('person_id')
    speciality_id = None
    if person_id:
        doctor = Person.query.get(int(person_id))
        speciality_id = doctor.speciality_id
    result = SearchEventService.search(query,
                                       eventType_id=event_type_id,
                                       contract_id=contract_id,
                                       speciality_id=speciality_id)

    def make_response(_item):
        return {
            'at_id': _item['id'],
            'at_code': _item['code'],
            'at_name': _item['name'],
            'service_name': _item['service'],
            'price': _item['price']
        }
    return jsonify([make_response(item) for item in result['result']['items']])


@module.route('/api/event_payment/local_contract.json', methods=['GET'])
def api_new_event_payment_info_get():
    try:
        source = request.args['source']
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(400)

    if source == 'prev_event':
        try:
            event_type_id = int(request.args['event_type_id'])
        except KeyError or ValueError:
            return abort(400)
        event = get_prev_event_payment(client_id, event_type_id)
        lcon = event.localContract
    elif source == 'client':
        client = Client.query.get(client_id)
        cvis = ClientVisualizer()
        lc_info = cvis.make_payer_for_lc(client)
        lcon = create_new_local_contract(lc_info)
    else:
        return abort(400)

    vis = EventVisualizer()
    res = vis.make_event_payment(lcon)
    return jsonify(res)


@module.route('/api/event_payment/make_payment.json', methods=['POST'])
def api_service_make_payment():
    # for tests
    pay_data = request.json
    event_id = pay_data['event_id']

    event = Event.query.get(event_id)

    payment = EventPayment()
    payment.createDatetime = payment.modifyDatetime = datetime.datetime.now()
    payment.deleted = 0
    payment.master_id = event_id
    payment.date = datetime.date.today()
    payment.sum = pay_data['sum']
    payment.typePayment = 0
    payment.cashBox = ''
    payment.sumDiscount = 0
    payment.action_id = pay_data['action_id']
    payment.service_id = pay_data['service_id']

    event.localContract.payments.append(payment)
    db.session.add(event)
    db.session.commit()

    return jsonify({
        'result': 'ok'
    })


@module.route('/api/event_payment/delete_service.json', methods=['POST'])
def api_service_delete_service():
    # TODO: validations
    action_ids = request.json['action_id_list']
    if action_ids:
        actions = Action.query.filter(Action.id.in_(action_ids))
        actions.update({Action.deleted: 1},
                       synchronize_session=False)
        db.session.commit()

    return jsonify({
        'result': 'ok'
    })