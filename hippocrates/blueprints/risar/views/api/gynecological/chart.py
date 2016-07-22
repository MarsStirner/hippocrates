# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.chart_creator import GynecologicCardCreator
from hippocrates.blueprints.risar.lib.represent.common import represent_header, represent_chart_for_close_event
from hippocrates.blueprints.risar.lib.represent.gyn import represent_gyn_event
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_chart_for_routing
from hippocrates.blueprints.risar.risar_config import request_type_gynecological
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_datetime
from nemesis.models.event import Event
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'

_base = '/api/0/gyn/'


@module.route(_base, methods=['GET'])
@module.route(_base + '<int:event_id>', methods=['GET'])
@api_method
def api_0_gyn_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = GynecologicCardCreator(client_id, ticket_id, event_id)
    try:
        chart_creator()
        return represent_gyn_event(chart_creator.event)
    except GynecologicCardCreator.DoNotCreate:
        raise ApiException(200, 'Must explicitly create event first')


@module.route(_base, methods=['POST'])
@api_method
def api_0_gyn_chart_create():
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = GynecologicCardCreator(client_id, ticket_id)
    chart_creator(create=True)
    return dict(
        represent_gyn_event(chart_creator.event),
        automagic=chart_creator.automagic,
    )


@module.route(_base + '<int:event_id>/mini', methods=['GET'])
@api_method
def api_0_gyn_chart_mini(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != request_type_gynecological:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'header': represent_header(event),
        'chart': represent_chart_for_routing(event)
    }


@module.route('/api/0/gyn/chart-by-ticket/<int:ticket_id>', methods=['DELETE'])
@api_method
def api_0_gyn_chart_delete(ticket_id):
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


@module.route('/api/0/chart_close/')
@module.route('/api/0/chart_close/<int:event_id>', methods=['POST'])
@api_method
def api_0_gyn_chart_close(event_id=None):
    if not event_id:
        raise ApiException(400, u'Either event_id must be provided')
    else:
        event = Event.query.get(event_id)
        data = request.get_json()
        if data.get('cancel'):
            event.execDate = None
            event.manager_id = None
        else:
            event.execDate = safe_datetime(data['exec_date'])
            event.manager_id = data['manager']['id']
        db.session.commit()
    return represent_chart_for_close_event(event)



