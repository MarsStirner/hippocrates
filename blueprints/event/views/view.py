# -*- encoding: utf-8 -*-

from flask import request, render_template, abort
from jinja2 import TemplateNotFound
from ..app import module
from flask.ext.login import current_user

# noinspection PyUnresolvedReferences
from . import api_json
from application.lib.utils import breadcrumb
from application.models.event import Event


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
        event = Event.query.get(event_id)
    except (KeyError, ValueError):
        return abort(400)
    return get_event_form(event=event)


@module.route('/event_new.html')
@breadcrumb(u'Создание обращения')
def new_event():
    try:
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(400)
    return get_event_form(event=None)


def get_event_form(**kwargs):
    # В зависимости от ролей и прав разный лейаут
    if current_user.role_in('admin', 'doctor', 'clinicDoctor', 'rRegistartor', 'clinicRegistrator'):
        return render_template('event/event_info.html', **kwargs)
    return abort(403)



@module.route('/events.html')
def get_events():
    return render_template('event/events.html')

