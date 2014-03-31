# -*- encoding: utf-8 -*-

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from application.lib.utils import public_endpoint
from blueprints.patients.app import module
from application.models.exists import Client
from blueprints.patients.forms import ClientForm
from blueprints.schedule.views.jsonify import ClientVisualizer, Format

# noinspection PyUnresolvedReferences
from . import api_html, api_json


@module.route('/')
@public_endpoint
def index():
    try:
        return render_template('patients/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patient')
@public_endpoint
def patient_get():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    context = ClientVisualizer(Format.HTML)
    client_form = ClientForm()
    return render_template(
        'patients/patient_info.html',
        form=client_form
    )


@module.route('/new_patient')
@public_endpoint
def new_patient():
    try:
        client = Client()
        client_form = ClientForm()

        return render_template('patients/new_patient.html', form=client_form)
    except TemplateNotFound:
        abort(404)