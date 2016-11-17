# -*- coding: utf-8 -*-

import datetime

from hippocrates.blueprints.risar.lib.card import PregnancyCard


def get_pregnancy_week(event, action=None, date=None):
    """
    :type event: nemesis.models.event.Event
    :type date: datetime.date | None
    :param event: Карточка пациентки
    :param action: Action атрибутов карты или None (тогда запрашивается из бд)
    :param date: Интересующая дата или None (тогда - текущая дата или дата окончания беременности)
    :return: число недель от начала беременности на дату
    """
    action = PregnancyCard.get_for_event(event).attrs
    start_date = action['pregnancy_start_date'].value
    if date is None:
        date = action['predicted_delivery_date'].value
        if date:
            date = min(date, datetime.date.today())
    if start_date:  # assume that date is not None
        if isinstance(date, datetime.datetime):
            date = date.date()
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        return (date - start_date).days / 7 + 1


def get_pregnancy_start_date(event):
    """
    :type event: nemesis.models.event.Event
    :param event: Карточка пациентки
    :return: Предположительная дата начала беременности
    """
    action = PregnancyCard.get_for_event(event).attrs
    start_date = action['pregnancy_start_date'].value
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    return start_date


def get_pregnancy_week_for_ultrasonography(event, dt=None):
    action = PregnancyCard.get_for_event(event).attrs
    if 'pregnancy_start_date_by_ultrasonography' in action.propsByCode:
        start_date = action['pregnancy_start_date_by_ultrasonography'].value
        if start_date:
            dt = dt or datetime.date.today()
            if isinstance(dt, datetime.datetime):
                dt = dt.date()
            res = (dt - start_date).days / 7
            if res > 0:
                return res
    return 0
