# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint
from application.models.client import Client
from blueprints.patients.app import module
from blueprints.patients.forms import ClientForm

# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
def index():
    try:
        return render_template('patients/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patient')
def patient():
    try:
        client_id = request.args['client_id']
        if client_id != 'new':
            client_id = int(client_id)
    except KeyError or ValueError:
        return abort(404)
    if client_id != 'new':
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
    client_form = ClientForm()
    return render_template(
        'patients/patient_info.html',
        form=client_form
    )