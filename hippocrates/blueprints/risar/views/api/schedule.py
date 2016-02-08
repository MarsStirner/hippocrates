# -*- coding: utf-8 -*-
import datetime
import itertools

from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.models.schedule import Schedule
from nemesis.models.utils import safe_current_user_id
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