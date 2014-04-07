# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from application.models.exists import Client

# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
def index():
    try:
        return render_template('schedule/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/doctors/')
def doctors():
    try:
        return render_template('schedule/doctors.html')
    except TemplateNotFound:
        abort(404)


@module.route('/appointment/')
def appointment():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    return render_template(
        'schedule/person_appointment.html',
        client=client
    )


@module.route('/person_month/')
def person_schedule_monthview():
    try:
        return render_template('schedule/person_schedule_monthview.html')
    except TemplateNotFound:
        abort(404)


@module.route('/day_free.html')
def html_day_free():
    return render_template('schedule/day_free.html')

@module.route('/event.html')
def html_event_info():
    # event_id = int(request.args['event_id'])
    return render_template(
        'schedule/event_info.html'
    )


@module.route('/event_new.html')
def new_event():
    return render_template('schedule/client_event/new_event.html')


@module.route('/action.html')
def html_action():
    return render_template(
        'schedule/action.html'
    )
