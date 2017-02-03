# -*- encoding: utf-8 -*-

from flask import render_template, request, session
from jinja2 import TemplateNotFound
from nemesis.lib.html_utils import UIException

from nemesis.models.client import Client
from hippocrates.blueprints.patients.app import module
from nemesis.lib.utils import breadcrumb, parse_id, roles_require, bail_out
from nemesis.lib.user import UserProfileManager

# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
def index():
    session.pop('crumbs', None)
    session_crumbs = session.setdefault('crumbs', [])
    session_crumbs.append((request.path, u"Обслуживание пациентов"))
    return render_template('patients/servicing.html')


@module.route('/search/')
def search():
    session.pop('crumbs', None)
    session_crumbs = session.setdefault('crumbs', [])
    session_crumbs.append((request.path, u"Поиск пациентов"))
    return render_template('patients/servicing.html')


@module.route('/patient')
@breadcrumb(u'Пациент')
@roles_require(*(UserProfileManager.ui_groups['registrator'] + UserProfileManager.ui_groups['registrator_cut']))
def patient():
    client_id = parse_id(request.args, 'client_id')
    client_id is False and bail_out(UIException(400, u'Неверное значение параметра client_id'))
    if client_id:
        Client.query.filter(Client.id == client_id).count() or bail_out(UIException(404, u'Пациент не найден'))
    return render_template('patients/patient_info.html')


@module.route('/patient_events')
def patient_events():
    client_id = parse_id(request.args, 'client_id')
    client_id is False and bail_out(UIException(400, u'Неверное значение параметра client_id'))
    if client_id:
        Client.query.filter(Client.id == client_id).count() or bail_out(UIException(404, u'Пациент не найден'))
    return render_template('patients/patient_events.html', client_id=client_id)


@module.route('/patient_info_full.html')
def patient_info_full():
    client_id = parse_id(request.args, 'client_id')
    client_id is False and bail_out(UIException(400, u'Неверное значение параметра client_id'))
    client = Client.query.get(client_id) or bail_out(UIException(404, u'Пациент не найден'))
    return render_template(
        'patients/patient_info_full.html',
        client=client
    )


@module.route('/patient_actions_modal/<int:client_id>')
def patient_actions_modal(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('patients/_modal_patient_actions.html', client=client)