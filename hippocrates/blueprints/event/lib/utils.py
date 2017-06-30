# -*- coding: utf-8 -*-

import datetime
import logging
import uuid

from flask_login import current_user
from nemesis.lib.data_ctrl.accounting.contract import ContractController
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased, joinedload

from nemesis.lib.data import create_action, get_action_by_id, get_action
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.user import UserUtils
from nemesis.models.actions import Action, ActionType, ActionProperty_Diagnosis, \
    ActionProperty, ActionPropertyType, ActionProperty_OrgStructure
from nemesis.models.client import Client
from nemesis.lib.apiutils import ApiException
from nemesis.models.event import Event, EventType, Visit, Event_Persons
from nemesis.lib.utils import safe_traverse, safe_datetime, get_new_event_ext_id
from nemesis.models.exists import Person, OrgStructure, ClientQuoting, MKB, \
    VMPQuotaDetails, VMPCoupon, rbRequestType, rbResult, rbAcheResult
from nemesis.models.enums import ActionStatus, OrgStructType
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.lib.const import STATIONARY_RECEIVED_CODE, STATIONARY_MOVING_CODE, \
    STATIONARY_ORG_STRUCT_STAY_CODE, STATIONARY_ORG_STRUCT_RECEIVED_CODE, \
    STATIONARY_ORG_STRUCT_TRANSFER_CODE, STATIONARY_HOSP_BED_CODE, \
    STATIONARY_HOSP_BED_PROFILE_CODE, STATIONARY_PATRONAGE_CODE, \
    DAY_HOSPITAL_CODE, STATIONARY_STATCARD_CODE, LeavedProps, \
    STATIONARY_LEAVED_CODE, DEATH_EPICRISIS_CODE, DeathEpicrisisProps, \
    SurgicalReportProps
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

    def update_prev_moving_or_received(self, cur_moving):
        prev = self.get_prev_moving_or_received(cur_moving)
        if prev:
            if not prev.endDate:
                prev.endDate = cur_moving.begDate
            if prev.status != ActionStatus.finished[0]:
                prev.status = ActionStatus.finished[0]

            prev.propsByCode[STATIONARY_ORG_STRUCT_TRANSFER_CODE].value = cur_moving.\
                propsByCode[STATIONARY_ORG_STRUCT_STAY_CODE].value

    def get_moving(self, action_id):
        return get_action_by_id(action_id)

    def get_prev_moving_or_received(self, moving):
        result = db.session.query(Action).join(ActionType).filter(
            Action.deleted == 0,
            Action.event_id == moving.event_id,
            ActionType.flatCode.in_([STATIONARY_MOVING_CODE, STATIONARY_RECEIVED_CODE]),
            or_(Action.begDate < moving.begDate,
                and_(Action.begDate == moving.begDate,
                     Action.id < moving.id if moving.id else True)
                ),
            Action.id != moving.id
        ).order_by(Action.begDate.desc()).limit(1).options(joinedload(Action.actionType)).first()

        return result

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
        else:
            prev = self.get_prev_moving_or_received(moving)
            from_os = prev[STATIONARY_ORG_STRUCT_STAY_CODE].value
            stay_os = prev[STATIONARY_ORG_STRUCT_TRANSFER_CODE].value
            if prev.endDate:
                beg_date = prev.endDate + datetime.timedelta(seconds=1)

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


def update_executives(event, new_beg_date=None, latest_end_date=None):
    if new_beg_date is None:
        new_beg_date = datetime.datetime.now()
    if latest_end_date is None:
        latest_end_date = datetime.datetime.now()

    last_executive = Event_Persons.query.filter(
        Event_Persons.event_id == event.id
    ).order_by(Event_Persons.begDate.desc()).first()
    if event.execPerson and (not last_executive or last_executive.person_id != event.execPerson_id):
        executives = Event_Persons()
        executives.person = event.execPerson
        executives.event = event
        executives.begDate = new_beg_date
        db.session.add(executives)
    if last_executive:
        last_executive.endDate = latest_end_date
        db.session.add(last_executive)


class EventCloseWarningException(Exception): pass


class EventCloseErrorException(Exception): pass


class EventCloseController(object):

    def check_can_close(self, event, final_step=True, ignore_warnings=False):
        out_data = {}
        ok = UserUtils.can_perform_close_event(event, final_step=final_step, out_msg=out_data)
        if not ok:
            raise EventCloseErrorException(out_data['message'])
        elif 'warnings_message' in out_data and not ignore_warnings:
            raise EventCloseWarningException(out_data['warnings_message'])

    def perform_close_event(self, event, data, ignore_warnings=False):
        self._save_event_data(event, data)
        self._update_executives(event)
        self.check_can_close(event, ignore_warnings=ignore_warnings)

    def perform_close_hosp(self, event, data, ignore_warnings=False):
        self._save_event_data(event, data['event'])
        self._update_executives(event)
        self._save_hosp_additional_data(event, data)
        self.check_can_close(event, ignore_warnings=ignore_warnings)

    def _save_event_data(self, event, data):
        event.execDate = safe_datetime(data.get('exec_date'))
        result_id = safe_traverse(data, 'result', 'id')
        result = rbResult.query.get(result_id) if result_id else None
        event.result = result
        ache_result_id = safe_traverse(data, 'ache_result', 'id')
        ache_result = rbAcheResult.query.get(ache_result_id) if ache_result_id else None
        event.rbAcheResult = ache_result
        return event

    def _update_executives(self, event):
        update_executives(event, latest_end_date=event.execDate)

    def _save_hosp_additional_data(self, event, data):
        # save stat card
        stat_card_data = data['stat_card']
        stat_card = get_action(event, STATIONARY_STATCARD_CODE, create=True)
        stat_card.note = stat_card_data.get('note') or ''
        db.session.add(stat_card)

        # save surgeries
        def set_surgical_protocol_prop(action, code, value):
            if action.has_property(code):
                action.set_prop_value(code, value)

        surgeries_data = data['surgeries']
        for report in surgeries_data:
            action_id = report['id']
            action = get_action_by_id(action_id)
            set_surgical_protocol_prop(action, SurgicalReportProps.date_start, report['date_start'])
            set_surgical_protocol_prop(action, SurgicalReportProps.time_start, report['time_start'])

            set_surgical_protocol_prop(action, SurgicalReportProps.operation1,
                report['operations']['op1']['operation_type']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.anesthesia1,
                report['operations']['op1']['anesthesia']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.transplant1,
                report['operations']['op1']['transplant']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.spec_equipment_use1,
                report['operations']['op1']['spec_equipment_use']['value'])

            set_surgical_protocol_prop(action, SurgicalReportProps.operation2,
                report['operations']['op2']['operation_type']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.anesthesia2,
                report['operations']['op2']['anesthesia']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.transplant2,
                report['operations']['op2']['transplant']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.spec_equipment_use2,
                report['operations']['op2']['spec_equipment_use']['value'])

            set_surgical_protocol_prop(action, SurgicalReportProps.operation3,
                report['operations']['op3']['operation_type']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.anesthesia3,
                report['operations']['op3']['anesthesia']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.transplant3,
                report['operations']['op3']['transplant']['value'])
            set_surgical_protocol_prop(action, SurgicalReportProps.spec_equipment_use3,
                report['operations']['op3']['spec_equipment_use']['value'])

        # save leaved
        leaved_data = data['leaved']
        leaved = get_action(event, STATIONARY_LEAVED_CODE)
        if leaved:
            leaved[LeavedProps.rw].value = safe_traverse(leaved_data, 'rw', 'value')
            leaved[LeavedProps.aids].value = safe_traverse(leaved_data, 'aids', 'value')

        # save death epicr
        de_data = data['death_epicrisis']
        death_epicrisis = get_action(event, DEATH_EPICRISIS_CODE)
        if death_epicrisis:
            death_epicrisis[DeathEpicrisisProps.main_rod].value = safe_traverse(
                de_data, 'main_rod', 'value')

