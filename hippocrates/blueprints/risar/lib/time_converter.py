# -*- coding: utf-8 -*-

import datetime
from dateutil import relativedelta


class DateTimeUtil(object):
    sec = 'second'
    min = 'minute'
    hour = 'hour'
    day = 'day'
    week = 'week'
    month = 'month'
    year = 'year'
    units_codes = [sec, min, hour, day, week, month, year]
    up_to = {
        'minute': lambda val: (val / 60, val % 60),
        'hour': lambda val: val * 24,
        'day': lambda val: val * 7,
        'week': lambda val: val / 7 * 30,
        'month': lambda val: val * 365
    }
    down_to = {
        'second': lambda val: val * 60,
        'minute': lambda val: val * 60,
        'hour': lambda val: val * 24,
        'day': lambda val: val * 7,
        'week': lambda val: val / 7 * 30,
        'month': lambda val: val * 365
    }

    class TimeVal(object):
        def __init__(self, **kwargs):
            self.second = kwargs.get('second')
            self.minute = kwargs.get('minute')
            self.hour = kwargs.get('hour')
            self.day = kwargs.get('day')
            self.week = kwargs.get('week')
            self.month = kwargs.get('month')
            self.year = kwargs.get('year')

        def __repr__(self):
            return '<TimeVal: second=%s, minute=%s, hour=%s, day=%s, week=%s, month=%s, year=%s>' % (
                self.second, self.minute, self.hour, self.day, self.week, self.month, self.year,
            )

    @classmethod
    def get_unit_code(cls, unit):
        if isinstance(unit, int):  # rbUnits
            code = unit.code
        else:
            code = unit
        if not isinstance(code, basestring) and code not in cls.units_codes:
            raise ValueError(u'Неподдерживаемое значение кода ед. измерения: %s' % unicode(code))
        return code

    def convert_time_unit(self, val, unit_from, unit_to):
        # not finished, test before using

        # self.check_unit(unit_from)
        # self.check_unit(unit_to)

        timeval = DateTimeUtil.TimeVal(**{unit_from: val})
        timeval = self._convert(timeval, unit_from, unit_to)
        return timeval

    def _convert(self, timeval, unit_from, unit_to):
        idx_from = self.units_codes.index(unit_from)
        idx_to = self.units_codes.index(unit_to)
        if idx_from < idx_to:
            val = getattr(timeval, unit_from)
            while idx_from < idx_to:
                next_code = self.units_codes[idx_from + 1]
                val = self.up_to[next_code](val)
                setattr(timeval, next_code, val)
                idx_from += 1
        elif idx_from > idx_to:
            val = getattr(timeval, unit_from)
            while idx_from > idx_to:
                next_code = self.units_codes[idx_from - 1]
                val = self.down_to[next_code](val)
                setattr(timeval, next_code, val)
                idx_from -= 1
        return timeval

    @classmethod
    def add_to_date(cls, dt, val, unit):
        if not isinstance(dt, (datetime.date, datetime.datetime)):
            raise TypeError('`dt` attribute must be a date/datetime')
        unit_code = cls.get_unit_code(unit)
        delta = cls._get_relative_delta(val, unit_code)
        return dt + delta

    @classmethod
    def _get_relative_delta(cls, val, unit_code):
        if unit_code == cls.sec:
            delta = relativedelta.relativedelta(seconds=val)
        elif unit_code == cls.min:
            delta = relativedelta.relativedelta(minutes=val)
        elif unit_code == cls.hour:
            delta = relativedelta.relativedelta(hours=val)
        elif unit_code == cls.day:
            delta = relativedelta.relativedelta(days=val)
        elif unit_code == cls.week:
            delta = relativedelta.relativedelta(weeks=val)
        elif unit_code == cls.month:
            delta = relativedelta.relativedelta(months=val)
        elif unit_code == cls.year:
            delta = relativedelta.relativedelta(years=val)
        else:
            delta = relativedelta.relativedelta(seconds=0)
        return delta

    @classmethod
    def get_current_date(cls):
        return datetime.date.today()


if __name__ == '__main__':
    print DateTimeUtil.add_to_date(datetime.datetime(2012, 2, 29), 2, 'year')