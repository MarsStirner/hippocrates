# -*- coding: utf-8 -*-


class IntersectionType:
    none = 0  # () [___] или [___] () Интервалы не пересекаются
    left = 1  # ( [_)_] интервал попадает на левую границу
    over = 2  # ( [___] ) интервал перекрывает интервал
    inner = 3  # [_(___)_] интервал целиком входит в интервал
    right = 4  # [_(_]_) интервал попадает на правую границу
    point = 5  # [_._] не интервал, но точка попадает в интервал. Аналогично inner


class DateTimeInterval(object):
    def __init__(self, beg_datetime, end_datetime):
        self.beg_datetime = beg_datetime
        self.end_datetime = end_datetime


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
    if not other_interval.end_datetime:
        other_interval = DateTimeInterval(other_interval.beg_datetime, other_interval.beg_datetime)
    if not interval.end_datetime:
        if other_interval.beg_datetime <= interval.beg_datetime < other_interval.end_datetime:
            return IntersectionType.point
    elif interval.beg_datetime < other_interval.beg_datetime:
        if interval.end_datetime > other_interval.end_datetime:
            return IntersectionType.over
        elif other_interval.beg_datetime < interval.end_datetime <= other_interval.end_datetime:
            return IntersectionType.left
    elif interval.beg_datetime < other_interval.end_datetime:
        if interval.end_datetime > other_interval.end_datetime:
            return IntersectionType.right
        else:
            return IntersectionType.inner
    elif (interval.beg_datetime == other_interval.beg_datetime and
          interval.end_datetime == other_interval.end_datetime):
        return IntersectionType.over
    return IntersectionType.none