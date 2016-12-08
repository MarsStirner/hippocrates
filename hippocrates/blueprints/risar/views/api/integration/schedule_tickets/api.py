# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import ScheduleTicketsXForm, ScheduleTicketXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/schedule_tickets/schedule_tickets.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule_tickets_schema(api_version):
    return ScheduleTicketsXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/schedule_tickets/<hospital_code>/<doctor_code>/')
@api_method(hook=hook)
def api_schedule_tickets_get(api_version, hospital_code, doctor_code):
    args = request.args.to_dict()
    xform = ScheduleTicketsXForm(api_version)
    xform.init_and_check_params(hospital_code, doctor_code)
    xform.find_tickets(**args)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/schedule_tickets/schedule_ticket.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule_ticket_schema(api_version):
    return ScheduleTicketXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/schedule_tickets/', methods=["POST"])
@module.route('/api/integration/<int:api_version>/schedule_tickets/<schedule_ticket_id>', methods=["PUT"])
@api_method(hook=hook)
def api_schedule_ticket_save(api_version, schedule_ticket_id=None):
    data = request.get_json()
    create = request.method == 'POST'

    xform = ScheduleTicketXForm(api_version, create)
    xform.validate(data)
    xform.check_params(schedule_ticket_id, None, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/schedule_tickets/<schedule_ticket_id>', methods=["DELETE"])
@api_method(hook=hook)
def api_schedule_ticket_delete(api_version, schedule_ticket_id):
    xform = ScheduleTicketXForm(api_version)
    xform.check_params(schedule_ticket_id)
    xform.delete_target_obj()
    xform.store()

