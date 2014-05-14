# -*- encoding: utf-8 -*-
from flask import render_template, abort
from jinja2 import TemplateNotFound
from ..app import module
from flask.ext.login import current_user

# noinspection PyUnresolvedReferences
from . import api_json


@module.route('/')
def index():
    try:
        return render_template('event/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/event.html')
def html_event_info():
    # event_id = int(request.args['event_id'])
    # В зависимости от ролей и прав разный лейаут
    if 'admin' in current_user.roles and 1 == 10:
        form_role = 'admin'
    elif 'doctor' in current_user.roles and 1 == 10:
        form_role = 'doctor'
    elif 'rRegistartor' in current_user.roles or 'clinicRegistrator' in current_user.roles or 1 == 1:
        form_role = 'receptionist'
    else:
        raise
    return render_template('event/event_info.html', form_role=form_role)


@module.route('/event_new.html')
def new_event():
    return html_event_info()