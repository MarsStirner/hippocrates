# -*- encoding: utf-8 -*-

from flask import render_template, abort, request, session
from jinja2 import TemplateNotFound

from application.models.client import Client
from blueprints.patients.app import module
from application.lib.utils import breadcrumb, parse_id, roles_require
from application.lib.user import UserProfileManager

# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
def index():
    session.pop('crumbs', None)
    session_crumbs = session.setdefault('crumbs', [])
    session_crumbs.append((request.path, u"Обслуживание пациентов"))
    try:
        return render_template('patients/servicing.html')
    except TemplateNotFound:
        abort(404)


@module.route('/search/')
def search():
    session.pop('crumbs', None)
    session_crumbs = session.setdefault('crumbs', [])
    session_crumbs.append((request.path, u"Поиск пациентов"))
    try:
        return render_template('patients/servicing.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patient')
@breadcrumb(u'Пациент')
@roles_require(*(UserProfileManager.ui_groups['registrator'] + UserProfileManager.ui_groups['registrator_cut']))
def patient():
    client_id = parse_id(request.args, 'client_id')
    if client_id is False:
        return abort(404)
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
    return render_template('patients/patient_info.html')


@module.route('/patient_info_full.html')
def patient_info_full():
    try:
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    return render_template(
        'patients/patient_info_full.html',
        client=client
    )