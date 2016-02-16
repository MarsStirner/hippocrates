# -*- coding: utf-8 -*-

from collections import deque

from nemesis.lib.utils import safe_date
from nemesis.models.actions import Action
from nemesis.models.enums import CardFillRate
from blueprints.risar.lib.utils import get_action, get_action_list
from blueprints.risar.lib.card_attrs import get_card_attrs_action
from blueprints.risar.risar_config import (checkup_flat_codes, risar_mother_anamnesis, risar_epicrisis,
    first_inspection_code, second_inspection_code)
from blueprints.risar.lib.time_converter import DateTimeUtil


def make_card_fill_timeline(event):
    """Построить таймлайн заполнения карты пациентки.

    :param event:
    :return:
    """
    if not event:
        return
    card_attrs_action = get_card_attrs_action(event)
    anamnesis = get_action(event, risar_mother_anamnesis)
    inspections = get_action_list(event, checkup_flat_codes).order_by(Action.begDate).all()
    first_inspection = last_inspection = None
    if inspections:
        if inspections[0].actionType.flatCode == first_inspection_code:
            first_inspection = inspections[0]
        last_inspection = inspections[-1]
    epicrisis = get_action(event, risar_epicrisis)
    preg_start_date = card_attrs_action['pregnancy_start_date'].value
    event_start_date = safe_date(event.setDate)
    cur_date = DateTimeUtil.get_current_date()

    inspections_iter = iter(
        [inspection for inspection in inspections
         if inspection.actionType.flatCode == second_inspection_code]
    )

    def get_next_repeated_inspection():
        try:
            return next(inspections_iter)
        except StopIteration:
            return None

    rules = {
        'anamnesis': {
            'waiting_period': 7,
            'get_document': lambda: anamnesis,
            'section_name': u'Анамнез'
        },
        'first_inspection': {
            'waiting_period': 7,
            'get_document': lambda: first_inspection,
            'section_name': u'Первичный осмотр'
        },
        'repeated_inspection': {
            'waiting_period': 30,
            'get_document': get_next_repeated_inspection,
            'section_name': u'Повторный осмотр'
        },
        'epicrisis': {
            'waiting_period': 329,  # 47 недель
            'get_document': lambda: epicrisis,
            'section_name': u'Эпикриз'
        }
    }

    def make_timeline_item(section, planned_date, fill_rate, document, delay_days, preg_week=None):
        return {
            'planned_date': planned_date,
            'fill_rate': CardFillRate(fill_rate),
            'delay_days': delay_days,
            'preg_week': preg_week,
            'section_name': rules[section]['section_name'],
            'document': {
                'id': document.id,
                'name': document.actionType.name,
                'beg_date': document.begDate,
                'set_person': document.setPerson,
            } if document else None
        }

    timeline = []
    q = deque()
    q.extend(('anamnesis', 'first_inspection', ))
    if preg_start_date:
        q.append('epicrisis')
    latest_date = event_start_date
    max_date = None
    if preg_start_date:
        epicrisis_planned_date = DateTimeUtil.add_to_date(
            preg_start_date, rules['epicrisis']['waiting_period'], DateTimeUtil.day
        )
        epicrisis_date = safe_date(epicrisis and epicrisis.begDate)
        max_date = (
            epicrisis_date
            if epicrisis_date and epicrisis_date < epicrisis_planned_date
            else epicrisis_planned_date
        )
    while len(q):
        section = q.popleft()

        document = rules[section]['get_document']()

        # итерация с текущей датой >= максимальной возможна только для секции эпикриза или
        # для секции повторного осмотра, для которой найдется существующий повторный осмотр;
        # иначе - это плановый повторный осмотр, который будет не обязателен из-за наличия
        # эпикриза, планового или фактического
        if max_date and latest_date >= max_date and (
            section != 'epicrisis' and document is None
        ):
            latest_date = max_date
            continue

        document_date = safe_date(document.begDate) if document is not None else None
        due_date = DateTimeUtil.add_to_date(latest_date, rules[section]['waiting_period'], DateTimeUtil.day)

        fill_rate = (
            CardFillRate.filled[0]
            if document is not None else (
                CardFillRate.waiting[0]
                if cur_date <= due_date else CardFillRate.not_filled[0]
            )
        )
        delay = max(
            0,
            ((document_date if document_date else cur_date) - due_date).days
        )
        item = make_timeline_item(section, due_date, fill_rate, document, delay)
        timeline.append(item)

        if section in ('first_inspection', 'repeated_inspection') and document is not None:
            latest_date = document_date
            q.appendleft('repeated_inspection')

    return timeline
