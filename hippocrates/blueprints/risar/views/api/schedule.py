# -*- coding: utf-8 -*-
import collections
import datetime
import itertools

from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_Integer
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