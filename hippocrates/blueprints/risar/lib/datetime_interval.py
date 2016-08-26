# -*- coding: utf-8 -*-

import datetime


class IntersectionType(object):
    none_left = 0  # () [___] Интервалы не пересекаются: 1-ый лежит левее
    none_right = 1  # [___] () Интервалы не пересекаются: 1-ый лежит правее
    left = 2  # ( [_)_] интервал попадает на левую границу
    over = 3  # ( [___] ) интервал перекрывает интервал
    inner = 4  # [_(___)_] интервал целиком входит в интервал
    right = 5  # [_(_]_) интервал попадает на правую границу
    point = 6  # [_._] не интервал, но точка попадает в интервал. Аналогично inner

    @classmethod
    def is_no_intersection(cls, it):
        return it == cls.none_left or it == cls.none_right

    @classmethod
    def is_intersection(cls, it):
        return not cls.is_no_intersection(it)


class DateTimeInterval(object):
    def __init__(self, beg, end=None, is_point=False):
        self.is_point = is_point
        self.beg = beg
        self.end = end if not is_point else beg
        if self.beg == self.end:
            self.is_point = True

    def __lt__(self, other):
        if not isinstance(other, DateTimeInterval):
            raise RuntimeError('Can compare only with DateTimeInterval')
        return get_intersection_type(self, other) == IntersectionType.none_left

    def __gt__(self, other):
        if not isinstance(other, DateTimeInterval):
            raise RuntimeError('Can compare only with DateTimeInterval')
        return get_intersection_type(self, other) == IntersectionType.none_right


def get_intersection_type(interval, other_interval):
    """Возвращает тип пересечения интервала с другим интервалом
    @param interval: тестируемый интервал (DateTimeInterval)
    @param other_interval: временной интервал (DateTimeInterval)
    @rtype: int
    @return: тип пересечения из IntersectionType
    """
    inf_end_date = max(interval.beg,
                       interval.end if interval.end is not None else interval.beg,
                       other_interval.beg) + datetime.timedelta(seconds=1)
    if not other_interval.end:
        other_interval = DateTimeInterval(other_interval.beg, inf_end_date)
    if not interval.end:
        interval = DateTimeInterval(interval.beg, inf_end_date)

    if interval.is_point:
        if other_interval.beg <= interval.beg <= other_interval.end:
            return IntersectionType.point
    elif other_interval.is_point:
        if interval.beg <= other_interval.beg <= interval.end:
            return IntersectionType.point
    elif interval.beg < other_interval.beg:
        if interval.end > other_interval.end:
            return IntersectionType.over
        elif other_interval.beg < interval.end <= other_interval.end:
            return IntersectionType.left
    elif interval.beg < other_interval.end:
        if interval.end > other_interval.end:
            return IntersectionType.right
        else:
            return IntersectionType.inner
    elif (interval.beg == other_interval.beg and
          interval.end == other_interval.end):
        return IntersectionType.over
    if interval.beg < other_interval.beg:
        return IntersectionType.none_left
    else:
        return IntersectionType.none_right