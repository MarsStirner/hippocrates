# -*- encoding: utf-8 -*-
import datetime
import json

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from ..app import module
from application.lib.utils import public_endpoint
from blueprints.schedule.models.exists import Person, Client
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer, MyJsonEncoder, ClientVisualizer


@module.route('/')
@public_endpoint
def index():
    try:
        return render_template('schedule/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/doctors/')
@public_endpoint
def doctors():
    try:
        return render_template('schedule/doctors.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patients/')
@public_endpoint
def patients():
    try:
        return render_template('schedule/patients.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patient_info/')
@public_endpoint
def patient_info():
    try:
        return render_template('schedule/patient_info.html')
    except TemplateNotFound:
        abort(404)


@module.route('/api/schedule.json')
@public_endpoint
def api_schedule():
    try:
        person_id = int(request.args['person_id'])
        person = Person.query.get(person_id)
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
        attendance_type = request.args.get('attendance_type')
    except KeyError or ValueError:
        return abort(404)
    schedules = Schedule.query.\
        filter(Schedule.person_id == person_id).\
        filter(month_f <= Schedule.date).\
        filter(Schedule.date <= month_l).\
        order_by(Schedule.date)
    context = ScheduleVisualizer()
    context.push_all(schedules, month_f, month_l)
    return json.dumps({
        'schedule': context.schedule,
        'max_tickets': context.max_tickets,
        'person': context.make_person(person),
    }, cls=MyJsonEncoder)


@module.route('/api/patient.json')
@public_endpoint
def api_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    context = ClientVisualizer()
    return json.dumps({
        'clientData': context.make_client_info(client),
        'records': context.make_records(client),
    }, cls=MyJsonEncoder)