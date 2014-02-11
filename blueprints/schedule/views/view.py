# -*- encoding: utf-8 -*-
import calendar
import datetime
from flask import render_template, abort, request, redirect, url_for, flash, jsonify

from jinja2 import TemplateNotFound
from wtforms import TextField, BooleanField, IntegerField
from wtforms.validators import Required
from flask.ext.wtf import Form

from ..app import module
from application.database import db
from application.lib.utils import admin_permission, public_endpoint
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import JsonSchedule


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


@module.route('/api/schedule/')
@public_endpoint
def api_schedule():
    try:
        person_id = int(request.args['person_id'])
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y.%m.%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
    except KeyError or ValueError:
        return abort(404)
    schedules = Schedule.query.\
        filter(Schedule.person_id == person_id).\
        filter(month_f <= Schedule.date).\
        filter(Schedule.date <= month_l).\
        order_by(Schedule.date)
    context = JsonSchedule()
    context.push_all(schedules, month_f, month_l)
    return jsonify({
        'result': context.__json__(),
        'max_tickets': context.max_tickets,
        'transposed': context.transposed
    })