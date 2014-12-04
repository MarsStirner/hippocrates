# -*- coding: utf-8 -*-

import datetime

from flask import request, abort
from sqlalchemy import desc

from config import ORGANISATION_INFIS_CODE
from application.models.actions import Action
from application.models.client import Client
from application.models.enums import EventPrimary, EventOrder
from application.models.event import (Event, EventType, Diagnosis, Diagnostic, EventPayment, Visit)
from application.models.exists import Person, rbRequestType, rbResult, Contract
from application.systemwide import db
from application.lib.utils import (jsonify, safe_traverse, logger, safe_datetime, get_utc_datetime_with_tz)
from application.models.schedule import ScheduleClientTicket
from application.models.utils import safe_current_user_id
from application.models.exists import (Organisation, )
from application.lib.jsonify import EventVisualizer
from blueprints.event.app import module
from blueprints.event.lib.utils import (EventSaveException, create_services, save_event, save_executives)
from application.lib.sphinx_search import SearchEventService
from application.lib.data import get_planned_end_datetime, int_get_atl_dict_all, delete_action
from application.lib.agesex import recordAcceptableEx
from application.lib.const import STATIONARY_EVENT_CODES
from application.lib.user import UserUtils


@module.errorhandler(EventSaveException)
def handle_event_error(err):
    base_msg = u'Ошибка сохранения данных обращения'
    code = err.data and err.data.get('code') or 500
    msg = err.message or base_msg
    ext_msg = err.data and err.data.get('ext_msg') or ''
    if ext_msg:
        msg = u'%s: %s' % (msg, ext_msg)
    return jsonify(None, code, msg)


@module.route('/api/event_info.json')
def api_event_info():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    vis = EventVisualizer()
    return jsonify(vis.make_event_info_for_current_role(event))


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
    if not event.is_diagnostic:
        event.execPerson_id = exec_person_id
        event.execPerson = Person.query.get(exec_person_id)
        event.orgStructure = event.execPerson.org_structure
    event.client = Client.query.get(client_id)
    event.setDate = setDate
    event.note = note
    v = EventVisualizer()
    return jsonify({
        'event': v.make_event(event),
        'payment': v.make_event_payment(None)
    })


@module.route('/api/event/event_stationary_open.json', methods=['GET'])
def api_event_stationary_open_get():
    client_id = int(request.args['client_id'])
    events = Event.query.join(EventType, rbRequestType).filter(
        Event.client_id == client_id,
        Event.execDate.is_(None),
        Event.deleted == 0,
        rbRequestType.code.in_(STATIONARY_EVENT_CODES)
    ).order_by(Event.setDate.desc())
    v = EventVisualizer()
    return jsonify([v.make_short_event(event) for event in events])


@module.route('api/event_save.json', methods=['POST'])
def api_event_save():
    all_data = request.json
    event_data = all_data.get('event')
    event_id = event_data.get('id')

    try:
        result = save_event(event_id, all_data)
    except EventSaveException:
        raise
    except Exception, e:
        logger.error(e, exc_info=True)
        raise EventSaveException()

    return jsonify(result)


@module.route('api/event_close.json', methods=['POST'])
def api_event_close():
    all_data = request.json
    event_data = all_data['event']
    event_id = event_data['id']
    event = Event.query.get(event_id)

    error_msg = {}
    if not UserUtils.can_close_event(event, error_msg):
        return jsonify(None, 403, u'Невозможно закрыть обращение: %s.' % error_msg['message'])

    if not event_data['exec_date']:
        event_data['exec_date'] = get_utc_datetime_with_tz().isoformat()
    try:
        save_event(event_id, all_data)
        save_executives(event_id)
    except EventSaveException:
        raise
    except Exception, e:
        logger.error(e, exc_info=True)
        raise EventSaveException()
    return jsonify(None, result_name=u'Обращение закрыто')


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


@module.route('/api/events/diagnosis', methods=['GET'])
def api_diagnosis_get():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    vis = EventVisualizer()
    return jsonify(vis.make_diagnoses(event))


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


@module.route('/api/event_payment/previous_local_contracts.json', methods=['GET'])
def api_prev_event_payment_info_get():
    try:
        client_id = int(request.args['client_id'])
        finance_id = int(request.args.get('finance_id'))
        event_set_date = safe_datetime(request.args.get('set_date'))
        if event_set_date is None:
            event_set_date = datetime.datetime.now()
    except (KeyError, ValueError, TypeError):
        return abort(400)
    request_type_codes = ['policlinic', '4']

    event_list = Event.query.join(EventType, rbRequestType).filter(
        rbRequestType.code.in_(request_type_codes),
        EventType.finance_id == finance_id,
        Event.client_id == client_id,
        Event.deleted == 0,
        Event.setDate < event_set_date
    ).order_by(Event.setDate.desc())

    vis = EventVisualizer()
    res = vis.make_prev_events_contracts(event_list)
    return jsonify(res)


@module.route('/api/event_payment/client_local_contract.json', methods=['GET'])
def api_client_payment_info_get():
    try:
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(400)

    client = Client.query.get(client_id)
    vis = EventVisualizer()
    res = vis.make_event_payment(None, client)
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

    return jsonify(None)


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

    return jsonify(None)


@module.route('/api/event_payment/delete_service.json', methods=['POST'])
def api_service_delete_service():
    # TODO: validations
    action_ids = request.json['action_id_list']
    if action_ids:
        actions = Action.query.filter(Action.id.in_(action_ids))
        actions.update({Action.deleted: 1},
                       synchronize_session=False)
        db.session.commit()

    return jsonify(None)


@module.route('api/delete_action.json', methods=['POST'])
def api_delete_action():
    action_id = int(request.json['action_id'])
    if not action_id:
        return jsonify(None, 404, "Argument 'action_id' cannot be found.")
    action = Action.query.get(action_id)
    ok, code, msg = delete_action(action)
    if ok:
        db.session.commit()
        return jsonify(None)
    else:
        return jsonify(None, code, msg)


@module.route('api/delete_event.json', methods=['POST'])
def api_delete_event():
    event_id = request.json.get('event_id')
    if not event_id:
        return abort(404)
    event = Event.query.get_or_404(event_id)

    msg = {}
    if UserUtils.can_delete_event(event, msg):
        event.deleted = 1
        db.session.add(event)
        db.session.query(Action).filter(
            Action.event_id == event.id
        ).update({
            Action.deleted: 1,
        }, synchronize_session=False)
        db.session.query(Visit).filter(
            Visit.event_id == event.id
        ).update({
            Visit.deleted: 1,
        }, synchronize_session=False)
        db.session.query(ScheduleClientTicket).filter(
            ScheduleClientTicket.event_id == event.id
        ).update({
            ScheduleClientTicket.event_id: None,
        }, synchronize_session=False)
        db.session.commit()
        return jsonify(None)

    return jsonify(None, 403, msg.get('message', ''))


@module.route('/api/events.json', methods=["POST"])
def api_get_events():
    flt = request.get_json()
    base_query = Event.query.join(Client)
    context = EventVisualizer()
    if 'id' in flt:
        event = base_query.filter(Event.id == flt['id']).first()
        return jsonify({
            'pages': 1,
            'items': [context.make_short_event(event)] if event else []
        })
    if 'external_id' in flt:
        base_query = base_query.filter(Event.externalId == flt['external_id'])
    if 'client_id' in flt:
        base_query = base_query.filter(Event.client_id == flt['client_id'])
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
    if 'speciality_id' in flt:
        base_query = base_query.join(Event.execPerson).filter(Person.speciality_id == flt['speciality_id'])
    if 'exec_person_id' in flt:
        base_query = base_query.filter(Event.execPerson_id == flt['exec_person_id'])
    if 'result_id' in flt:
        base_query = base_query.filter(Event.result_id == flt['result_id'])

    order_options = flt.get('sorting_params')
    if order_options:
        desc_order = order_options['order'] == 'DESC'
        col_name = order_options['column_name']
        if col_name == 'id':
            base_query = base_query.order_by(Event.id.desc() if desc_order else Event.id)
        if col_name == 'external_id':
            # that's bad
            ext_id_order_1 = u'CAST(SUBSTR(%s, 1, 4) AS UNSIGNED)' % Event.externalId
            ext_id_order_2 = u'CAST(SUBSTR(%s, 6) AS UNSIGNED)' % Event.externalId
            if desc_order:
                ext_id_order_1 = desc(ext_id_order_1)
                ext_id_order_2 = desc(ext_id_order_2)
            base_query = base_query.order_by(ext_id_order_1, ext_id_order_2)
        elif col_name == 'type_name':
            base_query = base_query.join(EventType).order_by(EventType.name.desc() if desc_order else EventType.name)
        elif col_name == 'beg_date':
            base_query = base_query.order_by(Event.setDate.desc() if desc_order else Event.setDate)
        elif col_name == 'end_date':
            base_query = base_query.order_by(Event.execDate.desc() if desc_order else Event.execDate)
        elif col_name == 'client_full_name':
            base_query = base_query.order_by(Client.lastName.desc() if desc_order else Client.lastName)
        elif col_name == 'person_short_name':
            base_query = base_query.join(Event.execPerson).order_by(Person.lastName.desc() if desc_order else Person.lastName)
        elif col_name == 'result_text':
            base_query = base_query.join(rbResult).order_by(rbResult.name.desc() if desc_order else rbResult.name)
    else:
        base_query = base_query.order_by(Event.setDate)

    per_page = int(flt.get('per_page', 20))
    page = int(flt.get('page', 1))
    paginate = base_query.paginate(page, per_page, False)
    return jsonify({
        'pages': paginate.pages,
        'items': [
            context.make_short_event(event)
            for event in paginate.items
        ]
    })
