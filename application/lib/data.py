# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import requests

from config import VESTA_URL
from application.systemwide import db
from application.lib.utils import logger, get_new_uuid
from application.models.actions import Action, ActionType, ActionPropertyType, ActionProperty
from application.models.exists import Person, UUID
from application.models.event import Event
from application.lib.agesex import recordAcceptableEx
from application.lib.calendar import calendar

# планируемая дата выполнения (default planned end date)
DPED_UNDEFINED = 0  # Не определено
DPED_NEXT_DAY = 1  # Следующий день
DPED_NEXT_WORK_DAY = 2  # Следедующий рабочий день
DPED_CURRENT_DAY = 3  # Текущий день

# дата выполнения (default end date)
DED_UNDEFINED = 0
DED_CURRENT_DATE = 1
DED_EVENT_SET_DATE = 2
DED_EVENT_EXEC_DATE = 3

# дата назначения (default direction date)
DDD_UNDEFINED = 0
DDD_EVENT_SET_DATE = 1
DDD_CURRENT_DATE = 2
DDD_ACTION_EXEC_DATE = 3

# ответственный
DP_UNDEFINED = 0
DP_EMPTY = 1
DP_SET_PERSON = 2
DP_EVENT_EXEC_PERSON = 3
DP_CURRENT_USER = 4


def create_action(event_id, action_type_id, current_user_id, data):
    if not event_id or not action_type_id:
        raise AttributeError

    now = datetime.now()
    actionType = ActionType.query.get(int(action_type_id))
    event = Event.query.get(int(event_id))
    _current_user = Person.query.get(int(current_user_id))

    action = Action()
    action.actionType_id = action_type_id
    action.event_id = event_id
    action.createDatetime = action.modifyDatetime = action.begDate = now
    action.createPerson_id = action.modifyPerson_id = action.setPerson_id = current_user_id
    action.office = actionType.office or u''
    # action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.amount = 1
    action.status = 0
    action.note = ''
    action.payStatus = 0
    action.account = 0
    action.coordText = ''
    action.AppointmentType = 0
    action.uuid = get_new_uuid()

    if actionType.defaultEndDate == DED_CURRENT_DATE:
        action.endDate = now
    elif actionType.defaultEndDate == DED_EVENT_SET_DATE:
        action.endDate = event.setDate
    elif actionType.defaultEndDate == DED_EVENT_EXEC_DATE:
        action.endDate = event.execDate

    if actionType.defaultDirectionDate == DDD_EVENT_SET_DATE:
        action.directionDate = event.setDate
    elif actionType.defaultDirectionDate == DDD_CURRENT_DATE:
        action.directionDate = now
    elif actionType.defaultDirectionDate == DDD_ACTION_EXEC_DATE and action.endDate:
        action.directionDate = max(action.endDate, event.setDate)
    else:
        action.directionDate = event.setDate

    if actionType.defaultExecPerson_id:
        action.person = Person.query.get(actionType.defaultExecPerson_id)
    elif actionType.defaultPersonInEvent == DP_UNDEFINED:
        action.person = None
    elif actionType.defaultPersonInEvent == DP_SET_PERSON:
        action.person = action.setPerson
    elif actionType.defaultPersonInEvent == DP_EVENT_EXEC_PERSON:
        action.person = event.execPerson
    elif actionType.defaultPersonInEvent == DP_CURRENT_USER:
        action.person = _current_user

    action.plannedEndDate = get_planned_end_datetime(action_type_id)

    for field, value in data.items():
        if field in Action.__table__.columns:  # and not getattr(action, field):
            setattr(action, field, value)

    prop_types = actionType.property_types.filter(ActionPropertyType.deleted == 0)
    now_date = now.date()
    for prop_type in prop_types:
        if recordAcceptableEx(event.client.sex, event.client.age_tuple(now_date), prop_type.sex, prop_type.age):
            prop = ActionProperty()
            prop.type = prop_type
            prop.action = action
            prop.createDatetime = prop.modifyDatetime = now
            prop.norm = ''
            prop.evaluation = ''
            prop.createPerson_id = prop.modifyPerson_id = int(data.get('person_id', 1))
            db.session.add(prop)

    db.session.add(action)

    try:
        db.session.commit()
    except Exception, e:
        logger.error(e)
        db.session.rollback()
    else:
        return action
    return None


def isRedDay(date):
    holidays = calendar.getList()
    holiday = False
    for hol in holidays:
        break
    return date.isoweekday() > 5 or holiday


def addPeriod(startDate, length, countRedDays):
    u"""Добавление к некоторой дате некоторого периода в днях.
    Сама дата, к которой идет прибавление дней, уже считается как целый день,
    кроме случая, когда она является выходным или праздником. При передаче
    False аргументу countRedDays при добавлении периода будут учитываться
    только рабочие дни (не выходные и не праздники).

    args:
    startDate -- начальная дата
    length -- число дней для добавления
    countRedDays -- считать или нет выходные и праздники

    """
    if isinstance(startDate, datetime):
        savedTime = startDate.time()
        startDate = startDate.date()
    else:
        savedTime = None

    if countRedDays:
        result_date = startDate + timedelta(days=length-1)
    else:
        current_date = startDate
        # если начальная дата не рабочий день, то она не должна учитываться
        while isRedDay(current_date):
            current_date = current_date + timedelta(days=1)
        days_count = length - 1  # не считая текущий
        if days_count < 0:
            current_date = startDate + timedelta(days=-1)
        while days_count > 0:
            current_date = current_date + timedelta(days=1)
            if not isRedDay(current_date):
                days_count -= 1
        result_date = current_date
    if savedTime:
        result_date = datetime.combine(result_date, savedTime)
    return result_date


def get_planned_end_datetime(action_type_id):
    """Получение планируемого времени для действия
    @param actionType_id: тип действия
    @return: дата, время понируемого действия
    @rtype 2-tuple"""
    now = datetime.now()
    current_date = now.date()
    action_type = ActionType.query.get(int(action_type_id))

    defaultPlannedEndDate = action_type.defaultPlannedEndDate
    currentDate = datetime.now()
    if defaultPlannedEndDate == DPED_UNDEFINED:
        plannedEndDate = None
    elif defaultPlannedEndDate == DPED_NEXT_DAY:
        plannedEndDate = addPeriod(currentDate, 2, True)
    elif defaultPlannedEndDate == DPED_NEXT_WORK_DAY:
        plannedEndDate = addPeriod(currentDate, 2, False)
    elif defaultPlannedEndDate == DPED_CURRENT_DAY:
        plannedEndDate = current_date
    else:
        plannedEndDate = None

    plannedEndTime = None
    if plannedEndDate:
        if defaultPlannedEndDate < DPED_CURRENT_DAY:
            plannedEndTime = time(7, 0)
        elif defaultPlannedEndDate == DPED_CURRENT_DAY:
            cur_hour = now.hour
            if cur_hour == 23:
                plannedEndTime = time(23, 59)
            else:
                plannedEndTime = time(cur_hour + 1, 0)
    if plannedEndDate is None:
        plannedEndDate = current_date
    if plannedEndTime is None:
        plannedEndTime = time(7, 0)
    return datetime.combine(plannedEndDate, plannedEndTime)


def get_kladr_city(code):
    result = dict()
    response = requests.get(u'{0}/kladr/city/{1}/'.format(VESTA_URL, code))
    city = response.json()['data']
    if city:
        result = city[0]
        result['code'] = result['identcode']
        result['name'] = u'{0}. {1}'.format(result['shorttype'], result['name'])
    return result


def get_kladr_street(code):
    data = dict()
    response = requests.get(u'{0}/kladr/street/{1}/'.format(VESTA_URL, code))
    street = response.json()['data']
    if street:
        data = street[0]
        data['code'] = data['identcode']
        data['name'] = u'{0} {1}'.format(data['fulltype'], data['name'])
    return data