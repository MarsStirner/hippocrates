# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm import lazyload, contains_eager

from ..xform import XForm, VALIDATION_ERROR
from .schemas import ScheduleSchema

from nemesis.models.schedule import ScheduleTicket, Schedule
from nemesis.models.person import Person
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, format_time
from nemesis.lib.apiutils import ApiException


logger = logging.getLogger('simple')


class ScheduleXForm(ScheduleSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Person
    target_id_required = False

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        pass

    def __init__(self, *args, **kwargs):
        super(ScheduleXForm, self).__init__(*args, **kwargs)
        self.schedules = {}

    def find_schedules(self, args):
        if 'date_begin' in args:
            date_begin = safe_date(args['date_begin'])
            if not date_begin:
                raise ApiException(
                    VALIDATION_ERROR,
                    u'Аргумент date_begin не соответствует формату даты YYYY-MM-DD'
                )
            args['date_begin'] = date_begin
        if 'date_end' in args:
            date_end = safe_date(args['date_end'])
            if not date_end:
                raise ApiException(
                    VALIDATION_ERROR,
                    u'Аргумент date_end не соответствует формату даты YYYY-MM-DD'
                )
            args['date_end'] = date_end

        if not self.parent_obj:
            self.find_parent_obj(self.parent_obj_id)

        query = db.session.query(Schedule).join(
            ScheduleTicket
        ).filter(
            ScheduleTicket.deleted == 0,
            Schedule.deleted == 0,
            Schedule.person_id == self.parent_obj_id
        )
        if 'date_begin' in args:
            query = query.filter(Schedule.date >= args['date_begin'])
        if 'date_end' in args:
            query = query.filter(Schedule.date <= args['date_end'])

        query = query.options(
            lazyload('*'),
            contains_eager(Schedule.tickets)
        )
        for sched in query:
            self.schedules.setdefault(sched.date, []).extend(sched.tickets)

    def as_json(self):
        res = []
        for date in sorted(self.schedules.keys()):
            res.append({
                'date': date,
                'intervals': [
                    {
                        'begin_time': format_time(ticket.begTime),
                        'end_time': format_time(ticket.endTime)
                    }
                    for ticket in self.schedules[date]
                ]
            })
        return res
