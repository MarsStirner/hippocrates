# -*- coding: utf-8 -*-
import collections
import datetime
import itertools

from flask import request

from application.lib.apiutils import api_method
from application.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_String
from application.models.event import Event
from application.models.schedule import Schedule
from application.models.utils import safe_current_user_id
from application.systemwide import db
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
        (ActionProperty_String.value,),
        whereclause=db.and_(
            ActionType.flatCode == 'cardAttributes',
            ActionPropertyType.code == 'prenatal_risk_572',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_String.id == ActionProperty.id,
            Event.execDate.is_(None),
        ),
        from_obj=(
            Event, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_String
        ))
    # query = Event.query.\
    #     join(Action, ActionProperty).\
    #     join(ActionType, onCond=(ActionType.flatCode == 'cardAttributes')).\
    #     join(ActionPropertyType, onCond=db.and_(ActionPropertyType.id == ActionProperty.type_id, ActionPropertyType.code == 'prenatal_risk_572')).\
    #     join(ActionProperty_String).\
    #     filter(Event.execDate.is_(None))

    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result