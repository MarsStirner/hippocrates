# -*- encoding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.actions import Action
from nemesis.models.event import Event
from blueprints.risar.app import module
from blueprints.risar.lib.expert.protocols import EventMeasureGenerator, EventMeasureRepr


@module.route('/api/0/event_measure/generate/')
@module.route('/api/0/event_measure/generate/<int:action_id>')
@api_method
def api_0_event_measure_generate(action_id):
    action = Action.query.get_or_404(action_id)
    measure_gen = EventMeasureGenerator(action)
    measure_gen.generate_measures()
    return EventMeasureRepr().represent_by_action(action)


@module.route('/api/0/event_measure/remove/', methods=['POST'])
@module.route('/api/0/event_measure/remove/<int:action_id>', methods=['POST'])
@api_method
def api_0_event_measure_remove(action_id):
    action = Action.query.get_or_404(action_id)
    measure_gen = EventMeasureGenerator(action)
    measure_gen.clear_existing_measures()
    return []


@module.route('/api/0/measure/list/<int:event_id>', methods=['GET', 'POST'])
@module.route('/api/0/measure/list/')
@api_method
def api_0_measure_list(event_id):
    data = dict(request.args)
    if request.json:
        data.update(request.json)

    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != 'pregnancy':
        raise ApiException(400, u'Обращение не является случаем беременности')

    return EventMeasureRepr().represent_by_event(event, data)