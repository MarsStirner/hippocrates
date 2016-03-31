# -*- coding: utf-8 -*-
import datetime
import itertools

from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.models.schedule import Schedule
from nemesis.models.utils import safe_current_user_id
from blueprints.risar.app import module
from blueprints.risar.lib.represent import represent_ticket
from nemesis.systemwide import db
from nemesis.models.event import Event
from nemesis.models.schedule import ScheduleTicket, ScheduleClientTicket
from sqlalchemy import or_, and_
from sqlalchemy import func

__author__ = 'mmalkov'


@module.route('/api/0/schedule/')
@module.route('/api/0/schedule/<int:person_id>')
@api_method
def api_0_schedule(person_id=None):
    all_tickets = bool(request.args.get('all', False))
    if not person_id:
        person_id = safe_current_user_id()
    for_date = request.args.get('date', datetime.date.today())

    sq = db.session.query(
        Event.client_id,
        func.max(Event.id).label('max_id')
    ).select_from(Event).filter(
        Event.execDate == None,
    ).group_by(Event.client_id).subquery('sq')

    query = db.session.query(ScheduleTicket, Event).join(
        Schedule
    ).outerjoin(
        ScheduleClientTicket
    ).filter(
        or_(
            and_(ScheduleClientTicket.event_id.isnot(None),
                 Event.id == ScheduleClientTicket.event_id),
            and_(ScheduleClientTicket.event_id.is_(None),
                 Event.id == (sq.c.max_id))
        ),
        ScheduleClientTicket.client_id == sq.c.client_id,
        Schedule.date == for_date,
        Schedule.person_id == person_id,
        ScheduleTicket.deleted == 0,
        ScheduleClientTicket.deleted == 0,
        Event.execDate == None,
    )
    if not all_tickets:
        query = query.filter(ScheduleClientTicket.id.isnot(None))
    ticket_event_list = query.all()

    return map(represent_ticket, ticket_event_list)
