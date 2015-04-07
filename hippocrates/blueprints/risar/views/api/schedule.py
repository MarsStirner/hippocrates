# -*- coding: utf-8 -*-
import collections
import datetime
import itertools

from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_Integer, \
    ActionProperty_Date, ActionProperty_ExtReferenceRb
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.schedule import Schedule
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.represent import represent_ticket


__author__ = 'mmalkov'


@module.route('/api/0/schedule/')
@module.route('/api/0/schedule/<int:person_id>')
@api_method
def api_0_schedule(person_id=None):
    all_tickets = bool(request.args.get('all', False))
    if not person_id:
        person_id = safe_current_user_id()
    for_date = request.args.get('date', datetime.date.today())
    schedule_list = Schedule.query\
        .filter(Schedule.date == for_date, Schedule.person_id == person_id)\
        .order_by(Schedule.begTime).all()
    return [
        represent_ticket(ticket)
        for ticket in itertools.chain(*(schedule.tickets for schedule in schedule_list))
        if all_tickets or ticket.client_ticket
    ]


@module.route('/api/0/current_stats.json')
@api_method
def api_0_current_stats():
    result = collections.defaultdict(lambda: 0)
    selectable = db.select(
        (ActionProperty_Integer.value_,),
        whereclause=db.and_(
            ActionType.flatCode == 'cardAttributes',
            ActionPropertyType.code == 'prenatal_risk_572',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Integer.id == ActionProperty.id,
            Event.execDate.is_(None),
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ))
    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result


@module.route('/api/0/death_stats.json')
@api_method
def api_0_death_stats():
    # младеньческая смертность
    result = collections.defaultdict(list)
    result1 = collections.defaultdict(dict)
    now = datetime.datetime.now()
    prev = now + datetime.timedelta(days=-now.day)
    dates_conditions = {'current_year': now.strftime('%Y')+'-%',
                        'previous_month': prev.strftime('%Y-%m')+'-%',
                        'current_month': now.strftime('%Y-%m')+'-%'}
    selectable = db.select(
        (Action.id, ActionProperty_Integer.value_),
        whereclause=db.and_(
            ActionType.flatCode == 'risar_newborn_inspection',
            ActionPropertyType.code == 'alive',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Integer.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Integer
        ))
    for (id, value) in db.session.execute(selectable):  # 0-dead, 1-alive
        result[value].append(id)

    for value in result:
        for condition in dates_conditions:
            selectable1 = db.select(
                (Action.id,),
                whereclause=db.and_(
                    ActionType.flatCode == 'risar_newborn_inspection',
                    ActionPropertyType.code == 'birth_date',
                    rbRequestType.code == 'pregnancy',
                    Action.event_id == Event.id,
                    ActionProperty.action_id == Action.id,
                    ActionPropertyType.id == ActionProperty.type_id,
                    ActionType.id == Action.actionType_id,
                    ActionProperty_Date.id == ActionProperty.id,
                    EventType.id == Event.eventType_id,
                    rbRequestType.id == EventType.requestType_id,
                    Event.deleted == 0,
                    Action.deleted == 0,
                    ActionProperty_Date.value.like(dates_conditions[condition]),
                    Action.id.in_(result[value])
                ),
                from_obj=(
                    Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
                    ActionProperty_Date
                ))
            result1[condition][value] = db.session.execute(selectable1).rowcount

    selectable = db.select(
        (Action.id, ),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'death_date',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Date.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            ActionProperty_Date.value.like(now.strftime('%Y')+'-%')
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Date
        ))
    result1['maternal_death'] = db.session.execute(selectable).rowcount
    return result1


@module.route('/api/0/pregnancy_final_stats.json')
@api_method
def api_0_pregnancy_final_stats():
    now = datetime.datetime.now()
    finished_cases = []
    result = collections.defaultdict(lambda: 0)
    selectable = db.select(
        (Action.id, ),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'delivery_date',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Date.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            ActionProperty_Date.value.like(now.strftime('%Y')+'-%')
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Date
        ))
    for (id, ) in db.session.execute(selectable):
        finished_cases.append(id)

    selectable = db.select(
        (ActionProperty_ExtReferenceRb.value_, ),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'pregnancy_final',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_ExtReferenceRb.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            Action.id.in_(finished_cases)
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_ExtReferenceRb
        ))
    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result