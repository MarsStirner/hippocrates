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


class Gender(Enum):
    male = 1, u'М'
    female = 2, u'Ж'


class AddressType(Enum):
    reg = 0, u'Регистрации'
    live = 1, u'Проживания'


class LocalityType(Enum):
    vilage = 2, u'Село'
    city = 1, u'Город'


class AllergyPower(Enum):
    undefined = 0, u'не известно'
    low = 1, u'малая'
    medium = 2, u'средняя'
    high = 3, u'высокая'
    strict = 4, u'строгая'