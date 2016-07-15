# -*- coding: utf-8 -*-

import datetime
import logging

from flask_login import current_user
from sqlalchemy import func

from nemesis.lib.data import create_new_action, update_action, ActionException, create_action
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.user import UserUtils
from nemesis.models.actions import Action, ActionType, ActionProperty_Diagnosis
from nemesis.models.client import Client
from nemesis.lib.apiutils import ApiException
from nemesis.models.event import EventLocalContract, Event, EventType, Visit, Event_Persons
from nemesis.lib.utils import safe_date, safe_traverse, safe_datetime, get_new_event_ext_id, get_new_uuid
from nemesis.models.exists import rbDocumentType, Person, OrgStructure, ClientQuoting, MKB, VMPQuotaDetails, VMPCoupon
from nemesis.lib.settings import Settings
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db

logger = logging.getLogger('simple')


class EventSaveException(Exception):
    def __init__(self, message=u'', data=None):
        super(EventSaveException, self).__init__(message)
        self.data = data


class EventSaveController():
    def __init__(self):
        pass

    def create_base_info(self, event, all_data):
        # для всех request type
        event_data = all_data['event']
        event.setPerson_id = current_user.get_main_user().id
        event.client_id = event_data['client_id']
        event.client = Client.query.get(event_data['client_id'])
        event.org_id = event_data['organisation']['id']
        event.payStatus = 0
        event = self.update_base_info(event, event_data)
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        event.uuid = get_new_uuid()
        return event

    def update_base_info(self, event, event_data):
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        exec_person_id = safe_traverse(event_data, 'exec_person', 'id')
        event.setDate = safe_datetime(event_data['set_date'])
        if exec_person_id and not event.is_diagnostic:
            event.execPerson = Person.query.get(exec_person_id)
        if event.is_stationary:
            event.isPrimaryCode = event_data['is_primary']['id']
            event.order = event_data['order']['id']
        contract_id = event_data['contract']['id']
        event.contract_id = contract_id
        if not event.id:
            self.update_contract(contract_id, event.client_id)
        event.note = event_data['note']
        event.orgStructure_id = event_data['org_structure']['id'] if event_data['org_structure'] else None
        event.result_id = safe_traverse(event_data, 'result', 'id')
        event.rbAcheResult_id = safe_traverse(event_data, 'ache_result', 'id')
        return event

    def update_contract(self, contract_id, client_id):
        from nemesis.lib.data_ctrl.accounting.contract import ContractController
        contract_ctrl = ContractController()
        contract = contract_ctrl.get_contract(contract_id)
        contract_ctrl.try_add_contingent(contract, client_id)

    def store(self, *entity_list):
        db.session.add_all(entity_list)
        db.session.commit()


class ReceivedController():
    def __init__(self):
        pass

    def update_received_data(self, received, received_info):
        diag_codes = ('diag_received', 'diag_received1', 'diag_received2')
        received.begDate = safe_datetime(received_info['beg_date'])
        for code, prop in received_info.iteritems():
            if code not in ('id', 'beg_data', 'person', 'flatCode', 'event_id') + diag_codes and code in received.propsByCode:
                received.propsByCode[code].value = prop['value']
            elif code in diag_codes and prop['value']:
                property = received.propsByCode[code]
                property.value = ActionProperty_Diagnosis.objectify(property, prop['value'])
        db.session.add(received)
        db.session.commit()
        return received

    def create_received(self, event_id, received_info):

        event = Event.query.get(event_id)
        action_type = ActionType.query.filter(ActionType.flatCode == u'received').first()

        received = create_action(action_type, event)
        received = self.update_received_data(received, received_info)
        return received


class MovingController():
    def __init__(self):
        pass

    def get_prev_action(self, event_id):
        """
        получить предыдущее движение или послупление
        """
        movings = db.session.query(Action).join(ActionType).filter(Action.event_id == event_id,
                                                                   Action.deleted == 0,
                                                                   ActionType.flatCode == 'moving').order_by(Action.begDate).all()
        if movings:
            action = movings[-1]
        else:
            action = db.session.query(Action).join(ActionType).filter(Action.event_id == event_id,
                                                                      Action.deleted == 0,
                                                                      ActionType.flatCode == 'received'
                                                                      ).first()
        return action

    def update_moving_data(self, moving, moving_info):
        moving.begDate = safe_datetime(moving_info['beg_date'])
        moving.propsByCode['orgStructStay'].value = moving_info['orgStructStay']['value']
        moving.propsByCode['hospitalBed'].value = moving_info['hospitalBed']['value'] if moving_info.get('hospitalBed') else None
        moving.propsByCode['hospitalBedProfile'].value = moving_info['hospitalBedProfile']['value'] if \
            moving_info.get('hospitalBedProfile') else None
        moving.propsByCode['patronage'].value = moving_info['patronage']['value'] if moving_info.get('patronage') else None
        db.session.add(moving)
        db.session.commit()
        return moving

    def create_moving(self, event_id, moving_info):
        event = Event.query.get(event_id)
        action_type = ActionType.query.filter(ActionType.flatCode == u'moving').first()

        moving = create_action(action_type, event)
        prev_action = self.get_prev_action(moving_info.get('event_id'))
        moving.propsByCode['orgStructReceived'].value = prev_action['orgStructStay'].value
        moving = self.update_moving_data(moving, moving_info)

        if not prev_action.endDate:
            prev_action.endDate = moving.begDate
        prev_action.propsByCode['orgStructDirection'].value = moving.propsByCode['orgStructStay'].value
        db.session.add(prev_action)
        db.session.commit()
        return prev_action, moving

    def close_moving(self, moving):
        moving.endDate = datetime.datetime.now()
        db.session.add(moving)
        db.session.commit()
        return moving


def create_new_event(event_data):
    base_msg = u'Невозможно создать обращение: %s.'
    event = Event()
    event.setPerson_id = current_user.get_main_user().id
    event.eventType = EventType.query.get(event_data['event_type']['id'])
    event.client_id = event_data['client_id']
    event.client = Client.query.get(event_data['client_id'])
    exec_person_id = safe_traverse(event_data, 'exec_person', 'id')
    if exec_person_id and not event.is_diagnostic:
        event.execPerson = Person.query.get(exec_person_id)
    event.setDate = safe_datetime(event_data['set_date'])
    event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
    # event.contract_id = event_data['contract']['id']
    event.isPrimaryCode = event_data['is_primary']['id']
    event.order = event_data['order']['id']
    event.org_id = event_data['organisation']['id']
    event.orgStructure_id = event_data['org_structure']['id']
    event.payStatus = 0
    event.note = event_data['note']
    event.uuid = get_new_uuid()

    error_msg = {}
    if not UserUtils.can_create_event(event, error_msg):
        raise EventSaveException(base_msg % error_msg['message'], {
            'code': 403
        })

    if event.is_policlinic:
        visit = Visit.make_default(event)
        db.session.add(visit)
        executives = Event_Persons()
        executives.person = event.execPerson
        executives.event = event
        executives.begDate = event.setDate
        db.session.add(executives)
    return event


def update_event(event_id, event_data):
    event = Event.query.get(event_id)
    event.eventType = EventType.query.get(event_data['event_type']['id'])
    exec_person_id = safe_traverse(event_data, 'exec_person', 'id')
    if exec_person_id and not event.is_diagnostic:
        event.execPerson = Person.query.get(exec_person_id)
    event.setDate = safe_datetime(event_data['set_date'])
    event.execDate = safe_datetime(event_data['exec_date'])
    event.contract_id = event_data['contract']['id']
    event.isPrimaryCode = event_data['is_primary']['id']
    event.order = event_data['order']['id']
    event.orgStructure_id = event_data['org_structure']['id']
    event.result_id = safe_traverse(event_data, 'result', 'id')
    event.rbAcheResult_id = safe_traverse(event_data, 'ache_result', 'id')
    event.note = event_data['note']
    return event


def save_event(event_id, data):
    event_data = data.get('event')
    if not event_data:
        raise EventSaveException(data={
            'ext_msg': u'Отсутствует основная информация об обращении'
        })
    create_mode = not event_id
    if event_id:
        event = update_event(event_id, event_data)
        db.session.add(event)
    else:
        event = create_new_event(event_data)
    db.session.add(event)

    result = {}
    try:
        db.session.commit()
    except Exception, e:
        logger.error(e, exc_info=True)
        db.session.rollback()
        raise EventSaveException()
    else:
        result['id'] = int(event)

        # save ticket reference
        if create_mode:
            ticket_id = data.get('ticket_id')
            if ticket_id:
                ticket = ScheduleClientTicket.query.get(int(ticket_id))
                ticket.event_id = int(event)
                db.session.commit()

    return result


def received_save(event_id, received_data):
    received_ctrl = ReceivedController()
    received_id = received_data['id']
    diagnoses_data = received_data.get('diagnoses')
    if received_id:
        received = Action.query.get(received_id)
        if not received:
            raise ApiException(404, u'Не найдено поступление с id = {}'.format(received_id))
        received = received_ctrl.update_received_data(received, received_data)
    else:
        received = received_ctrl.create_received(event_id, received_data)

    if diagnoses_data:
        create_or_update_diagnoses(received, diagnoses_data)
    db.session.add(received)
    db.session.commit()


def client_quota_save(event, quota_data):
    quota_id = quota_data.get('id')
    coupon_id = safe_traverse(quota_data, 'coupon', 'id')
    coupon = VMPCoupon.query.get(coupon_id) if coupon_id else None
    with db.session.no_autoflush:
        if quota_id:
            quota = ClientQuoting.query.get(quota_id)
            if not quota:
                raise ApiException(404, u'Не найдена квота с id = {}'.format(quota_id))
            quota.MKB_object = MKB.query.get(safe_traverse(quota_data, 'mkb', 'id'))
            quota.quotaDetails.pacientModel_id = safe_traverse(quota_data, 'patient_model', 'id')
            quota.quotaDetails.quotaType_id = safe_traverse(quota_data, 'quota_type', 'id')
            quota.quotaDetails.treatment_id = safe_traverse(quota_data, 'treatment', 'id')
            if quota.vmpCoupon != coupon:
                quota.vmpCoupon.clientQuoting_id = None
                db.session.add(quota.vmpCoupon)
            quota.vmpCoupon = coupon
            coupon.clientQuoting_id = quota_id
        else:
            quota = ClientQuoting()
            quota.master = event.client
            quota.MKB_object = MKB.query.get(safe_traverse(quota_data, 'mkb', 'id'))
            quota_ditails = VMPQuotaDetails()
            quota_ditails.pacientModel_id = safe_traverse(quota_data, 'patient_model', 'id')
            quota_ditails.quotaType_id = safe_traverse(quota_data, 'quota_type', 'id')
            quota_ditails.treatment_id = safe_traverse(quota_data, 'treatment', 'id')
            quota.quotaDetails = quota_ditails
            quota.event = event
            quota.vmpCoupon = coupon

        db.session.add(quota)
        db.session.commit()
        coupon.clientQuoting_id = quota.id
        db.session.add(coupon)
        db.session.commit()


def save_executives(event_id):
    event = Event.query.get(event_id)
    if not event or not event.execDate:
        return
    try:
        last_executive = db.session.query(
            func.max(Event_Persons.id)
        ).filter(
            Event_Persons.event_id == event.id
        ).first()
        if last_executive:
            db.session.query(Event_Persons).filter(
                Event_Persons.id == last_executive[0]
            ).update({
                Event_Persons.endDate: event.execDate
            }, synchronize_session=False)
            db.session.commit()
    except Exception, e:
        db.rollback()
        raise EventSaveException(u'Ошибка закрытия обращения')


def integration_1codvd_enabled():
    return Settings.getBool('Event.Payment.1CODVD')


class PaymentKind:
    per_event = 0
    per_service = 1


def get_event_payment_kind(event):
    if event:
        is_per_event = lambda payment: not payment.is_per_service()
        is_per_service = lambda payment: payment.is_per_service()
        if any(map(is_per_event, event.payments)):
            return PaymentKind.per_event
        if any(map(is_per_service, event.payments)):
            return PaymentKind.per_service
    return PaymentKind.per_service if integration_1codvd_enabled() else PaymentKind.per_event


def create_new_local_contract(lc_info):
    err_msg = u'Ошибка сохранения обращения'
    lcon = EventLocalContract()

    date = lc_info.get('date_contract')
    if integration_1codvd_enabled():
        number = lc_info.get('number_contract') or ''
    else:
        number = lc_info.get('number_contract')
    if not date:
        raise EventSaveException(data={
            'ext_msg': u'Не указана дата заключения договора'
        })
    lcon.dateContract = date
    if number is None:
        raise EventSaveException(data={
            'ext_msg': u'Не указан номер договора'
        })
    lcon.numberContract = number

    lcon.coordAgent = lc_info.get('coord_agent', '')
    lcon.coordInspector = lc_info.get('coord_inspector', '')
    lcon.coordText = lc_info.get('coord_text', '')
    lcon.sumLimit = lc_info.get('sum_limit', 0.0)
    lcon.lastName = lc_info.get('last_name')
    lcon.firstName = lc_info.get('first_name')
    lcon.patrName = lc_info.get('patr_name')
    lcon.birthDate = safe_date(lc_info.get('birth_date'))

    doc_type_id = safe_traverse(lc_info, 'doc_type', 'id')
    lcon.documentType_id = doc_type_id
    lcon.documentType = rbDocumentType.query.get(doc_type_id) if doc_type_id else None
    lcon.serialLeft = lc_info.get('serial_left')
    lcon.serialRight = lc_info.get('serial_right')
    lcon.number = lc_info.get('number')
    lcon.regAddress = lc_info.get('reg_address')
    lcon.org_id = safe_traverse(lc_info, 'payer_org', 'id')
    return lcon


def _check_shared_local_contract_changes(lc_info):
    def _has_changes(lc, lc_info):
        if (lc.numberContract != lc_info.get('number_contract', '')
                or lc.dateContract != safe_date(lc_info.get('date_contract'))
                or lc.lastName != lc_info.get('last_name', '')
                or lc.firstName != lc_info.get('first_name', '')
                or lc.patrName != lc_info.get('patr_name', '')
                or lc.birthDate != safe_date(lc_info.get('birth_date', ''))
                or lc.documentType_id != safe_traverse(lc_info, 'doc_type', 'id')
                or lc.serialLeft != lc_info.get('serial_left', '')
                or lc.serialRight != lc_info.get('serial_right', '')
                or lc.number != lc_info.get('number', '')
                or lc.regAddress != lc_info.get('reg_address', '')
                or lc.org_id != safe_traverse(lc_info, 'payer_org', 'id')):
            return True
        return False

    lc_id = lc_info.get('id')
    lcon = EventLocalContract.query.get(lc_id)
    return _has_changes(lcon, lc_info)


def get_local_contract_for_new_event(lc_info):
    lc_id = None
    if lc_info:
        lc_id = lc_info.get('id')
    if lc_id:
        if _check_shared_local_contract_changes(lc_info):
            lcon = create_new_local_contract(lc_info)
        else:
            lcon = EventLocalContract.query.get(lc_id)
    else:
        lcon = create_new_local_contract(lc_info)
    return lcon


def create_or_update_local_contract(event, lc_info):
    lc_id = lc_info.get('id')
    number_contract = lc_info.get('number_contract', '')
    date_contract = safe_date(lc_info.get('date_contract'))
    coord_text = lc_info.get('coord_text', '')
    last_name = lc_info.get('last_name', '')
    first_name = lc_info.get('first_name', '')
    patr_name = lc_info.get('patr_name', '')
    birth_date = safe_date(lc_info.get('birth_date', ''))
    document_type_id = safe_traverse(lc_info, 'doc_type', 'id')
    serial_left = lc_info.get('serial_left', '')
    serial_right = lc_info.get('serial_right', '')
    doc_number = lc_info.get('number', '')
    reg_address = lc_info.get('reg_address', '')
    org_id = safe_traverse(lc_info, 'payer_org', 'id')
    if event.id:
        if not event.localContract_id:
            lc = get_local_contract_for_new_event(lc_info)
        else:
            if not lc_id or (
                lc_id and lc_info.get('shared_in_events') and _check_shared_local_contract_changes(lc_info)
            ):
                lc = create_new_local_contract(lc_info)
            else:
                lc = EventLocalContract.query.get(lc_id)
                lc.numberContract = number_contract
                lc.dateContract = date_contract
                lc.coordText = coord_text
                lc.lastName = last_name
                lc.firstName = first_name
                lc.patrName = patr_name
                lc.birthDate = birth_date
                lc.documentType_id = document_type_id
                lc.serialLeft = serial_left
                lc.serialRight = serial_right
                lc.number = doc_number
                lc.regAddress = reg_address
                lc.org_id = org_id
    else:
        lc = get_local_contract_for_new_event(lc_info)
    return lc


def create_services(event_id, service_groups, contract_id):
    """
    Создание или обновление услуг (действий) и последующее сохранение в бд.
    """
    actions = []
    errors = []
    for sg in service_groups:
        for act_data in sg['actions']:
            action_id = act_data['action_id']
            action_type = ActionType.query.get(sg['at_id'])
            data = {
                'amount': act_data.get('amount', 1),
                'account': act_data.get('account', 0),
                'coordDate': safe_datetime(act_data.get('coord_date')),
                'coordPerson_id': safe_traverse(act_data, 'coord_person', 'id')
            }
            if sg['is_lab']:
                data['plannedEndDate'] = safe_datetime(act_data['planned_end_date'])
            assigned = act_data['assigned'] if sg['is_lab'] else None

            try:
                if not action_id:
                    data['contract_id'] = contract_id
                    action = create_new_action(
                        sg['at_id'],
                        event_id,
                        assigned=assigned,
                        data=data
                    )
                else:
                    if assigned:
                        data['properties_assigned'] = assigned
                    action = Action.query.get(action_id)
                    action = update_action(action, **data)
            except ActionException, e:
                db.session.rollback()
                err_msg = u'Ошибка сохранения услуги "%s": %s.' % (action_type.name, e.message)
                logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                errors.append(err_msg)
            except Exception, e:
                db.session.rollback()
                err_msg = u'Ошибка сохранения услуги "%s"' % action_type.name
                logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                errors.append(err_msg)
            else:
                db.session.add(action)
                try:
                    db.session.commit()
                except Exception, e:
                    db.session.rollback()
                    err_msg = u'Ошибка сохранения услуги "%s"' % action_type.name
                    logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                    errors.append(err_msg)
                else:
                    actions.append(action)
    return actions, errors
