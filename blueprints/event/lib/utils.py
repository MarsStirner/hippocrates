# -*- coding: utf-8 -*-
from collections import defaultdict

import datetime
from application.lib.data import create_action
from application.models.actions import Action, ActionType
from application.models.event import Event, EventType, EventLocalContract
from application.lib.utils import safe_date
from flask.ext.login import current_user
from application.models.exists import rbDocumentType, ContractTariff, Contract, rbService
from application.lib.settings import Settings
from application.systemwide import db


def create_new_local_contract(lc_info):
    lcon = EventLocalContract()
    lcon.coordAgent = lc_info.get('coord_agent', '')
    lcon.coordInspector = lc_info.get('coord_inspector', '')
    lcon.coordText = lc_info.get('coord_text', '')

    if Settings.getBool('Event.Payment.1CODVD'):
        lcon.dateContract = lc_info.get('date_contract') or datetime.date.today()
        lcon.numberContract = lc_info.get('number_contract') or ''
    else:
        lcon.dateContract = lc_info['date_contract']
        lcon.numberContract = lc_info['number_contract']
    lcon.sumLimit = lc_info.get('sum_limit', 0.0)
    lcon.lastName = lc_info.get('last_name')
    lcon.firstName = lc_info.get('first_name')
    lcon.patrName = lc_info.get('patr_name')
    lcon.birthDate = safe_date(lc_info.get('birth_date'))
    _doc_type = lc_info.get('doc_type', {})
    lcon.documentType_id = _doc_type.get('id') if _doc_type else None
    lcon.documentType = rbDocumentType.query.get(_doc_type.get('id')) if _doc_type else None
    lcon.serialLeft = lc_info.get('serial_left')
    lcon.serialRight = lc_info.get('serial_right')
    lcon.number = lc_info.get('number')
    lcon.regAddress = lc_info.get('reg_address')
    _payer_org = lc_info.get('payer_org', {})
    lcon.org_id = _payer_org.get('id') if _payer_org else None
    return lcon


def get_local_contract(lc_info):
    lc_id = None
    if lc_info:
        lc_id = lc_info.get('id')
    if lc_id:
        def _has_changes(lc, lc_info):
            if (lc.numberContract != lc_info.get('number_contract', '')
                    or lc.lastName != lc_info.get('last_name', '')
                    or lc.firstName != lc_info.get('first_name', '')
                    or lc.patrName != lc_info.get('patr_name', '')
                    or lc.birthDate != safe_date(lc_info.get('birth_date', ''))
                    or lc.documentType_id != lc_info.get('doc_type', {}).get('id')
                    or lc.serialLeft != lc_info.get('serial_left', '')
                    or lc.serialRight != lc_info.get('serial_right', '')
                    or lc.number != lc_info.get('number', '')
                    or lc.regAddress != lc_info.get('reg_address', '')
                    or lc.org_id != lc_info.get('payer_org_id')):
                return True
            return False

        lcon = EventLocalContract.query.get(lc_id)
        if _has_changes(lcon, lc_info):
            lcon = create_new_local_contract(lc_info)
    else:
        lcon = create_new_local_contract(lc_info)
    return lcon


def get_prev_event_payment(client_id, event_type_id):
    event = Event.query.join(EventType).filter(EventType.id == event_type_id,
                                               Event.client_id == client_id,
                                               Event.deleted == 0).\
        order_by(Event.setDate.desc()).first()
    if not event:
        event = Event()
        lc = EventLocalContract()
        event.localContract = lc
    return event


def get_event_services(event_id):
    query = db.session.query(Action,
                             ActionType.id,
                             ActionType.service_id,
                             ActionType.code,
                             ActionType.name,
                             rbService.name,
                             ContractTariff.price).\
        join(Event,
             EventType,
             Contract,
             ContractTariff,
             ActionType).\
        join(rbService, ActionType.service_id == rbService.id).\
        filter(Action.event_id == event_id,
               ContractTariff.eventType_id == EventType.id,
               ContractTariff.service_id == ActionType.service_id,
               Action.deleted == 0,
               ContractTariff.deleted == 0).all()
    services_by_at = defaultdict(list)
    for a, at_id, service_id, at_code, at_name, service_name, price in query:
        s = {
            'at_id': at_id,
            'at_code': at_code,
            'at_name': at_name,
            'service_name': service_name,
            'price': price,
            'action_id': a.id,
            'service_id': service_id,
            'is_coord': a.coordDate and a.coordPerson_id
        }
        services_by_at[(at_id, service_id)].append(s)
    services_grouped = []
    for k, service_group in services_by_at.iteritems():
        actions = []
        coord_actions = []
        for s in service_group:
            actions.append(s['action_id'])
            if s['is_coord']:
                coord_actions.append(s['action_id'])
        services_grouped.append(
            dict(service_group[0],
                 amount=len(service_group),
                 sum=service_group[0]['price'] * len(service_group),
                 actions=actions,
                 coord_actions=coord_actions))

    return services_grouped


def create_services(event_id, services_data, cfinance_id):
    result = []
    for service in services_data:
        created_count = len(service['actions'])
        new_count = int(float(service['amount']))
        # TODO: отработать случай уменьшения количества услуг при редактировании обращения (created_count > new_count)
        if created_count < new_count:
            for i in xrange(1, new_count - created_count + 1):
                action = create_action(
                    event_id,
                    service['at_id'],
                    current_user.id,
                    {'finance_id': cfinance_id,
                     'coordDate': datetime.datetime.now() if service.get('coord_person_id') else None,
                     'coordPerson_id': service.get('coord_person_id')})
                result.append(action.id)
    return result