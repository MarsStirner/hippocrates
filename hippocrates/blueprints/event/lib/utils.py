# -*- coding: utf-8 -*-

import datetime
import logging
import uuid

from flask_login import current_user
from nemesis.lib.data_ctrl.accounting.contract import ContractController
from nemesis.models.utils import safe_current_user_id
from sqlalchemy import func
from sqlalchemy.orm import aliased

from nemesis.lib.data import create_action, get_action, get_action_by_id
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.user import UserUtils
from nemesis.models.actions import Action, ActionType, ActionProperty_Diagnosis, \
    ActionProperty, ActionPropertyType, ActionProperty_OrgStructure
from nemesis.models.client import Client
from nemesis.lib.apiutils import ApiException
from nemesis.models.event import Event, EventType, Visit, Event_Persons
from nemesis.lib.utils import safe_traverse, safe_datetime, get_new_event_ext_id
from nemesis.models.exists import Person, OrgStructure, ClientQuoting, MKB, \
    VMPQuotaDetails, VMPCoupon, rbRequestType
from nemesis.models.enums import ActionStatus, OrgStructType
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.lib.const import STATIONARY_RECEIVED_CODE, STATIONARY_MOVING_CODE, \
    STATIONARY_ORG_STRUCT_STAY_CODE, STATIONARY_ORG_STRUCT_RECEIVED_CODE, \
    STATIONARY_ORG_STRUCT_TRANSFER_CODE, STATIONARY_HOSP_BED_CODE, \
    STATIONARY_HOSP_BED_PROFILE_CODE, STATIONARY_PATRONAGE_CODE, \
    DAY_HOSPITAL_CODE
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class EventSaveException(ApiException):
    def __init__(self, message=u'', data=None):
        base_msg = u'Ошибка сохранения данных обращения'
        code = data and data.get('code') or 500
        msg = message or base_msg
        ext_msg = data and data.get('ext_msg') or ''
        if ext_msg:
            msg = u'%s: %s' % (msg, ext_msg)
        super(EventSaveException, self).__init__(code, msg)
        self.data = data


class EventSaveController():
    def __init__(self):
        pass

    def create_base_info(self, event, all_data):
        # для всех request type
        event_data = all_data['event']
        event.setPerson_id = current_user.get_main_user().id
        client_id = safe_traverse(event_data, 'client', 'id') or event_data['client_id']
        event.client_id = client_id
        event.client = Client.query.get(client_id)
        event.org_id = event_data['organisation']['id']
        event.payStatus = 0
        event = self.update_base_info(event, event_data)
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        event.uuid = uuid.uuid4()
        return event

    def update_base_info(self, event, event_data):
        """
        @type event: nemesis.models.event.Event
        @param event:
        @param event_data:
        @return:
        """
        event.eventType = EventType.query.get(event_data['event_type']['id'])
        exec_person_id = safe_traverse(event_data, 'exec_person', 'id')
        event.setDate = safe_datetime(event_data['set_date'])
        if UserUtils.can_set_event_exec_date(event):
            event.execDate = safe_datetime(event_data['exec_date'])
        if exec_person_id and not event.is_diagnostic:
            event.execPerson = Person.query.get(exec_person_id)
        if event.is_stationary:
            event.isPrimaryCode = event_data['is_primary']['id']
            event.order = event_data['order']['id']
        contract_id = event_data['contract']['id']
        event.contract_id = contract_id
        if not event.id:
            if not contract_id:
                contract_controller = ContractController()
                contract = contract_controller.get_new_contract()
                contract = contract_controller.update_contract(contract, event_data['contract'])
                contract_controller.session.add(contract)
                event.contract = contract
            else:
                self.update_contract(contract_id, event.client_id)
        event.note = event_data.get('note')
        event.orgStructure_id = safe_traverse(event_data, 'org_structure', 'id')
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

        received = create_action(action_type.id, event)
        received = self.update_received_data(received, received_info)
        return received


class MovingController():
    def __init__(self):
        pass

    def update_moving_data(self, moving, moving_info):
        moving.begDate = safe_datetime(moving_info['beg_date'])
        moving.endDate = safe_datetime(moving_info.get('end_date'))
        if moving.endDate is not None:
            moving.status = ActionStatus.finished[0]
        else:
            moving.status = ActionStatus.started[0] if moving.status == ActionStatus.finished[0] \
                else moving.status

        moving[STATIONARY_ORG_STRUCT_STAY_CODE].value = moving_info['orgStructStay']['value']
        moving[STATIONARY_ORG_STRUCT_TRANSFER_CODE].value = moving_info['orgStructTransfer']['value']
        moving[STATIONARY_PATRONAGE_CODE].value = safe_traverse(
            moving_info, 'patronage', 'value')
        if 'hospitalBed' in moving_info:
            moving[STATIONARY_HOSP_BED_CODE].value = safe_traverse(
                moving_info, 'hospitalBed', 'value')
        if 'hospitalBedProfile' in moving_info:
            moving[STATIONARY_HOSP_BED_PROFILE_CODE].value = safe_traverse(
                moving_info, 'hospitalBedProfile', 'value')

        return moving

    def update_prev_moving(self, prev_action):
        # TODO
        if not prev_action.endDate:
            prev_action.endDate = moving.begDate
        prev_action.propsByCode['orgStructTransfer'].value = moving.propsByCode['orgStructStay'].value

    def get_moving(self, action_id):
        return get_action_by_id(action_id)

    def create_moving(self, event, moving_info):
        moving = get_action_by_id(None, event, STATIONARY_MOVING_CODE, True)

        beg_date = datetime.datetime.now()
        stay_os = from_os = None
        if 'received_id' in moving_info:
            received = get_action_by_id(moving_info['received_id'])
            from_os = received[STATIONARY_ORG_STRUCT_STAY_CODE].value
            stay_os = received[STATIONARY_ORG_STRUCT_TRANSFER_CODE].value
            if received.endDate:
                beg_date = received.endDate + datetime.timedelta(seconds=1)
        elif 'latest_moving_id' in moving_info:
            prev_moving = get_action_by_id(moving_info['latest_moving_id'])
            from_os = prev_moving[STATIONARY_ORG_STRUCT_STAY_CODE].value
            stay_os = prev_moving[STATIONARY_ORG_STRUCT_TRANSFER_CODE].value
            if prev_moving.endDate:
                beg_date = prev_moving.endDate + datetime.timedelta(seconds=1)

        moving[STATIONARY_ORG_STRUCT_RECEIVED_CODE].value = from_os
        moving[STATIONARY_ORG_STRUCT_STAY_CODE].value = stay_os
        moving.begDate = beg_date

        return moving


def get_hb_days_for_moving_list(moving_ids):
    """Рассчитать длительность нахождения пациента в отделениях по движениям.

    Длительность рассчитывается как разница между датой начала и датой окончания
    экшена движения. Длительность нахождения в реанимационном отделении добавляется к
    длительности предыдущего движения.
    """
    if not moving_ids:
        return {}

    NextMoving = aliased(Action, name='NextMoving')
    NextResusMoving = aliased(Action, name='NextResusMoving')

    q_next_moving = db.session.query(NextMoving.id).join(
        ActionType, ActionProperty, ActionPropertyType
    ).outerjoin(
        ActionProperty_OrgStructure
    ).outerjoin(
        OrgStructure
    ).filter(
        ActionType.flatCode == STATIONARY_MOVING_CODE,
        ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
        Action.deleted == 0, ActionProperty.deleted == 0,
        ActionPropertyType.deleted == 0,
        NextMoving.event_id == Action.event_id,
        NextMoving.begDate >= Action.id,
        NextMoving.id > Action.id,
        OrgStructure.type != OrgStructType.resuscitation[0]
    ).order_by(Action.begDate).limit(1).subquery()

    q_next_resus_moving = db.session.query(NextResusMoving.id).join(
        ActionType, ActionProperty, ActionPropertyType
    ).join(
        ActionProperty_OrgStructure, OrgStructure
    ).filter(
        ActionType.flatCode == STATIONARY_MOVING_CODE,
        ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
        Action.deleted == 0, ActionProperty.deleted == 0,
        ActionPropertyType.deleted == 0,
        NextResusMoving.event_id == Action.event_id,
        NextResusMoving.begDate >= Action.id, NextResusMoving.begDate <= NextMoving.begDate,
        NextResusMoving.id > Action.id, NextResusMoving.id < NextMoving.id,
        OrgStructure.type == OrgStructType.resuscitation[0]
    ).order_by(Action.begDate.desc()).limit(1).subquery()

    query = db.session.query(Action).join(
        Event, EventType, rbRequestType
    ).outerjoin(
        NextMoving, NextMoving.id == q_next_moving
    ).outerjoin(
        NextResusMoving, NextResusMoving.id == q_next_resus_moving
    ).filter(
        Action.id.in_(moving_ids)
    ).with_entities(
        Action.event_id.label('event_id'), Action.id.label('moving_id'),
        (func.datediff(
            func.coalesce(
                func.IF(NextResusMoving.id.isnot(None),
                        NextResusMoving.endDate,
                        Action.endDate),
                func.curdate()
            ),
            Action.begDate
        ) + func.IF(rbRequestType.code.in_(DAY_HOSPITAL_CODE), 1, 0)
        ).label('hb_days')
    )
    res = {}
    for item in query:
        res[item.event_id] = {
            'moving_id': item.moving_id,
            'hb_days': item.hb_days
        }
    return res


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
    event.orgStructure_id = safe_traverse(event_data, 'org_structure', 'id')
    event.payStatus = 0
    event.note = event_data.get('note')
    event.uuid = uuid.uuid4()

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
    if event.is_policlinic:
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


def received_close(event):
    received = get_action(event, STATIONARY_RECEIVED_CODE)
    if received and received.status < 2:
        received.modifyPerson = safe_current_user_id()
        received.modifyDatetime = datetime.datetime.now()
        received.endDate = datetime.datetime.now()
        received.status = 2


def client_quota_save(event, quota_data):
    quota_id = quota_data.get('id')
    coupon_id = safe_traverse(quota_data, 'coupon', 'id')
    coupon_beg_date = safe_traverse(quota_data, 'coupon', 'beg_date')
    coupon_end_date = safe_traverse(quota_data, 'coupon', 'end_date')
    coupon = VMPCoupon.query.get(coupon_id) if coupon_id else None
    if coupon:
        coupon.begDate = safe_datetime(coupon_beg_date)
        coupon.endDate = safe_datetime(coupon_end_date)
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

