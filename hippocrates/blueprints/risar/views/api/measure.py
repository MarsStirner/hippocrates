# -*- encoding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from nemesis.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.expert.em_generation import EventMeasureGenerator
from blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from blueprints.risar.lib.expert.em_appointment_repr import EmAppointmentRepr
from blueprints.risar.lib.expert.em_result_repr import EmResultRepr
from blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from blueprints.risar.lib.utils import get_action_by_id


@module.route('/api/0/event_measure/generate/')
@module.route('/api/0/event_measure/generate/<int:action_id>')
@api_method
def api_0_event_measure_generate(action_id):
    action = Action.query.get_or_404(action_id)
    measure_gen = EventMeasureGenerator(action)
    measure_gen.generate_measures()
    em_ctrl = EventMeasureController()
    measures = em_ctrl.get_measures_in_action(action)
    return EventMeasureRepr().represent_listed_event_measures_in_action(measures)


@module.route('/api/0/event_measure/')
@module.route('/api/0/event_measure/<int:event_measure_id>')
@api_method
def api_0_event_measure_get(event_measure_id=None):
    em = EventMeasure.query.get(event_measure_id)
    if not em:
        raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/remove/', methods=['POST'])
@module.route('/api/0/event_measure/remove/<int:action_id>', methods=['POST'])
@api_method
def api_0_event_measure_remove(action_id):
    action = Action.query.get_or_404(action_id)
    measure_gen = EventMeasureGenerator(action)
    measure_gen.clear_existing_measures()
    return []


@module.route('/api/0/event_measure/execute/', methods=['POST'])
@module.route('/api/0/event_measure/execute/<int:event_measure_id>', methods=['POST'])
@api_method
def api_0_event_measure_execute(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.execute(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/cancel/', methods=['POST'])
@module.route('/api/0/event_measure/cancel/<int:event_measure_id>', methods=['POST'])
@api_method
def api_0_event_measure_cancel(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.cancel(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/')
@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/<int:appointment_id>')
@api_method
def api_0_event_measure_appointment_get(event_measure_id, appointment_id=None):
    get_new = safe_bool(request.args.get('new', False))
    em_ctrl = EventMeasureController()
    if get_new:
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
        action_type_id = em.scheme_measure.measure.appointmentAt_id
        measure_id = em.scheme_measure.measure_id
        if not action_type_id:
            raise ApiException(
                422,
                u'Невозможно создать направление для мероприятия Measure с id = {0},'
                u'т.к. для него не настроен ActionType для данных направления'.format(measure_id)
            )
        appointment = em_ctrl.get_new_appointment(em)
        # FIXME: иначе будут insert-ы с последующим rollback
        # Проблема в create_action, где при установке дефолтного значения для свойства
        # объект помещается в сессию, после чего сессия становится грязной в flush-тся позднее
        db.session.rollback()
    elif appointment_id:
        appointment = get_action_by_id(appointment_id)
        if not appointment:
            raise ApiException(404, u'Не найден Action с id = '.format(appointment_id))
    else:
        raise ApiException(404, u'`appointment_id` required')
    return EmAppointmentRepr().represent_appointment(appointment)


@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/', methods=['PUT'])
@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/<int:appointment_id>', methods=['POST'])
@api_method
def api_0_event_measure_appointment_save(event_measure_id, appointment_id=None):
    json_data = request.get_json()
    em = EventMeasure.query.get(event_measure_id)
    if not em:
        raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
    em_ctrl = EventMeasureController()
    if not appointment_id:
        appointment = em_ctrl.create_appointment(em, json_data)
        em_ctrl.store(em, appointment)
    elif appointment_id:
        appointment = get_action_by_id(appointment_id)
        if not appointment:
            raise ApiException(404, u'Не найден Action с id = '.format(appointment_id))
        appointment = em_ctrl.update_appointment(em, appointment, json_data)
        em_ctrl.store(em, appointment)
    else:
        raise ApiException(404, u'`appointment_id` required')
    return EmAppointmentRepr().represent_appointment(appointment)


@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/')
@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/<int:em_result_id>')
@api_method
def api_0_event_measure_result_get(event_measure_id, em_result_id=None):
    get_new = safe_bool(request.args.get('new', False))
    em_ctrl = EventMeasureController()
    if get_new:
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
        action_type_id = em.scheme_measure.measure.resultAt_id
        measure_id = em.scheme_measure.measure_id
        if not action_type_id:
            raise ApiException(
                422,
                u'Невозможно создать результат для мероприятия Measure с id = {0},'
                u'т.к. для него не настроен ActionType для данных результата'.format(measure_id)
            )
        em_result = em_ctrl.get_new_em_result(em)
        # FIXME: иначе будут insert-ы с последующим rollback
        # Проблема в create_action, где при установке дефолтного значения для свойства
        # объект помещается в сессию, после чего сессия становится грязной в flush-тся позднее
        db.session.rollback()
    elif em_result_id:
        em_result = get_action_by_id(em_result_id)
        if not em_result:
            raise ApiException(404, u'Не найден Action с id = '.format(em_result_id))
    else:
        raise ApiException(404, u'`appointment_id` required')
    return EmResultRepr().represent_em_result(em_result)


@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/', methods=['PUT'])
@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/<int:em_result_id>', methods=['POST'])
@api_method
def api_0_event_measure_result_save(event_measure_id, em_result_id=None):
    json_data = request.get_json()
    em = EventMeasure.query.get(event_measure_id)
    if not em:
        raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
    em_ctrl = EventMeasureController()
    if not em_result_id:
        em_result = em_ctrl.create_em_result(em, json_data)
        em_ctrl.store(em, em_result)
    elif em_result_id:
        em_result = get_action_by_id(em_result_id)
        if not em_result:
            raise ApiException(404, u'Не найден Action с id = '.format(em_result_id))
        em_result = em_ctrl.update_em_result(em, em_result, json_data)
        em_ctrl.store(em, em_result)
    else:
        raise ApiException(404, u'`appointment_id` required')
    return EmResultRepr().represent_em_result(em_result)


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

    paginate = safe_bool(data.get('paginate', True))
    em_ctrl = EventMeasureController()
    data = em_ctrl.get_measures_in_event(event, data, paginate)
    if paginate:
        return EventMeasureRepr().represent_paginated_event_measures(data)
    else:
        return EventMeasureRepr().represent_listed_event_measures(data)