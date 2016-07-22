# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent.common import represent_header
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.event import Event

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
