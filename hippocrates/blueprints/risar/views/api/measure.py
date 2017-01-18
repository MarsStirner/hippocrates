# -*- encoding: utf-8 -*-
from hippocrates.blueprints.risar.lib import sirius
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.expert.em_appointment_repr import EmAppointmentRepr
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from hippocrates.blueprints.risar.lib.expert.em_result_repr import EmResultRepr
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_interval
from hippocrates.blueprints.risar.lib.utils import get_action_by_id
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int, db_non_flushable
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from nemesis.systemwide import db


@module.route('/api/0/event_measure/generate/')
@module.route('/api/0/event_measure/generate/<int:action_id>')
@api_method
def api_0_event_measure_generate(action_id):
    action = Action.query.get_or_404(action_id)
    em_ctrl = EventMeasureController()
    em_ctrl.regenerate(action)
    if em_ctrl.exception:
        raise ApiException(500, unicode(em_ctrl.exception))
    measures = em_ctrl.get_measures_in_action(action)
    return EventMeasureRepr().represent_listed_event_measures_in_action(measures)


@module.route('/api/0/event_measure/')
@module.route('/api/0/event_measure/<int:event_measure_id>')
@api_method
def api_0_event_measure_get(event_measure_id=None):
    get_new = safe_bool(request.args.get('new', False))
    if get_new:
        data = request.args.to_dict()
        em_ctrl = EventMeasureController()
        em = em_ctrl.get_new_event_measure(data)
    elif event_measure_id:
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
    else:
        raise ApiException(404, u'`event_measure_id` required')
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure_info/<int:event_measure_id>')
@db_non_flushable
@api_method
def api_0_event_measure_get_info(event_measure_id):
    em_ctrl = EventMeasureController()
    em = EventMeasure.query.get(event_measure_id)
    if not em:
        raise ApiException(404, u'Не найдено EM с id = {}'.format(event_measure_id))

    appointment = em.appointment_action
    if not appointment and em.measure.appointmentAt_id:
        appointment = em_ctrl.get_new_appointment(em)
        data = {
            'em': em,
            'checkup_id': safe_int(request.args.get('checkup_id'))
        }
        appointment = em_ctrl.fill_new_appointment(appointment, data)
    em.appointment_action = appointment

    em_result = em.result_action
    if not em_result and em.measure.resultAt_id:
        em_result = em_ctrl.get_new_em_result(em)
    em.result_action = em_result

    data = EventMeasureRepr().represent_event_measure_info(em)
    return data


@module.route('/api/0/event_measure/<int:event_id>/save-list/', methods=['POST'])
@api_method
def api_0_event_measure_save_list(event_id):
    data = request.get_json()
    event = Event.query.get(event_id)

    em_ctrl = EventMeasureController()
    em_list = em_ctrl.save_list(event, data)
    em_ctrl.store(*em_list)

    for em in em_list:
        sirius.send_to_mis(
            sirius.RisarEvents.CREATE_REFERRAL,
            sirius.RisarEntityCode.MEASURE,
            sirius.OperationCode.READ_ONE,
            'risar.api_measure_get',
            obj=('measure_id', em.id),
            params={'card_id': event_id},
            is_create=True,
        )

    return EventMeasureRepr().represent_listed_event_measures(em_list)


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
    data = request.get_json()
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.cancel(em, data)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/<int:event_measure_id>', methods=['DELETE'])
@api_method
def api_0_event_measure_delete(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.delete(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/<int:event_measure_id>/undelete', methods=['POST'])
@api_method
def api_0_event_measure_undelete(event_measure_id):
    em = EventMeasure.query.get_or_404(event_measure_id)
    em_ctrl = EventMeasureController()
    em_ctrl.restore(em)
    em_ctrl.store(em)
    return EventMeasureRepr().represent_em_full(em)


@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/')
@module.route('/api/0/event_measure/<int:event_measure_id>/appointment/<int:appointment_id>')
@db_non_flushable
@api_method
def api_0_event_measure_appointment_get(event_measure_id, appointment_id=None):
    get_new = safe_bool(request.args.get('new', False))
    em_ctrl = EventMeasureController()
    if get_new:
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
        action_type_id = em.measure.appointmentAt_id
        measure_id = em.measure.id
        if not action_type_id:
            raise ApiException(
                422,
                u'Невозможно создать направление для мероприятия Measure с id = {0},'
                u'т.к. для него не настроен ActionType для данных направления'.format(measure_id)
            )
        appointment = em_ctrl.get_new_appointment(em)

        data = {
            'em': em,
            'checkup_id': safe_int(request.args.get('checkup_id'))
        }
        appointment = em_ctrl.fill_new_appointment(appointment, data)
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
    create_mode = not appointment_id and request.method == 'PUT'
    if create_mode:
        appointment = em_ctrl.create_appointment(em, json_data)
        em_ctrl.store_appointments([em])

    elif appointment_id:
        appointment = get_action_by_id(appointment_id)
        if not appointment:
            raise ApiException(404, u'Не найден Action с id = '.format(appointment_id))
        appointment = em_ctrl.update_appointment(em, appointment, json_data)
        em_ctrl.store(em, appointment)
    else:
        raise ApiException(404, u'`appointment_id` required')

    sirius.send_to_mis(
        sirius.RisarEvents.CREATE_REFERRAL,
        sirius.RisarEntityCode.MEASURE,
        sirius.OperationCode.READ_ONE,
        'risar.api_measure_get',
        obj=('measure_id', event_measure_id),
        params={'card_id': em.event_id},
        is_create=create_mode,
    )

    return EmAppointmentRepr().represent_appointment(appointment)


@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/')
@module.route('/api/0/event_measure/<int:event_measure_id>/em_result/<int:em_result_id>')
@db_non_flushable
@api_method
def api_0_event_measure_result_get(event_measure_id, em_result_id=None):
    get_new = safe_bool(request.args.get('new', False))
    em_ctrl = EventMeasureController()
    if get_new:
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(404, u'Не найдено EM с id = '.format(event_measure_id))
        action_type_id = em.measure.resultAt_id
        measure_id = em.measure_id
        if not action_type_id:
            raise ApiException(
                422,
                u'Невозможно создать результат для мероприятия Measure с id = {0},'
                u'т.к. для него не настроен ActionType для данных результата'.format(measure_id)
            )
        em_result = em_ctrl.get_new_em_result(em)
    elif em_result_id:
        em_result = get_action_by_id(em_result_id)
        if not em_result:
            raise ApiException(404, u'Не найден Action с id = '.format(em_result_id))
    else:
        raise ApiException(404, u'необходим `em_result_id`')
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
    create_mode = not em_result_id and request.method == 'PUT'
    if create_mode:
        em_result = em_ctrl.create_em_result(em, json_data)
        if em_ctrl.emr_changes_diagnoses_system(em_result):
            em_ctrl.update_patient_diagnoses(em_result, create_mode)
        em_ctrl.store(em, em_result)
    elif em_result_id:
        em_result = get_action_by_id(em_result_id)
        if not em_result:
            raise ApiException(404, u'Не найден Action с id = '.format(em_result_id))
        if em_ctrl.emr_changes_diagnoses_system(em_result):
            old_em_diag_data = em_ctrl.get_emr_data_for_diags(em_result)
        else:
            old_em_diag_data = None
        em_result = em_ctrl.update_em_result(em, em_result, json_data)
        if em_ctrl.emr_changes_diagnoses_system(em_result):
            em_ctrl.update_patient_diagnoses(em_result, False, old_em_diag_data)
        em_ctrl.store(em, em_result)
    else:
        raise ApiException(404, u'необходим `em_result_id`')
    card = PregnancyCard.get_for_event(em.event)
    card.reevaluate_card_attrs()
    db.session.commit()
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

    paginate = safe_bool(data.get('paginate', True))
    em_ctrl = EventMeasureController()
    data = em_ctrl.get_measures_in_event(event, data, paginate)
    if paginate:
        return EventMeasureRepr().represent_paginated_event_measures(data)
    else:
        return EventMeasureRepr().represent_listed_event_measures(data)


@module.route('/api/0/measure/list/by_action/<int:action_id>')
@module.route('/api/0/measure/list/by_action/')
@api_method
def api_0_measure_list_by_action(action_id):
    args = dict(request.args)
    action = Action.query.get_or_404(action_id)

    em_ctrl = EventMeasureController()
    data = em_ctrl.get_measures_in_action(action, args)
    return EventMeasureRepr().represent_listed_event_measures(data)


@module.route('/api/0/measure_checkups/')
@module.route('/api/0/measure_checkups/<int:event_id>', methods=['GET', 'POST'])
@api_method
def api_0_event_measure_checkups(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return {
        'checkups': map(represent_pregnancy_checkup_interval, card.checkups)
    }


@module.route('/api/0/event_measure/<int:action_id>/appointment-list/', methods=['POST'])
@api_method
def api_0_event_measure_appointment_list_save(action_id):
    json_data = request.get_json()
    data_list = json_data.get('em_id_list')
    action = get_action_by_id(action_id)
    em_ctrl = EventMeasureController()
    ev_measures = em_ctrl.save_appointment_list(data_list, action)
    em_ctrl.store_appointments(ev_measures, silent=True)

    for em in ev_measures:
        sirius.send_to_mis(
            sirius.RisarEvents.CREATE_REFERRAL,
            sirius.RisarEntityCode.MEASURE,
            sirius.OperationCode.READ_ONE,
            'risar.api_measure_get',
            obj=('measure_id', em.id),
            params={'card_id': em.event_id},
            is_create=False,
        )

    return EventMeasureRepr().represent_listed_event_measures_in_action(ev_measures)
