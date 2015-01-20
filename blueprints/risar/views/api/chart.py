# -*- coding: utf-8 -*-
from datetime import datetime

from flask import request

from application.lib.data import create_action
from application.lib.utils import get_new_event_ext_id, safe_traverse
from application.lib.apiutils import api_method, ApiException
from application.models.actions import ActionType
from application.models.client import Client, ClientAttach
from application.models.enums import EventPrimary, EventOrder
from application.models.event import Event, EventType
from application.models.exists import Organisation, Person, rbAttachType, rbRequestType, rbFinance
from application.models.schedule import ScheduleClientTicket
from application.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.represent import represent_event
from blueprints.risar.risar_config import attach_codes


__author__ = 'mmalkov'


@module.route('/api/0/chart/ticket/', methods=['DELETE'])
@module.route('/api/0/chart/ticket/<int:ticket_id>', methods=['DELETE'])
@api_method
def api_0_chart_delete(ticket_id):
    # TODO: Security
    ticket = ScheduleClientTicket.query.get(ticket_id)
    if not ticket:
        raise ApiException(404, 'Ticket not found')
    if not ticket.event:
        raise ApiException(404, 'Event not found')
    if ticket.event.deleted:
        raise ApiException(400, 'Event already deleted')
    ticket.event.deleted = 1
    ticket.event = None
    db.session.commit()


def default_ET_Heuristic():
    return EventType.query \
        .join(rbRequestType, rbFinance) \
        .filter(
            rbRequestType.code == 'pregnancy',  # Случай беременности
            rbFinance.code == '2',  # ОМС
            EventType.deleted == 0,
        ) \
        .order_by(EventType.createDatetime.desc())\
        .first()


def default_AT_Heuristic():
    return ActionType.query.filter(ActionType.flatCode == 'cardAttributes').first()


@module.route('/api/0/chart/')
@module.route('/api/0/chart/<int:event_id>')
@api_method
def api_0_chart(event_id=None):
    automagic = False
    ticket_id = request.args.get('ticket_id')
    if not event_id and not ticket_id:
        raise ApiException(400, u'Either event_id or ticket_id must be provided')
    if ticket_id:
        ticket = ScheduleClientTicket.query.get(ticket_id)
        if not ticket:
            raise ApiException(404, 'ScheduleClientTicket not found')
        event = ticket.event
        if not event:
            event = Event()
            at = default_AT_Heuristic()
            if not at:
                raise ApiException(500, u'Нет типа действия с flatCode = cardAttributes')
            ext = create_action(at.id, event)
            ET = default_ET_Heuristic()
            if ET is None:
                raise ApiException(500, u'Не настроен тип события - Случай беременности ОМС')
            event.eventType = ET

            exec_person_id = ticket.ticket.schedule.person_id
            exec_person = Person.query.get(exec_person_id)
            event.execPerson = exec_person
            event.orgStructure = exec_person.org_structure
            event.organisation = exec_person.organisation

            event.isPrimaryCode = EventPrimary.primary[0]
            event.order = EventOrder.planned[0]

            client_id = ticket.client_id
            setDate = ticket.ticket.begDateTime
            note = ticket.note
            event.client = Client.query.get(client_id)
            event.setDate = setDate
            event.note = note
            event.externalId = get_new_event_ext_id(event.eventType.id, ticket.client_id)
            event.payStatus = 0
            db.session.add(event)
            db.session.add(ext)
            ticket.event = event
            db.session.add(ticket)
            db.session.commit()
            automagic = True
    else:
        event = Event.query.get(event_id)
        if not event:
            raise ApiException(404, 'Event not found')
    return {
        'event': represent_event(event),
        'automagic': automagic
    }


@module.route('/api/0/chart/attach_lpu/', methods=['POST'])
@api_method
def api_0_attach_lpu():
    client_id = request.args.get('client_id', None)
    if client_id is None:
        raise ApiException(400, 'Client is not set')
    data = request.get_json()

    result = {}
    for attach_type in data:
        attach_lpu = data[attach_type]
        if attach_lpu:
            if attach_lpu.get('id') is None:
                obj = ClientAttach()
            else:
                obj = ClientAttach.query.get(attach_lpu['id'])
                if obj is None:
                    raise ApiException(404, 'Attach not found')

            obj.client_id = client_id
            obj.attachType = rbAttachType.query.filter(rbAttachType.code == attach_codes[attach_type]).first()
            obj.org = Organisation.query.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.begDate = datetime.now()
            db.session.add(obj)
            result[attach_type] = obj
    db.session.commit()
    return result


@module.route('/api/1/chart/attach_lpu/', methods=['POST'])
@api_method
def api_1_attach_lpu():
    # Оптимизированная версия
    # TODO: проверить работоспособность
    client_id = request.args.get('client_id', None)
    if client_id is None:
        raise ApiException(400, 'Client is not set')
    data = request.get_json()
    now = datetime.now()

    result = {}
    if not data:
        return {}
    orgs = dict(
        (org.id, org)
        for org in Organisation.query.filter(Organisation.id.in_(
            set(safe_traverse(attach_lpu, 'org', 'id') for attach_lpu in data.itervalues())
        ))
    )
    attach_types = dict(
        (at.code, at)
        for at in rbAttachType.query.filter(rbAttachType.code.in_(attach_codes.values()))
    )

    for attach_type, attach_lpu in data.iteritems():
        if attach_lpu:
            if attach_lpu.get('id') is None:
                obj = ClientAttach()
            else:
                obj = ClientAttach.query.get(attach_lpu['id'])
                if obj is None:
                    raise ApiException(404, 'Attach not found')

            obj.client_id = client_id
            # rbAttachType.query.filter(rbAttachType.code == attach_codes[attach_type]).first()
            obj.attachType = attach_types.get(attach_codes[attach_type])
            # Organisation.query.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.org = orgs.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.begDate = now
            db.session.add(obj)
            result[attach_type] = obj
    db.session.commit()
    return result