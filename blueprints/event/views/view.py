# -*- encoding: utf-8 -*-

from flask import request, render_template, abort
from jinja2 import TemplateNotFound
from ..app import module
from flask.ext.login import current_user

# noinspection PyUnresolvedReferences
from . import api_json
from application.lib.utils import breadcrumb


@module.route('/')
def index():
    try:
        return render_template('event/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/event.html')
def html_event_info():
    try:
        event_id = int(request.args['event_id'])
    except KeyError or ValueError:
        return abort(400)
    return get_event_form()


@module.route('/event_new.html')
@breadcrumb(u'Создание обращения')
def new_event():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(400)
    return get_event_form(event_new=True)


def get_event_form(**kwargs):
    # В зависимости от ролей и прав разный лейаут
    if current_user.role_in('admin'):
        form_role = 'admin'
    elif current_user.role_in(('doctor', 'clinicDoctor')):
        form_role = 'doctor'
    elif current_user.role_in(('rRegistartor', 'clinicRegistrator')):
        form_role = 'receptionist'
    else:
        return abort(403)
    return render_template('event/event_info.html', form_role=form_role, **kwargs)
