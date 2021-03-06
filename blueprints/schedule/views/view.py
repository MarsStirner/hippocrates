# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint, roles_require
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


@module.route('/appointment/')
@breadcrumb(u'Запись на прием')
def appointment():
    try:
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    return render_template(
        'schedule/person_appointment.html',
        client=client
    )


@module.route('/person_month/')
@roles_require('clinicRegistrator')
def person_schedule_monthview():
    try:
        return render_template('schedule/person_schedule_monthview.html')
    except TemplateNotFound:
        abort(404)


@module.route('/doctor/')
@roles_require('clinicDoctor')
@breadcrumb(u'Приём пациентов')
def doctor_schedule_day():
    try:
        return render_template('schedule/doctor_schedule_day.html')
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
