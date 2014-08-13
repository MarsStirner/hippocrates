# -*- coding: utf-8 -*-

import requests

from collections import defaultdict
from datetime import datetime, time, timedelta
from flask.ext.login import current_user

from config import VESTA_URL
from application.systemwide import db
from application.app import cache
from application.lib.utils import logger, get_new_uuid
from application.models.actions import Action, ActionType, ActionPropertyType, ActionProperty, Job, JobTicket, \
    TakenTissueJournal, ActionType_TissueType
from application.models.exists import Person
from application.models.event import Event
from application.models.enums import ActionStatus
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


def create_action(action_type_id, event_id, src_action=None, assigned=None, data=None):
    """
    Базовое создание действия, например для отправки клиентской стороне.

    :param action_type_id: action_type_id int
    :param event_id: event_id int
    :param src_action: другое действие Action, из которого будут браться данные
    :param assigned: список id ActionPropertyType, которые должны быть отмечены назначенными
    :param data: словарь с данными для установки произвольных параметров действия
    :return: Action model
    """
    # TODO: transfer some checks from ntk
    if not action_type_id or not event_id:
        raise AttributeError

    now = datetime.now()
    now_date = now.date()
    actionType = ActionType.query.get(int(action_type_id))
    event = Event.query.get(int(event_id))
    current_user_p = Person.query.get(current_user.get_id())

    action = Action()
    action.actionType = actionType
    action.event = event
    action.event_id = event.id  # need for now
    action.begDate = now  # todo
    action.setPerson = current_user_p
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.status = actionType.defaultStatus
    action.account = 0
    action.uet = 0  # TODO: calculate UET

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

    if src_action:
        action.person = src_action.person
    elif actionType.defaultExecPerson_id:
        action.person = Person.query.get(actionType.defaultExecPerson_id)
    elif actionType.defaultPersonInEvent == DP_UNDEFINED:
        action.person = None
    elif actionType.defaultPersonInEvent == DP_SET_PERSON:
        action.person = action.setPerson
    elif actionType.defaultPersonInEvent == DP_EVENT_EXEC_PERSON:
        action.person = event.execPerson
    elif actionType.defaultPersonInEvent == DP_CURRENT_USER:
        action.person = current_user_p

    action.plannedEndDate = get_planned_end_datetime(action_type_id)
    action.uuid = get_new_uuid()

    # set changed attributes
    if data:
        for field, value in data.items():
            if field in Action.__table__.columns:
                setattr(action, field, value)

    # properties
    if assigned is None:
        assigned = []
    src_props = dict((prop.type_id, prop) for prop in src_action.properties) if src_action else {}
    prop_types = actionType.property_types.filter(ActionPropertyType.deleted == 0)
    for prop_type in prop_types:
        if recordAcceptableEx(event.client.sexCode, event.client.age_tuple(now_date), prop_type.sex, prop_type.age):
            prop = ActionProperty()
            prop.type = prop_type
            prop.action = action
            prop.isAssigned = prop_type.id in assigned
            prop.value = src_props[prop_type.id].value if src_props.get(prop_type.id) else None
            action.properties.append(prop)

    return action


def create_new_action(action_type_id, event_id, src_action=None, assigned=None, data=None):
    """
    Создание действия для сохранения в бд.

    :param action_type_id: action_type_id int
    :param event_id: event_id int
    :param src_action: другое действие Action, из которого будут браться данные
    :param assigned: список id ActionPropertyType, которые должны быть отмечены назначенными
    :param data: словарь с данными для установки произвольных параметров действия
    :return: Action model
    """
    action = create_action(action_type_id, event_id, src_action, assigned, data)

    org_structure = action.event.current_org_structure
    if action.actionType.isRequiredTissue and org_structure:
        os_id = org_structure.id
        for prop in action.properties:
            if prop.type.typeName == 'JobTicket':
                prop.value = create_JT(action, os_id)

    return action


def create_JT(action, orgstructure_id):
    """
    Создание JobTicket для лабораторного исследования

    :param action: Action
    :param orgstructure_id:
    :return: JobTicket
    """
    planned_end_date = action.plannedEndDate
    job_type_id = action.actionType.jobType_id
    jt_date = planned_end_date.date()
    jt_time = planned_end_date.time()
    client_id = action.event.client_id
    at_tissue_type = action.actionType.tissue_type
    if at_tissue_type is None:
        raise Exception(u'Неверно настроены параметры биозаборов для создания лабораторных исследований.')

    job = Job.query.filter(
        Job.jobType_id == job_type_id,
        Job.date == jt_date,
        Job.orgStructure_id == orgstructure_id,
        Job.begTime <= jt_time,
        Job.endTime >= jt_time
    ).first()
    if not job:
        job = Job()
        job.date = jt_date
        job.begTime = '00:00:00'
        job.endTime = '23:59:59'
        job.jobType_id = job_type_id
        job.orgStructure_id = orgstructure_id
        job.quantity = 100
        db.session.add(job)
    ttj = TakenTissueJournal.query.filter(
        TakenTissueJournal.client_id == client_id,
        TakenTissueJournal.tissueType_id == at_tissue_type.tissueType_id,
        TakenTissueJournal.datetimeTaken == planned_end_date
    ).first()
    if not ttj:
        ttj = TakenTissueJournal()
        ttj.client_id = client_id
        ttj.tissueType_id = at_tissue_type.tissueType_id
        ttj.amount = at_tissue_type.amount
        ttj.unit_id = at_tissue_type.unit_id
        ttj.datetimeTaken = planned_end_date
        ttj.externalId = action.event.externalId
        db.session.add(ttj)
    jt = JobTicket()
    jt.job = job
    jt.datetime = planned_end_date
    db.session.add(jt)
    return jt


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


@cache.memoize(86400)
def get_kladr_city(code):
    if len(code) == 13:  # убрать после конвертации уже записанных кодов кладр
        code = code[:-2]
    result = dict()
    try:
        response = requests.get(u'{0}kladr/city/{1}/'.format(VESTA_URL, code))
    except (requests.ConnectionError, requests.exceptions.MissingSchema):
        # log
        pass
    else:
        city = response.json().get('data')
        if city:
            result = city[0]
            result['code'] = result['identcode']
            result['fullname'] = result['name'] = u'{0}. {1}'.format(result['shorttype'], result['name'])
            if result['parents']:
                for parent in result['parents']:
                    result['fullname'] = u'{0}, {1}. {2}'.format(result['fullname'], parent['shorttype'], parent['name'])
                del result['parents']
    return result


@cache.memoize(86400)
def get_kladr_street(code):
    if len(code) == 17:  # убрать после конвертации уже записанных кодов кладр
        code = code[:-2]
    data = dict()
    try:
        response = requests.get(u'{0}kladr/street/{1}/'.format(VESTA_URL, code))
    except (requests.ConnectionError, requests.exceptions.MissingSchema):
        # log
        pass
    else:
        street = response.json().get('data')
        if street:
            data = street[0]
            data['code'] = data['identcode']
            data['name'] = u'{0} {1}'.format(data['fulltype'], data['name'])
    return data


@cache.memoize(86400)
def get_apt_assignable_small_info():
    at_apts = defaultdict(list)
    raw = db.text(
        ur'''SELECT ActionPropertyType.actionType_id, ActionPropertyType.id, ActionPropertyType.name
        FROM ActionPropertyType
        JOIN ActionType ON ActionPropertyType.actionType_id = ActionType.id
        WHERE ActionType.isRequiredTissue = 1 AND ActionPropertyType.isAssignable != 0 AND
        ActionPropertyType.deleted = 0 AND ActionType.deleted = 0 AND ActionType.hidden = 0'''
    )
    map(lambda (at_id, apt_id, apt_name): at_apts[at_id].append((apt_id, apt_name)),
        db.session.execute(raw)
    )
    return at_apts