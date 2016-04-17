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

    # Есть три запроса: все тикеты врача, все незакрытые евенты
    # "случай беременности" и последние незакрытые евенты "случай беременности"
    # сгруппррованные по client_id. Они джойнятся по сложному условию: если
    # ScheduleClientTicket.event_id указывает на кого-нибудь из незакрытых
    # эвентов (первых), то работает такая связка. Если нет (event_id пуст или
    # указывает на неподходящий event), то из последних незакрытых случаев
    # беременности выбирается для данного пациента (если он есть).
    sq = db.session.query(
        func.max(Event.id).label('max_id')
    ).select_from(Event).filter(
        Event.deleted == 0,
        Event.execDate == None,
        ScheduleClientTicket.client_id == Event.client_id,
    ).correlate(ScheduleClientTicket
    ).group_by(Event.client_id)

    query = db.session.query(ScheduleTicket).join(
        Schedule
    ).outerjoin(
        ScheduleClientTicket
    ).outerjoin(
        Event,
        and_(
            Event.deleted == 0,
            Event.execDate == None,
            or_(
                and_(ScheduleClientTicket.event_id.isnot(None),
                     Event.id == ScheduleClientTicket.event_id),
                and_(ScheduleClientTicket.event_id.is_(None),
                     Event.id == sq)
            )
        ),
    ).filter(
        Schedule.date == for_date,
        Schedule.person_id == person_id,
        ScheduleTicket.deleted == 0,
        ScheduleClientTicket.deleted == 0,
    )
    if not all_tickets:
        query = query.filter(ScheduleClientTicket.id.isnot(None))
    ticket_event_ids_list = query.values(ScheduleTicket.id, Event.id)

    return map(represent_ticket, ticket_event_ids_list)
