# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from ..app import module
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Client
from blueprints.schedule.forms import ClientForm

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


@module.route('/patients/')
@public_endpoint
def patients():
    try:
        return render_template('schedule/patients.html')
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


@module.route('/patient_info/')
@public_endpoint
def patient_info():
    try:
        return render_template('schedule/patient_info.html')
    except TemplateNotFound:
        abort(404)


@module.route('/person_month/')
@public_endpoint
def person_schedule_monthview():
    try:
        return render_template('schedule/person_schedule_monthview.html')
    except TemplateNotFound:
        abort(404)


@module.route('/new_patient/')
@public_endpoint
def new_patient():
    try:
        client = Client()
        client_form = ClientForm()

        return render_template('schedule/new_patient.html', form=client_form)
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
