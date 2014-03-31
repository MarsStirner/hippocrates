# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from application.models.exists import Client

# noinspection PyUnresolvedReferences
from . import api_html, api_json


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


@module.route('/appointment/')
@public_endpoint
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
@public_endpoint
def person_schedule_monthview():
    try:
        return render_template('schedule/person_schedule_monthview.html')
    except TemplateNotFound:
        abort(404)


@module.route('/day_free.html')
@public_endpoint
def html_day_free():
    return render_template('schedule/day_free.html')

@module.route('/event.html')
@public_endpoint
def html_event_info():
    # event_id = int(request.args['event_id'])
    return render_template(
        'schedule/event_info.html'
    )

@module.route('/action.html')
@public_endpoint
def html_action():
    return render_template(
        'schedule/action.html'
    )
