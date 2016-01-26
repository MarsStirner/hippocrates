# -*- coding: utf-8 -*-


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
    def __init__(self, beg, end):
        self.beg = beg
        self.end = end


def get_intersection_type(interval, other_interval):
    """Возвращает тип пересечения интервала назначения с диапазоном
    @param interval: тестируемый интервал (DateTimeInterval)
    @param other_interval: временной интервал (DateTimeInterval)
    @rtype: int
    @return: тип пересечения:
        0 - не пересекает
        1 - пересекает слева, но не справа
        2 - перекрывает
        3 - попадает внутрь
        4 - пересекает справа
        5 - входное значение не интервал, но попадает во временной интервал
    """
    if not other_interval.end:
        other_interval = DateTimeInterval(other_interval.beg, other_interval.beg)
    if not interval.end:
        if other_interval.beg <= interval.beg < other_interval.end:
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