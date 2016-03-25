# -*- coding: utf-8 -*-

import datetime
import logging

from flask.ext.login import current_user
from sqlalchemy import func, exists, join, and_, or_

from nemesis.lib.data import create_new_action, update_action, ActionException
from nemesis.lib.user import UserUtils
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_OrgStructure
from nemesis.models.client import Client
from nemesis.models.event import EventLocalContract, Event, EventType, Visit, Event_Persons
from nemesis.lib.utils import safe_date, safe_traverse, safe_datetime, get_new_event_ext_id, get_new_uuid
from nemesis.models.exists import rbDocumentType, Person, rbRequestType
from nemesis.lib.settings import Settings
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db
from nemesis.lib.const import (STATIONARY_EVENT_CODES, POLICLINIC_EVENT_CODES, STATIONARY_MOVING_CODE,
   STATIONARY_ORG_STRUCT_TRANSFER_CODE)

logger = logging.getLogger('simple')


class EventSaveException(Exception):
    def __init__(self, message=u'', data=None):
        super(EventSaveException, self).__init__(message)
        self.data = data


def create_new_event(event_data, local_contract_data, force_create=False):
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
    event.contract_id = event_data['contract']['id']
    event.isPrimaryCode = event_data['is_primary']['id']
    event.order = event_data['order']['id']
    event.org_id = event_data['organisation']['id']
    event.orgStructure_id = event_data['org_structure']['id']
    event.payStatus = 0
    event.note = event_data['note']
    event.uuid = get_new_uuid()

    error_msg = {}
    if not UserUtils.can_create_event(event, error_msg, force_create):
        raise EventSaveException(base_msg % error_msg['message'], {
            'code': 403,
            'obj': error_msg.get('obj')
        })

    if event.payer_required:
        if not local_contract_data:
            raise EventSaveException(base_msg % error_msg['message'], {
                'code': 422,
                'ext_msg': u'Не заполнена информация о плательщике.'
            })
        lcon = create_or_update_local_contract(event, local_contract_data)
        event.localContract = lcon

    if event.is_policlinic:
        visit = Visit.make_default(event)
        db.session.add(visit)
        executives = Event_Persons()
        executives.person = event.execPerson
        executives.event = event
        executives.begDate = event.setDate
        db.session.add(executives)
    return event


def update_event(event_id, event_data, local_contract_data):
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

    if local_contract_data:
        lcon = create_or_update_local_contract(event, local_contract_data)
        event.localContract = lcon
    return event


def save_event(event_id, data):
    event_data = data.get('event')
    if not event_data:
        raise EventSaveException(data={
            'ext_msg': u'Отсутствует основная информация об обращении'
        })
    force_create = data.get('force_create', False)
    create_mode = not event_id
    local_contract_data = safe_traverse(data, 'payment', 'local_contract')
    services_data = data.get('services', [])
    if event_id:
        event = update_event(event_id, event_data, local_contract_data)
        db.session.add(event)
    else:
        event = create_new_event(event_data, local_contract_data, force_create)
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

        # save actions
        contract_id = event_data['contract']['id']
        if create_mode:
            try:
                actions, errors = create_services(event.id, services_data, contract_id)
            except Exception, e:
                db.session.rollback()
                logger.error(u'Ошибка сохранения услуг при создании обращения %s: %s' % (event.id, e), exc_info=True)
                result['error_text'] = u'Обращение создано, но произошла ошибка при сохранении услуг. ' \
                                       u'Свяжитесь с администратором.'
            else:
                if errors:
                    err_msg = u'Обращение создано, но произошла ошибка при сохранении следующих услуг:' \
                              u'<br><br> - %s<br>Свяжитесь с администратором.' % (u'<br> - '.join(errors))
                    result['error_text'] = err_msg
        else:
            try:
                actions, errors = create_services(event.id, services_data, contract_id)
            except Exception, e:
                db.session.rollback()
                logger.error(u'Ошибка сохранения услуг для обращения %s: %s' % (event.id, e), exc_info=True)
                raise EventSaveException(u'Ошибка сохранения услуг', {
                    'ext_msg': u'Свяжитесь с администратором.'
                })
            else:
                if errors:
                    err_msg = u'<br><br> - %s<br>Свяжитесь с администратором.' % (
                        u'<br> - '.join(errors)
                    )
                    raise EventSaveException(u'Произошла ошибка при сохранении следующих услуг', {
                        'ext_msg': err_msg
                    })

    return result


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


def check_existing_open_events(client_id, request_type_kind):
    """Проверить, есть для данного пациента открытые ИБ или обращения.

    Для стационарных ИБ (request_type_kind = 'stationary') открытым считается Event, у которого нет
    даты окончания + последнее движение либо не имеет даты окончания, либо имеет дату окончания,
    но поле 'Переведен в отделение' имеет непустое значение.
    Для поликлинических обращений (request_type_kind = 'policlinic') открытым считается Event, у которого нет
    даты окончания.

    :returns True если имеются открытые Event, иначе False
    """
    from_ = join(
        Event, EventType,
        Event.eventType_id == EventType.id
    ).join(
        rbRequestType, EventType.requestType_id == rbRequestType.id
    )
    request_type_codes = []
    if request_type_kind == 'stationary':
        request_type_codes = STATIONARY_EVENT_CODES

        # самая поздняя дата движения для каждого обращения пациента
        q_action_begdates = db.session.query(Action).join(
            Event, EventType, rbRequestType, ActionType,
        ).filter(
            Event.deleted == 0, Action.deleted == 0, rbRequestType.code.in_(request_type_codes),
            ActionType.flatCode == STATIONARY_MOVING_CODE, Event.client_id == client_id
        ).with_entities(
            func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
        ).group_by(
            Event.id
        ).subquery('MaxActionBegDates')

        # самое позднее движение (включая уже и дату и id, если даты совпадают) для каждого обращения пациента
        q_latest_movings = db.session.query(Action).join(
            q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                    q_action_begdates.c.event_id == Action.event_id)
        ).with_entities(
            func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
        ).group_by(
            Action.event_id
        ).subquery('EventLatestMovings')

        # значения полей Переведен в отделение для всех движений, всех обращений пациента
        q_transfer_os = db.session.query(Action).join(
            Event, ActionType, ActionProperty, ActionPropertyType
        ).outerjoin(
            ActionProperty_OrgStructure
        ).filter(
            Action.deleted == 0, ActionProperty.deleted == 0, ActionType.flatCode == STATIONARY_MOVING_CODE,
            ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE, Event.client_id == client_id
        ).with_entities(
            Action.id.label('action_id'), ActionProperty_OrgStructure.value_.label('os_id')
        ).subquery('MovingTransferOs')

        # итого: самое позднее движение и значение поля Переведен в отделение
        q_latest_movings_os = db.session.query(Action).join(
            q_latest_movings, q_latest_movings.c.action_id == Action.id
        ).outerjoin(
            q_transfer_os, q_transfer_os.c.action_id == Action.id
        ).with_entities(
            Action.id.label('action_id'), Action.event_id.label('event_id'),
            Action.begDate.label('beg_date'), Action.endDate.label('end_date'),
            q_transfer_os.c.os_id.label('os_id')
        ).subquery('EventLatestMovingsOs')

        from_ = from_.outerjoin(
            q_latest_movings_os, Event.id == q_latest_movings_os.c.event_id
        )
    elif request_type_kind == 'policlinic':
        request_type_codes = POLICLINIC_EVENT_CODES
    else:
        raise ValueError('unknown `request_type_kind`')

    result = exists().select_from(
        from_
    ).where(
        rbRequestType.code.in_(request_type_codes)
    ).where(
        Event.client_id == client_id
    ).where(
        Event.execDate.is_(None)
    )
    if request_type_kind == 'stationary':
        result = result.where(
            or_(
                q_latest_movings_os.c.end_date.is_(None),
                and_(q_latest_movings_os.c.os_id.isnot(None),
                     q_latest_movings_os.c.os_id != 0)
            )
        )
    return db.session.query(result).scalar()
