# -*- coding: utf-8 -*-

from flask import request, abort

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent.common import represent_header
from hippocrates.blueprints.risar.lib.chart import can_control_events, take_event_control,\
    remove_event_control
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.event import Event, EventPersonsControl
from nemesis.systemwide import db

from nemesis.models.person import Person
from nemesis.models.utils import safe_current_user_id
__author__ = 'viruzzz-kun'


@module.route('/api/0/any/<int:event_id>/header')
@api_method
def api_0_chart_header(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    # if event.eventType.requestType.code != request_type_pregnancy:
    #     raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'header': represent_header(event),
    }


@module.route('/api/0/event_control/<do>/<int:event_id>/', methods=['POST'])
@module.route('/api/0/event_control/<do>/<int:event_id>/<int:person_id>', methods=['POST'])
@api_method
def api_0_chart_under_control(event_id, do='take_control', person_id=None):
    person_id = person_id or safe_current_user_id()
    if not person_id:
        raise ApiException(400, u'Неизвестно к кому привязывать')
    event = Event.query.get(event_id)
    person = Person.query.get(person_id)
    if not event:
        raise ApiException(404, u'Обращение c id=%s не найдено' % event_id)
    if not person:
        raise ApiException(404, u'Врач с id=%s не найден' % person_id)
    if not can_control_events():
        raise ApiException(403, u'Пользователь не может брать карты на контроль')

    if do == 'take_control':
        controlled = take_event_control(event)
    elif do == 'remove_control':
        controlled = remove_event_control(event)
    else:
        raise abort(404)

    return {
        'controlled': controlled,
        'event_id': event_id,
        'person_id': person_id,
    }
