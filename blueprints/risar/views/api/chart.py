# -*- coding: utf-8 -*-
from flask import request
from application.lib.utils import jsonify, get_new_event_ext_id
from application.models.client import Client
from application.models.enums import EventPrimary, EventOrder
from application.models.event import Event, EventType
from application.models.exists import Organisation, Person
from application.models.schedule import ScheduleClientTicket
from application.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.represent import represent_event
from config import ORGANISATION_INFIS_CODE

__author__ = 'mmalkov'


@module.route('/api/0/chart/ticket/', methods=['DELETE'])
@module.route('/api/0/chart/ticket/<int:ticket_id>', methods=['DELETE'])
def api_0_chart_delete(ticket_id):
    # TODO: Security
    ticket = ScheduleClientTicket.query.get(ticket_id)
    if not ticket:
        return jsonify(None, 404, 'Ticket not found')
    if not ticket.event:
        return jsonify(None, 404, 'Event not found')
    if ticket.event.deleted:
        return jsonify(None, 400, 'Event already deleted')
    ticket.event.deleted = 1
    ticket.event = None
    db.session.commit()
    return jsonify(None)


@module.route('/api/0/chart/')
@module.route('/api/0/chart/<int:event_id>')
def api_0_chart(event_id=None):
    automagic = False
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
            event.eventType = EventType.get_default_et()  # FIXME: Risar has different EventType
            event.organisation = Organisation.query.filter_by(infisCode=str(ORGANISATION_INFIS_CODE)).first()
            event.isPrimaryCode = EventPrimary.primary[0]
            event.order = EventOrder.planned[0]

            client_id = ticket.client_id
            setDate = ticket.ticket.begDateTime
            note = ticket.note
            exec_person_id = ticket.ticket.schedule.person_id
            event.execPerson_id = exec_person_id
            event.execPerson = Person.query.get(exec_person_id)
            event.orgStructure = event.execPerson.org_structure
            event.client = Client.query.get(client_id)
            event.setDate = setDate
            event.note = note
            event.externalId = get_new_event_ext_id(event.eventType.id, ticket.client_id)
            event.payStatus = 0
            db.session.add(event)
            ticket.event = event
            db.session.add(ticket)
            db.session.commit()
            automagic = True
    else:
        event = Event.query.get(event_id)
        if not event:
            return jsonify(None, result_code=404, result_name='Event not found')
    return jsonify({
        'event': represent_event(event),
        'automagic': automagic
    })