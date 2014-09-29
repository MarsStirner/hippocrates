# -*- coding: utf-8 -*-
import datetime
from flask import request
import itertools
from ..app import module
from application.lib.utils import jsonify, get_new_event_ext_id
from application.models.client import Client
from application.models.enums import EventPrimary, EventOrder
from application.models.event import Event, EventType
from application.models.exists import Organisation, Person
from application.models.schedule import Schedule, ScheduleClientTicket
from application.models.utils import safe_current_user_id
from application.systemwide import db
from blueprints.risar.lib.represent import represent_event
from config import ORGANISATION_INFIS_CODE


__author__ = 'mmalkov'


@module.route('/api/0/schedule/')
@module.route('/api/0/schedule/<int:person_id>')
def api_0_schedule(person_id=None):
    all_tickets = bool(request.args.get('all', False))
    if not person_id:
        person_id = safe_current_user_id()
    for_date = request.args.get('date', datetime.date.today())
    schedule_list = Schedule.query\
        .filter(Schedule.date == for_date, Schedule.person_id == person_id)\
        .order_by(Schedule.begTime).all()
    return jsonify([{
        'schedule_id': ticket.schedule_id,
        'ticket_id': ticket.id,
        'client_ticket_id': ticket.client_ticket.id if ticket.client_ticket else None,
        'client': ticket.client,
        'beg_time': ticket.begDateTime,
        'event_id': ticket.client_ticket.event_id if ticket.client_ticket else None,
        'note': ticket.client_ticket.note if ticket.client else None,
    }
        for ticket in itertools.chain(*(schedule.tickets for schedule in schedule_list))
        if all_tickets or ticket.client_ticket
    ])


@module.route('/api/0/chart/')
@module.route('/api/0/chart/<int:event_id>')
def api_0_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    if not event_id and not ticket_id:
        return jsonify(None, 404, u'Either event_id or ticket_id must be provided')
    if ticket_id:
        ticket = ScheduleClientTicket.query.get(ticket_id)
        if not ticket:
            return jsonify(None, 404, 'ScheduleClientTicket not found')
        event = ticket.event
        if not event:
            event = Event()
            event.eventType = EventType.get_default_et()
            event.organisation = Organisation.query.filter_by(infisCode=str(ORGANISATION_INFIS_CODE)).first()
            event.isPrimaryCode = EventPrimary.primary[0]
            event.order = EventOrder.planned[0]

            client_id = ticket.client_id
            setDate = ticket.ticket.begDateTime
            note = ticket.note
            exec_person_id = ticket.ticket.schedule.person_id
            event.execPerson_id = exec_person_id
            event.execPerson = Person.query.get(exec_person_id)
            event.orgStructure = event.execPerson.OrgStructure
            event.client = Client.query.get(client_id)
            event.setDate = setDate
            event.note = note
            event.externalId = get_new_event_ext_id(event.eventType.id, ticket.client_id)
            event.payStatus = 0
            db.session.add(event)
            ticket.event = event
            db.session.add(ticket)
            db.session.commit()
    else:
        event = Event.query.get(event_id)
        if not event:
            return jsonify(None, result_code=404, result_name='Event not found')
    return jsonify(represent_event(event))
