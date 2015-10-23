# -*- encoding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from blueprints.risar.app import module
from blueprints.risar.lib.expert.em_generation import EventMeasureGenerator
from blueprints.risar.lib.expert.em_representation import EventMeasureRepr
from blueprints.risar.lib.expert.em_manipulation import EventMeasureController


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


@module.route('/api/0/event_measure/cancel/', methods=['POST'])
@module.route('/api/0/event_measure/cancel/<int:event_measure_id>', methods=['POST'])
@api_method
def api_0_event_measure_cancel(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.cancel(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_measure(em)


@module.route('/api/0/event_measure/<int:event_measure_id>/direction/', methods=['POST'])
@api_method
def api_0_event_measure_make_direction(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.make_direction(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_measure(em)


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