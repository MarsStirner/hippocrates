# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm import lazyload, contains_eager

from ..xform import XForm, VALIDATION_ERROR
from .schemas import ScheduleSchema, Schedule2Schema

from hippocrates.blueprints.schedule.lib.data import delete_schedules, create_schedules

from nemesis.models.schedule import ScheduleTicket, Schedule, rbReceptionType
from nemesis.models.person import Person
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, format_time, safe_dict
from nemesis.lib.apiutils import ApiException


logger = logging.getLogger('simple')


class ScheduleXForm(ScheduleSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Person
    target_id_required = False

    def __init__(self, *args, **kwargs):
        super(ScheduleXForm, self).__init__(*args, **kwargs)
        self.person = None
        self.schedules = {}
        self.new_schedules = []

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        pass

    def init_and_check_params(self, lpu_code, doctor_code, data=None):
        self.person = self.find_doctor(doctor_code, lpu_code)
        super(ScheduleXForm, self).check_params(None, self.person.id, data)

    def find_schedules(self, **args):
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

        query = db.session.query(Schedule).filter(
            Schedule.deleted == 0,
            Schedule.person_id == self.parent_obj_id,
            Schedule.reasonOfAbsence_id.is_(None)
        ).order_by(Schedule.date, Schedule.begTime)
        if 'date_begin' in args:
            query = query.filter(Schedule.date >= args['date_begin'])
        if 'date_end' in args:
            query = query.filter(Schedule.date <= args['date_end'])

        query = query.options(
            lazyload('*'),
        )
        for sched in query:
            self.schedules.setdefault(sched.date, []).append(sched)

    def _map_sheds_data(self, data):
        def map_interval(i):
            return {
                'planned': i['quantity'],
                'begTime': i['begin_time'],
                'endTime': i['end_time'],
                'reception_type': rec_type_amb
            }

        rec_type_amb = safe_dict(rbReceptionType.query.filter(rbReceptionType.code == 'amb').first())
        by_dates = {}
        for sched_interval in data:
            by_dates.setdefault(sched_interval['date'], []).extend(
                [map_interval(interval) for interval in sched_interval['intervals']]
            )

        res = []
        for date, subscheds in by_dates.iteritems():
            res.append({
                'date': date,
                'scheds': sorted(subscheds, key=lambda s: s['begTime'])
            })
        return res

    def create_schedules(self, data):
        data = self._map_sheds_data(data)
        dates = [day['date'] for day in data]

        ok, msg = delete_schedules(dates, self.person.id)
        if not ok:
            raise ApiException(422, msg)

        self._changed = create_schedules(self.person, data, strict=False)
        return min(dates), max(dates)

    def as_json(self):
        res = []
        for date in sorted(self.schedules.keys()):
            res.append({
                'date': date,
                'intervals': [
                    {
                        'begin_time': format_time(sched.begTime),
                        'end_time': format_time(sched.endTime),
                        'quantity': sched.numTickets
                    }
                    for sched in self.schedules[date]
                ]
            })
        return res


class Schedule2XForm(Schedule2Schema, XForm):
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
        super(Schedule2XForm, self).__init__(*args, **kwargs)
        self.schedules = {}

    def find_schedules(self, **args):
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
            Schedule.person_id == self.parent_obj_id,
            Schedule.reasonOfAbsence_id.is_(None)
        ).order_by(Schedule.date, Schedule.begTime)
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
