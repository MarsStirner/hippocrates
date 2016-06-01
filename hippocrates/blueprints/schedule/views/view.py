# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound
from nemesis.lib.html_utils import UIException

from nemesis.lib.utils import roles_require, bail_out, parse_id
from nemesis.models.client import Client
from nemesis.lib.utils import breadcrumb
from hippocrates.blueprints.schedule.app import module
from nemesis.lib.user import UserProfileManager


# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
def index():
    return render_template('schedule/index.html')


@module.route('/appointment/')
@breadcrumb(u'Запись на прием')
def appointment():
    client_id = parse_id(request.args, 'client_id')
    client_id is False and bail_out(UIException(400, u'Некорректное значение client_id'))
    client = Client.query.get(client_id) or bail_out(UIException(404, u'Пациент не найден'))
    return render_template(
        'schedule/person_appointment.html',
        client=client
    )


@module.route('/person_month/')
@roles_require(*UserProfileManager.ui_groups['registrator'])
def person_schedule_monthview():
    return render_template('schedule/person_schedule_monthview.html')


@module.route('/doctor/')
@roles_require(*UserProfileManager.ui_groups['doctor'])
@breadcrumb(u'Приём пациентов')
def doctor_schedule_day():
    return render_template('schedule/doctor_schedule_day.html')


@module.route('/day_free.html')
def html_day_free():
    return render_template('schedule/day_free.html')

