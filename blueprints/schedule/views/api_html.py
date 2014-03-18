# -*- coding: utf-8 -*-
from flask import request, abort, render_template
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Client
from blueprints.schedule.views.jsonify import ClientVisualizer, Format
from blueprints.schedule.forms import ClientForm

__author__ = 'mmalkov'


@module.route('/api/patient.html')
@public_endpoint
def html_patient():
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
        'schedule/patient_info.html',
        form=client_form
    )