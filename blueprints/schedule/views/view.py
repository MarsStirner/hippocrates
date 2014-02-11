# -*- encoding: utf-8 -*-
import calendar
import datetime
import json
from flask import render_template, abort, request, redirect, url_for, flash, jsonify

from jinja2 import TemplateNotFound
from wtforms import TextField, BooleanField, IntegerField
from wtforms.validators import Required
from flask.ext.wtf import Form

from ..app import module
from application.database import db
from application.lib.utils import admin_permission, public_endpoint
from blueprints.schedule.lib.utils import get_schedule, paginator_month
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer, MyJsonEncoder


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
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
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
    }, cls=MyJsonEncoder)


@module.route('/api/pages/')
@public_endpoint
def api_pages():
    today = datetime.date.today()
    try:
        if 'mid_date' in request.args:
            mid_date = datetime.datetime.strptime(request.args['mid_date'], '%Y.%m').date()
            if mid_date.year == today.year and mid_date.month == today.month:
                mid_date = today
        else:
            mid_date = today
    except ValueError:
        return abort(404)
    page, pages = paginator_month(mid_date)
    return json.dumps({
        'page': page,
        'pages': [
            ('%02d.%02d - %02d.%02d' % (p[0].day, p[0].month, p[1].day, p[0].month), p[0].isoformat())
            for p in pages
        ],
    }, cls=MyJsonEncoder)


@module.route('/schedule/table/')
@public_endpoint
def schedule_table():
    try:
        person_id = int(request.args['person_id'])
        start_date = datetime.datetime.strptime(request.args['start_date'], '%Y.%m.%d').date()
        end_date = start_date + datetime.timedelta(weeks=1)
    except KeyError or ValueError:
        return abort(404)
    schedule = get_schedule(person_id, start_date, end_date)
    return render_template(
        'schedule/schedule_table.html',
        schedule=schedule
    )

@module.route('/schedule/main/')
@public_endpoint
def schedule_main():
    try:
        person_id = int(request.args['person_id'])
        if 'mid_date' in request.args:
            mid_date = datetime.datetime.strptime(request.args['mid_date'], '%Y.%m').date()
        else:
            mid_date = datetime.date.today()
    except KeyError or ValueError:
        return abort(404)
    page, pages = paginator_month(mid_date)
    start_date, end_date = pages[page]
    schedule = get_schedule(person_id, start_date, end_date)
    return render_template(
        'schedule/schedule_main_part.html',
        schedule=schedule,
        page=page,
        pages=pages
    )