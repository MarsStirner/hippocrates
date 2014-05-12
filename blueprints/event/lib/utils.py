# -*- coding: utf-8 -*-

import datetime
from application.models.event import Event, EventType, EventLocalContract
from application.lib.utils import safe_date
from flask.ext.login import current_user
from application.models.exists import rbDocumentType
from application.lib.settings import Settings


def create_new_local_contract(lc_info):
    now = datetime.datetime.now()
    lcon = EventLocalContract()
    lcon.createDatetime = lcon.modifyDatetime = now
    lcon.createPerson_id = lcon.modifyPerson_id = current_user.get_id() or 1  # todo: fix
    lcon.deleted = 0
    lcon.coordAgent = lc_info.get('coord_agent', '')
    lcon.coordInspector = lc_info.get('coord_inspector', '')
    lcon.coordText = lc_info.get('coord_text', '')

    if Settings.getBool('Event.Payment.1CODVD'):
        lcon.dateContract = lc_info.get('date_contract', '')
        lcon.numberContract = lc_info.get('number_contract', '')
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