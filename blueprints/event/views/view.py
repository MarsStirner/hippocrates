# -*- encoding: utf-8 -*-

from flask import request, render_template, abort, redirect

from application.app import app
from ..app import module
from application.lib.utils import breadcrumb
from application.models.event import Event
from application.lib.user import UserProfileManager

# noinspection PyUnresolvedReferences
from . import api_json


@module.route('/event.html')
def html_event_info():
    try:
        event_id = int(request.args['event_id'])
        event = Event.query.get(event_id)
    except (KeyError, ValueError):
        return abort(400)
    if event.is_stationary:
        wm10url = app.config['WEBMIS10_URL'].rstrip('/')
        if not wm10url:
            return abort(404)
        new_url = u'%s/appeals/%s/' % (wm10url, event_id)
        return redirect(new_url)
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
    if UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_doctor():
        return render_template('event/event_info.html', **kwargs)
    return abort(403)


@module.route('/events.html')
def get_events():
    return render_template('event/events.html')

