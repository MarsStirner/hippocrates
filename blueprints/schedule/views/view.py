# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint
from application.models.client import Client
from application.lib.utils import breadcrumb
from blueprints.schedule.app import module

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
@breadcrumb(u'Запись на прием')
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


@module.route('/action.html')
def html_action():
    return render_template(
        'schedule/action.html'
    )
