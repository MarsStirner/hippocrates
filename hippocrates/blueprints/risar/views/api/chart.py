# -*- coding: utf-8 -*-

from flask import request

from datetime import datetime

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent.common import represent_header
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.event import Event, ControlledEvents
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

@module.route('/api/0/event_control/<do>/<int:event_id>/<int:person_id>', methods=['POST', 'GET'])
@api_method
def api_0_chart_under_control(event_id, do='take_control', person_id=0):
    person_id = person_id or safe_current_user_id()

    event = Event.query.get(event_id)
    person = Person.query.get(person_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено c id %s не найдено' % event_id)
    if not person:
        raise ApiException(404, u'Врач не найден с айди %s не найден' % person_id)

    qr = person.events_under_control.filter(
        ControlledEvents.event_id == event_id,
        ControlledEvents.endDate == None
    )

    if not person_id:
        raise ApiException(404, u'не известно к кому привязывать')

    if request.method == 'POST':
        if do == 'take_control':
            already_controlled = qr.all()
            if not already_controlled:
                ce = ControlledEvents(event_id=event_id,
                                      person_id=person_id,
                                      begDate=datetime.now())
                db.session.add(ce)
        elif do == 'off_control':
            qr.update({ControlledEvents.endDate: datetime.now()})
        db.session.commit()

    return {
        'controlled': True if qr.all() else False,
        'event_id': event_id,
        'person_id': person_id,
    }