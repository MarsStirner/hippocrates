# -*- coding: utf-8 -*-
from application.lib.enum import Enum

__author__ = 'mmalkov'


class EventOrder(Enum):
    planned = 1, u'Планово'
    emergency = 2, u'Экстренно'
    without = 3, u'Самотёком'
    forced = 4, u'Принудительно'


class EventPrimary(Enum):
    primary = 1, u'Первично'
    secondary = 2, u'Повторно'
    active = 3, u'Активное посещение'
    transport = 4, u'Транспортировка'
    ambulatory = 5, u'Амбулаторно'


class ActionStatus(Enum):
    started = 0, u'Начато'
    waiting = 1, u'Ожидание'
    finished = 2, u'Закончено'
    cancelled = 3, u'Отменено'
    no_result = 4, u'Без результата'