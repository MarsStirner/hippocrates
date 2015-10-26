# -*- encoding: utf-8 -*-

from flask import request, render_template, abort, redirect
from flask.ext.login import current_user

from nemesis.app import app
from ..app import module
from nemesis.lib.utils import breadcrumb
from nemesis.models.event import Event
from nemesis.lib.user import UserProfileManager

# noinspection PyUnresolvedReferences
from . import api_json


@module.route('/event.html')
def html_event_info():
    try:
        event_id = int(request.args['event_id'])
        event = Event.query.get(event_id)
    except (KeyError, ValueError):
        return abort(400)
    # if event.is_stationary:
    #     wm10url = app.config['WEBMIS10_URL'].rstrip('/')
    #     if not wm10url:
    #         return abort(404)
    #     new_url = (u'%s/appeals/%s/?token=%s&role=%s'
    #                % (wm10url,
    #                   event_id,
    #                   request.cookies.get(app.config['CASTIEL_AUTH_TOKEN']),
    #                   current_user.current_role))
    #     return redirect(new_url)
    return get_event_form(event=event, client_id=event.client_id)


@module.route('/event_new.html')
@breadcrumb(u'Создание обращения')
def new_event():
    try:
        requestType_kind = request.args['requestType_kind']
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(400)
    return get_event_form(event=None, requestType_kind=requestType_kind, client_id=client_id)


def get_event_form(**kwargs):
    # В зависимости от ролей и прав разный лейаут
    requestType_kind = kwargs.get('requestType_kind', None)
    event = kwargs.get('event', None)
    if (UserProfileManager.has_ui_registrator() or
        UserProfileManager.has_ui_doctor() or
        UserProfileManager.has_ui_cashier()
    ):
        if (event and event.is_stationary) or requestType_kind == 'stationary':
            return render_template('event/event_info_stationary.html', **kwargs)
        elif (event and event.is_policlinic) or requestType_kind == 'policlinic':
            return render_template('event/event_info_policlinic.html', **kwargs)
    return abort(403)


@module.route('/event_group_choose.html')
def request_type_kind_choose():
    try:
        client_id = int(request.args['client_id'])
    except (KeyError, ValueError):
        return abort(400)
    return render_template('event/request_type_kind_choose.html', client_id=client_id)


@module.route('/events.html')
def get_events():
    return render_template('event/events.html')

