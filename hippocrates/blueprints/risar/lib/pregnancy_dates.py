# -*- coding: utf-8 -*-

import datetime

from blueprints.risar.lib.card_attrs import get_card_attrs_action


def get_pregnancy_week(event, date=None):
    """
    :type event: nemesis.models.event.Event
    :type date: datetime.date | None
    :param event: Карточка пациентки
    :param date: Интересующая дата или None (тогда - дата окончания беременности)
    :return: число недель от начала беременности на дату
    """
    action = get_card_attrs_action(event)
    start_date = action['pregnancy_start_date'].value
    if date is None:
        date = action['predicted_delivery_date'].value
    if start_date:  # assume that date is not None
        if isinstance(date, datetime.datetime):
            date = date.date()
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        return (min(date, datetime.date.today()) - start_date).days / 7 + 1


def get_pregnancy_start_date(event):
    """
    :type event: nemesis.models.event.Event
    :param event: Карточка пациентки
    :return: Предположительная дата начала беременности
    """
    action = get_card_attrs_action(event)
    start_date = action['pregnancy_start_date'].value
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    return start_date