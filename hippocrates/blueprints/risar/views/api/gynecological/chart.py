# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.chart_creator import GynecologicCardCreator
from hippocrates.blueprints.risar.lib.represent.gyn import represent_gyn_event
from nemesis.lib.apiutils import api_method, ApiException

__author__ = 'viruzzz-kun'


@module.route('/api/1/gynecological/chart/', methods=['GET'])
@module.route('/api/1/gynecological/chart/<int:event_id>', methods=['GET'])
@api_method
def api_1_gyn_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = GynecologicCardCreator(client_id, ticket_id, event_id)
    try:
        chart_creator()
        return represent_gyn_event(chart_creator.event)
    except GynecologicCardCreator.DoNotCreate:
        raise ApiException(404, 'Must explicitly create event first')


@module.route('/api/1/gynecological/chart/', methods=['POST'])
@api_method
def api_1_gyn_chart_create():
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = GynecologicCardCreator(client_id, ticket_id)
    chart_creator(create=True)
    return dict(
        represent_gyn_event(chart_creator.event),
        automagic=chart_creator.automagic,
    )


