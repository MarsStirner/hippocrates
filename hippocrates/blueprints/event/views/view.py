# -*- encoding: utf-8 -*-

from flask import request, render_template, abort, redirect
from flask.ext.login import current_user

from nemesis.app import app
from nemesis.lib.html_utils import UIException
from ..app import module
from nemesis.lib.utils import breadcrumb, bail_out, parse_id
from nemesis.models.event import Event
from nemesis.lib.user import UserProfileManager

# noinspection PyUnresolvedReferences
from . import api_json


@module.route('/event.html')
def html_event_info():
    try:
        event_id = int(request.args['event_id'])
        event = Event.query.get(event_id)
        if not event:
            raise UIException(404, u'Обращение не найдено')
        requestType_kind = 'stationary' if event.is_stationary else 'policlinic'
    except (KeyError, ValueError):
        raise UIException(500, u'Неизвестная ошибка')
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
    return get_event_form(event=event, requestType_kind=requestType_kind, client_id=event.client_id)


@module.route('/event_new.html')
@breadcrumb(u'Создание обращения')
def new_event():
    requestType_kind = request.args.get('requestType_kind') or bail_out(UIException(400, u'Не указан параметр requestType_kind'))
    client_id = parse_id(request.args, 'client_id') or bail_out(UIException(400, u'Параметр client_id должен быть числом'))
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
    raise UIException(403, u'Для данной роли запрещён доступ к обращениям')


@module.route('/event_group_choose.html')
def request_type_kind_choose():
    client_id = parse_id(request.args, 'client_id') or bail_out(UIException(400, u'Параметр client_id должен быть числом'))
    return render_template('event/request_type_kind_choose.html', client_id=client_id)


@module.route('/events.html')
def get_events():
    return render_template('event/events.html')

