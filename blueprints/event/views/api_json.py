# -*- coding: utf-8 -*-

import datetime
from application.lib.agesex import recordAcceptableEx

from flask import request, abort
from flask.ext.login import current_user
from application.models.schedule import ScheduleClientTicket
from application.models.utils import safe_current_user_id

from config import ORGANISATION_INFIS_CODE
from application.models.actions import ActionType, Action
from application.models.client import Client
from application.models.enums import EventPrimary, EventOrder
from application.models.event import (Event, EventType, Diagnosis, Diagnostic, EventPayment, Visit,
                                      rbVisitType, rbScene, Event_Persons)
from application.models.exists import Person, OrgStructure
from application.systemwide import db
from application.lib.utils import (jsonify, safe_traverse, get_new_uuid, logger,
                                   string_to_datetime, get_new_event_ext_id)
from blueprints.event.app import module
from application.models.exists import (Organisation, )
from application.lib.jsonify import EventVisualizer, ClientVisualizer
from blueprints.event.lib.utils import (EventSaveException, get_local_contract,
    create_new_local_contract, create_services)
from application.lib.sphinx_search import SearchEventService
from application.lib.data import get_planned_end_datetime, int_get_atl_dict_all


@module.errorhandler(EventSaveException)
def handle_event_error(err):
    return jsonify({
        'name': err.message,
        'data': {
            'err_msg': err.data
        }
    }, 422, 'error')


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
        data['payment'] = vis.make_event_payment(event)
        data['services'] = vis.make_event_services(event_id)
    elif current_user.role_in('doctor'):
        data['diagnoses'] = vis.make_diagnoses(event)
    elif current_user.role_in(('rRegistartor', 'clinicRegistrator')):
        data['payment'] = vis.make_event_payment(event)
        data['services'] = vis.make_event_services(event_id)
    return jsonify(data)


@module.route('/api/event_new.json', methods=['GET'])
def api_event_new_get():
    event = Event()
    event.eventType = EventType.get_default_et()
    event.organisation = Organisation.query.filter_by(infisCode=str(ORGANISATION_INFIS_CODE)).first()
    event.isPrimaryCode = EventPrimary.primary[0]
    event.order = EventOrder.planned[0]

    ticket_id = request.args.get('ticket_id')
    if ticket_id:
        ticket = ScheduleClientTicket.query.get(int(ticket_id))
        client_id = ticket.client_id
        setDate = ticket.ticket.begDateTime
        note = ticket.note
        exec_person_id = ticket.ticket.schedule.person_id
    else:
        client_id = int(request.args['client_id'])
        setDate = datetime.datetime.now()
        note = ''
        exec_person_id = safe_current_user_id()
    event.execPerson_id = exec_person_id
    event.execPerson = Person.query.get(exec_person_id)
    event.orgStructure = event.execPerson.OrgStructure
    event.client = Client.query.get(client_id)
    event.setDate = setDate
    event.note = note
    db.session.add(event)
    v = EventVisualizer()
    return jsonify({
        'event': v.make_event(event),
        'payment': v.make_event_payment(None)
    })


@module.route('api/event_save.json', methods=['POST'])
def api_event_save():
    event_data = request.json['event']
    close_event = request.json['close_event']
    event_id = event_data.get('id')
    is_diagnostic = event_data['event_type']['request_type']['code'] == '4'
    if is_diagnostic:
        execPerson = None
    else:
        execPerson = Person.query.get(event_data['exec_person']['id'])
    err_msg = u'Ошибка сохранения данных обращения'
    if event_id:
        event = Event.query.get(event_id)
        event.deleted = event_data['deleted']
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        event.execPerson = execPerson
        event.setDate = string_to_datetime(event_data['set_date'])
        event.contract_id = event_data['contract']['id']
        event.isPrimaryCode = event_data['is_primary']['id']
        event.order = event_data['order']['id']
        event.orgStructure_id = event_data['org_structure']['id']
        event.result_id = event_data['result']['id'] if event_data.get('result') else None
        event.rbAcheResult_id = event_data['ache_result']['id'] if event_data.get('ache_result') else None
        event.note = event_data['note']
        db.session.add(event)
    else:
        event = Event()
        event.setPerson_id = current_user.get_id()
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        event.client_id = event_data['client_id']
        event.execPerson = execPerson
        event.setDate = string_to_datetime(event_data['set_date'])
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        event.contract_id = event_data['contract']['id']
        event.isPrimaryCode = event_data['is_primary']['id']
        event.order = event_data['order']['id']
        event.org_id = event_data['organisation']['id']
        event.orgStructure_id = event_data['org_structure']['id']
        event.payStatus = 0
        event.note = event_data['note']
        event.uuid = get_new_uuid()

        local_contract = safe_traverse(request.json, 'payment', 'local_contract')
        if event.payer_required:
            if not local_contract:
                raise EventSaveException(err_msg, u'Не заполнена информация о плательщике.')
            lcon = get_local_contract(local_contract)
            event.localContract = lcon
        db.session.add(event)

        if not is_diagnostic:
            visit = Visit.make_default(event)
            db.session.add(visit)
            executives = Event_Persons()
            executives.person = event.execPerson
            executives.event = event
            executives.begDate = event.setDate
            db.session.add(executives)

    if close_event:
        exec_date = event_data['exec_date']
        event.execDate = string_to_datetime(exec_date) if exec_date else datetime.datetime.now()

    try:
        db.session.commit()
    except EventSaveException:
        raise
    except Exception, e:
        logger.error(e, exc_info=True)
        db.session.rollback()
        return jsonify({'name': err_msg,
                        'data': {
                            'err_msg': 'INTERNAL SERVER ERROR'
                        }},
                       500, 'save event data error')
    else:
        services_data = request.json.get('services', [])
        cfinance_id = event_data['contract']['finance']['id']
        try:
            actions = create_services(event.id, services_data, cfinance_id)
            db.session.commit()
        except Exception, e:
            logger.error(e)
            db.session.rollback()
            raise EventSaveException(u'Ошибка создания услуг', u'%s Свяжитесь с администратором.' % e.message )

    if request.json.get('ticket_id'):
        ticket = ScheduleClientTicket.query.get(int(request.json['ticket_id']))
        ticket.event_id = int(event)
        db.session.commit()

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
    # result = find_services_direct(query, event_type_id, contract_id, speciality_id)

    ats_apts = int_get_atl_dict_all()
    client = Client.query.get(client_id)
    client_age = client.age_tuple(datetime.date.today())

    def make_response(service_data):
        at_id = service_data['action_type_id']
        at_data = ats_apts.get(at_id)
        if at_data:
            if not recordAcceptableEx(client.sexCode,
                                      client_age,
                                      at_data[6],
                                      at_data[5]):
                return None

        service = {
            'at_id': at_id,
            'at_code': service_data['code'],
            'at_name': service_data['name'],
            'service_name': service_data['service'],
            'price': service_data['price'],
            'is_lab': False
        }

        if at_data and at_data[9]:
            prop_types = at_data[9]
            prop_types = [prop_type[:2] for prop_type in prop_types if recordAcceptableEx(client.sexCode,
                                                                                          client_age,
                                                                                          prop_type[3],
                                                                                          prop_type[2])]
            if prop_types:
                service['is_lab'] = True
                service['assignable'] = prop_types
                service['all_assigned'] = map(lambda p: p[0], service['assignable'])
                service['all_planned_end_date'] = get_planned_end_datetime(at_id)
        return service

    matched = []
    for item in result['result']['items']:
        s = make_response(item)
        if s is not None:
            matched.append(s)

    return jsonify(matched)


def find_services_direct(query, event_type_id, contract_id, speciality_id):
    # for tests
    sql = u'''
SELECT  at.id as action_type_id, ct.code, ct.name as service, at.name, at.service_id,
	GROUP_CONCAT(DISTINCT e.eventType_id SEPARATOR ',') as eventType_id,
	IF(e.speciality_id, GROUP_CONCAT(DISTINCT e.speciality_id SEPARATOR ','), 0) as speciality_id,
	GROUP_CONCAT(DISTINCT ct.master_id SEPARATOR ',') as contract_id,
	ct.price
FROM ActionType at
INNER JOIN EventType_Action e ON e.actionType_id=at.id
INNER JOIN Contract_Tariff ct ON ct.service_id=at.service_id AND ct.eventType_id=e.eventType_id
INNER JOIN rbService s ON s.id=at.service_id
WHERE at.deleted=0 AND ct.deleted=0 AND (CURDATE() BETWEEN ct.begDate AND ct.endDate)
AND e.eventType_id {0} AND ct.master_id {1} AND speciality_id {2} AND at.code like '%{3}%'
GROUP BY at.id, ct.code
'''
    result = {
        'result': {
            'items': []
        }
    }
    sr = db.session.execute(
        db.text(
            sql.format(
                '= %s' % event_type_id if event_type_id else '!= -1',
                '= %s' % contract_id if contract_id else '!= -1',
                '!= %s' % speciality_id if speciality_id else '!= -1',
                '%s' % query
                )
        )
    )
    for r in sr:
        r = list(r)
        item = {}
        item['action_type_id'] = r[0]
        item['code'] = r[1]
        item['service'] = r[2]
        item['name'] = r[3]
        item['price'] = r[8]
        result['result']['items'].append(item)
    return result



@module.route('/api/event_payment/local_contract.json', methods=['GET'])
def api_new_event_payment_info_get():
    try:
        source = request.args['source']
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(400)

    event = client = None
    if source == 'prev_event':
        try:
            event_type_id = int(request.args['event_type_id'])
        except KeyError or ValueError:
            return abort(400)
        event = Event.query.join(EventType).filter(
            EventType.id == event_type_id,
            Event.client_id == client_id,
            Event.deleted == 0
        ).order_by(Event.setDate.desc()).first()
    elif source == 'client':
        client = Client.query.get(client_id)
    else:
        return abort(400)

    vis = EventVisualizer()
    res = vis.make_event_payment(event, client)
    return jsonify(res)


@module.route('/api/event_payment/make_payment.json', methods=['POST'])
def api_service_make_payment():
    # for tests
    pay_data = request.json
    event_id = pay_data['event_id']

    event = Event.query.get(event_id)

    payment = EventPayment()
    payment.master_id = event_id
    payment.date = datetime.date.today()
    payment.sum = pay_data['sum']
    payment.typePayment = 0
    payment.cashBox = ''
    payment.sumDiscount = 0
    payment.action_id = None
    payment.service_id = None

    event.payments.append(payment)
    db.session.add(event)
    db.session.commit()

    return jsonify(None)


@module.route('/api/event_payment/service_remove_coord.json', methods=['POST'])
def api_service_remove_coord():
    # not used
    data = request.json
    if data['action_id']:
        actions = Action.query.filter(Action.id.in_(data['action_id']))
        actions.update({Action.coordDate: None, Action.coordPerson_id: None},
                       synchronize_session=False)
        db.session.commit()

    return jsonify({
        'result': 'ok'
    })


@module.route('/api/event_payment/service_coordinate.json', methods=['POST'])
def api_service_coordinate():
    # not used
    data = request.json
    service = data['service']
    result = service['actions']
    if service['actions'] and service['coord_person_id']:
        actions = Action.query.filter(db.and_(Action.id.in_(service['actions']), Action.coordPerson_id==None))
        actions.update({Action.coordDate: datetime.datetime.now(), Action.coordPerson_id: service['coord_person_id']},
                       synchronize_session=False)
        db.session.commit()

    if len(service['actions']) < service['amount']:
        result.extend(create_services(data['event_id'], [service], data['finance_id']))

    return jsonify({
        'result': 'ok',
        'data': result
    })


@module.route('/api/event_payment/service_change_account.json', methods=['POST'])
def api_service_change_account():
    # not used
    data = request.json
    if data['actions']:
        actions = Action.query.filter(Action.id.in_(data['actions']))
        actions.update({Action.account: data['account']}, synchronize_session=False)
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


@module.route('api/delete_action.json', methods=['POST'])
def api_delete_action():
    action_id = request.json['action_id']
    if action_id:
        action = Action.query.filter(Action.id == action_id)
        action.update({Action.deleted: 1}, synchronize_session=False)
        db.session.commit()

    return jsonify({
        'result': 'ok'
    })


@module.route('/api/events.json', methods=["POST"])
def api_get_events():
    from application.models.event import Event
    from application.models.exists import Contract
    flt = request.get_json()
    base_query = Event.query.join(Client)
    context = EventVisualizer()
    if 'id' in flt:
        return jsonify({
            'pages': 1,
            'items': [context.make_short_event(base_query.filter(Event.id == flt['id']).first())]
        })
    if 'client_id' in flt:
        base_query = base_query.filter(Event.client_id == flt['client_id'])
    if 'exec_person_id' in flt:
        base_query = base_query.filter(Event.execPerson_id == flt['exec_person_id'])
    if 'beg_date' in flt:
        base_query = base_query.filter(Event.setDate >= datetime.datetime.strptime(flt['beg_date'], '%Y-%m-%d').date())
    if 'unfinished' in flt:
        base_query = base_query.filter(Event.execDate.is_(None))
    elif 'end_date' in flt:
        base_query = base_query.filter(Event.execDate <= datetime.datetime.strptime(flt['end_date'], '%Y-%m-%d').date())
    if 'request_type_id' in flt:
        base_query = base_query.join(EventType).filter(EventType.requestType_id == flt['request_type_id'])
    if 'finance_id' in flt:
        base_query = base_query.join(Contract).filter(Contract.finance_id == flt['finance_id'])
    per_page = int(flt.get('per_page', 20))
    page = int(flt.get('page', 1))
    base_query = base_query.order_by(Event.setDate)
    paginate = base_query.paginate(page, per_page, False)
    return jsonify({
        'pages': paginate.pages,
        'items': [
            context.make_short_event(event)
            for event in paginate.items
        ]
    })
