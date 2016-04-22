# -*- coding: utf-8 -*-

from nemesis.models.enums import MeasureStatus, EventMeasureActuality


em_status_all = {id_val for id_val in MeasureStatus.get_values()}

em_cancelled_explicit = {MeasureStatus.cancelled[0], MeasureStatus.cancelled_invalid[0]}

em_cancelled_implicit = {MeasureStatus.cancelled_dupl[0],
                         MeasureStatus.cancelled_changed_data[0]}

em_cancelled_all = em_cancelled_explicit | em_cancelled_implicit

em_final_status_list = {MeasureStatus.performed[0], MeasureStatus.overdue[0]} | em_cancelled_all

em_garbage_status_list = em_cancelled_implicit

em_touched_status_list = {MeasureStatus.assigned[0], MeasureStatus.waiting[0],
                          MeasureStatus.overdue[0], MeasureStatus.performed[0]} | em_cancelled_explicit

em_stats_status_list = {MeasureStatus.created[0], MeasureStatus.assigned[0], MeasureStatus.waiting[0],
                        MeasureStatus.overdue[0], MeasureStatus.performed[0]}


def is_em_touched(em):
    """Проверить, что с мероприятием случая провзаимодействовал кто-то или что-то."""
    return em.status in em_touched_status_list and (
        # TODO: добавить проверку на созданное направление
        em.appointmentAction_id is not None or em.resultAction_id is not None
    )


def is_em_cancellable(em):
    """Проверить, что мероприятие случая можно отменить"""
    return (
        not is_em_touched(em) and
        em.status not in em_final_status_list and
        em.is_actual == EventMeasureActuality.actual[0]
    )


def is_em_in_final_status(em):
    return em.status in em_final_status_list


def can_edit_em_appointment(em):
    return (
        em.appointmentAction_id is not None or
        em.scheme_measure.measure.appointmentAt_id is not None
    )


def can_edit_em_result(em):
    return (
        em.resultAction_id is not None or
        em.scheme_measure.measure.resultAt_id is not None
    )