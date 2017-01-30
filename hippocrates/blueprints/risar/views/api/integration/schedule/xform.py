# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm import lazyload, contains_eager

from ..xform import XForm, VALIDATION_ERROR, wrap_simplify, none_default
from .schemas import ScheduleSchema, Schedule2Schema, ScheduleFullSchema

from hippocrates.blueprints.schedule.lib.data import delete_schedules, create_schedules

from nemesis.models.schedule import ScheduleTicket, Schedule, rbReceptionType, rbAttendanceType,\
    ScheduleClientTicket
from nemesis.models.person import Person
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, format_time, safe_dict, safe_time, safe_int, \
    safe_bool
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


class ScheduleFullXForm(ScheduleFullSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_id_required = False
    target_obj_class = Schedule

    def __init__(self, *args, **kwargs):
        super(ScheduleFullXForm, self).__init__(*args, **kwargs)
        self.existing_client_tickets = {}

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        return Schedule.query.filter(
            Schedule.deleted == 0,
            Schedule.id == self.target_obj_id
        ).options(
            lazyload('*')
        )

    def convert_and_format(self, data):
        res = {}
        person = self.find_doctor(data['doctor'], data['hospital'])
        reserve_type_rb = self.rb(data.get('quota_type'), 'rbReserveType') or {}
        res.update({
            'schedule_id': data.get('schedule_id'),
            'person': person,
            'date': safe_date(data['date']),
            'time_begin': safe_time(data['time_begin']),
            'time_end': safe_time(data['time_end']),
            'quantity': data.get('quantity'),
            'reserve_type_id': reserve_type_rb.get('id'),
            'appointment_permited': int(safe_bool(data.get('appointment_permited'))),
        })
        sts = []
        for st_data in data.get('schedule_tickets', []):
            st = {
                'time_begin': safe_time(st_data['time_begin']),
                'time_end': safe_time(st_data['time_end']),
                'patient': None,
                'schedule_ticket_type': safe_int(st_data.get('schedule_ticket_type')) or 1,
                'schedule_ticket_id': safe_int(st_data.get('schedule_ticket_id')),
            }
            if 'patient' in st_data:
                st['patient'] = self.find_client(st_data['patient'])
            sts.append(st)
        res['schedule_tickets'] = sts
        return res

    def create_schedule(self, data):
        rec_type = rbReceptionType.query.filter(rbReceptionType.code == 'amb').first()
        # make main interval
        s = Schedule(
            person=data['person'], date=data['date'],
            begTime=data['time_begin'], endTime=data['time_end'],
            numTickets=data['quantity'], receptionType=rec_type,
            reserve_type_id=data['reserve_type_id'],
            appointment_permitted=data['appointment_permited'],
        )

        # make interval slots
        for st_data in data['schedule_tickets']:
            att_code = u'extra' if st_data['schedule_ticket_type'] else u'planned'
            if att_code == u'planned':
                if not (st_data['time_begin'] and st_data['time_end']):
                    raise ApiException(
                        VALIDATION_ERROR,
                        u'Не указано время начала или окончания слота'
                        u' time_begin=(%s) time_end=(%s) schedule_ticket_id=(%s)' %
                        (st_data['time_begin'], st_data['time_end'],
                         st_data['schedule_ticket_id'])
                    )
            attendance = rbAttendanceType.cache().by_code()[att_code]
            st = ScheduleTicket(
                begTime=st_data['time_begin'], endTime=st_data['time_end'],
                attendanceType=attendance
            )
            s.tickets.append(st)

            # if slot is not empty
            if st_data['patient'] is not None:
                patient = st_data['patient']
                # transfer cards (event_id) from ScheduleClientTickets,
                # that existed before rebuilding
                if patient.id in self.existing_client_tickets:
                    event_id = self.existing_client_tickets[patient.id].pop(0)
                    if len(self.existing_client_tickets[patient.id]) == 0:
                        del self.existing_client_tickets[patient.id]
                else:
                    event_id = None

                sct = ScheduleClientTicket(
                    ticket=st, client=patient,
                    event_id=event_id
                )
                self._changed.append(sct)
        return s

    def _save_existing_client_tickets(self):
        self.existing_client_tickets = {}
        existing_q = ScheduleClientTicket.query.join(
            ScheduleTicket, Schedule
        ).filter(
            ScheduleClientTicket.deleted == 0,
            ScheduleTicket. deleted == 0,
            Schedule.id == self.target_obj_id
        ).options(
            lazyload('*'),
        ).with_entities(
            ScheduleClientTicket.client_id, ScheduleClientTicket.event_id
        )
        for ticket in existing_q:
            self.existing_client_tickets.setdefault(ticket[0], []).append(ticket[1])

    def update_target_obj(self, data):
        data = self.convert_and_format(data)

        if not self.new:
            self._save_existing_client_tickets()
            self.delete_target_obj()

        self.target_obj = self.create_schedule(data)
        self._changed.append(self.target_obj)

    def delete_target_obj(self):
        schedules = self._find_target_obj_query()
        schedule_tickets = ScheduleTicket.query.filter(
            ScheduleTicket.schedule_id == self.target_obj_id
        ).options(
            lazyload('*')
        )

        schedules.update({
            Schedule.deleted: 1,
        }, synchronize_session=False)
        ScheduleTicket.query.filter(
            ScheduleTicket.schedule_id == self.target_obj_id
        ).update({
            ScheduleTicket.deleted: 1
        }, synchronize_session=False)
        ScheduleClientTicket.query.filter(
            ScheduleClientTicket.ticket_id.in_([st.id for st in schedule_tickets])
        ).update({
            ScheduleClientTicket.deleted: 1
        }, synchronize_session=False)

    @wrap_simplify
    def as_json(self):
        schedule = self.target_obj
        return {
            'schedule_id': str(schedule.id),
            'doctor': self.from_person_rb(schedule.person),
            'hospital': self.from_org_rb(schedule.person.organisation),
            'date': schedule.date,
            'time_begin': format_time(schedule.begTime),
            'time_end': format_time(schedule.begTime),
            'quantity': schedule.numTickets,
            'schedule_tickets': self.or_undefined(self._represent_intervals(schedule))
        }

    @none_default
    def _represent_intervals(self, schedule):
        return [
            {
                'schedule_ticket_id': st.id,
                'time_begin': format_time(st.begTime),
                'time_end': format_time(st.begTime),
                'patient': self.or_undefined(st.client_ticket and st.client_ticket.client_id),
            }
            for st in schedule.tickets
        ]
