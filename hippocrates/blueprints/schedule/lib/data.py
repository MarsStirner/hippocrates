# -*- coding: utf-8 -*-

import datetime

from nemesis.lib.utils import safe_date, safe_time_as_dt, safe_traverse, format_date
from nemesis.models.schedule import (Schedule, ScheduleTicket, ScheduleClientTicket,
    rbReasonOfAbsence, rbAttendanceType, QuotingByTime)
from nemesis.lib.apiutils import ApiException


def delete_schedules(dates, person_id):
    schedules = Schedule.query.filter(
        Schedule.person_id == person_id, Schedule.date.in_(dates),
    )
    if not schedules.count():
        return True, ''
    schedules_with_clients = schedules.join(ScheduleTicket).join(ScheduleClientTicket).filter(
        Schedule.deleted == 0,
        ScheduleClientTicket.client_id is not None,
        ScheduleClientTicket.deleted == 0
    ).all()
    if schedules_with_clients:
        return False, u'Пациенты успели записаться на приём'

    schedules.update({
        Schedule.deleted: 1,
    }, synchronize_session=False)

    ScheduleTicket.query.filter(
        ScheduleTicket.schedule_id.in_([s.id for s in schedules])
    ).update({
        ScheduleTicket.deleted: 1
    }, synchronize_session=False)
    return True, ''


def _make_default_ticket(schedule):
    ticket = ScheduleTicket()
    ticket.schedule = schedule
    return ticket


def _make_tickets(schedule, planned, extra, cito):
    res = []
    # here cometh another math
    dt = (datetime.datetime.combine(schedule.date, schedule.endTime) -
          datetime.datetime.combine(schedule.date, schedule.begTime)) / planned
    it = schedule.begTimeAsDt
    attendanceType = rbAttendanceType.cache().by_code()[u'planned']
    for i in xrange(planned):
        ticket = _make_default_ticket(schedule)
        begDateTime = datetime.datetime.combine(schedule.date, it.time())
        ticket.begTime = begDateTime.time()
        ticket.endTime = (begDateTime + dt).time()
        ticket.attendanceType = attendanceType
        it += dt
        res.append(ticket)

    if extra:
        attendanceType = rbAttendanceType.cache().by_code()[u'extra']
        for i in xrange(extra):
            ticket = _make_default_ticket(schedule)
            ticket.attendanceType = attendanceType
            res.append(ticket)

    if cito:
        attendanceType = rbAttendanceType.cache().by_code()[u'CITO']
        for i in xrange(cito):
            ticket = _make_default_ticket(schedule)
            ticket.attendanceType = attendanceType
            res.append(ticket)

    return res


def create_schedules(person, schedules_data, strict=True):
    person_id = person.id

    res = []
    for day_desc in schedules_data:
        date = safe_date(day_desc['date'])
        roa = day_desc.get('roa')

        if roa:
            new_sched = Schedule()
            new_sched.person_id = person_id
            new_sched.date = date
            new_sched.reasonOfAbsence = rbReasonOfAbsence.query.\
                filter(rbReasonOfAbsence.code == roa['code']).first()
            new_sched.begTime = '00:00'
            new_sched.endTime = '00:00'
            new_sched.numTickets = 0
            res.append(new_sched)
        else:
            for sub_sched in day_desc['scheds']:
                new_sched = Schedule()
                new_sched.person_id = person_id
                new_sched.date = date
                new_sched.begTimeAsDt = safe_time_as_dt(sub_sched['begTime'])
                new_sched.begTime = new_sched.begTimeAsDt.time()
                new_sched.endTimeAsDt = safe_time_as_dt(sub_sched['endTime'])
                new_sched.endTime = new_sched.endTimeAsDt.time()
                new_sched.receptionType_id = safe_traverse(sub_sched, 'reception_type', 'id')
                new_sched.finance_id = safe_traverse(sub_sched, 'finance', 'id')
                office_id = safe_traverse(sub_sched, 'office', 'id')
                if not office_id and strict and \
                        safe_traverse(sub_sched, 'reception_type', 'code') == 'amb':
                    raise ApiException(422, u'На %s не указан кабинет' % format_date(date))
                new_sched.office_id = office_id
                planned_count = sub_sched.get('planned')
                if not planned_count:
                    raise ApiException(422, u'На %s указаны интервалы с нулевым планом' % format_date(date))
                new_sched.numTickets = planned_count

                new_tickets = _make_tickets(new_sched, planned_count,
                                            sub_sched.get('extra', 0), sub_sched.get('CITO', 0))
                res.extend(new_tickets)

    return res


def create_time_quotas(person, quotas):
    person_id = person.id
    res = []
    for quota_desc in quotas:
        date = safe_date(quota_desc['date'])
        QuotingByTime.query.filter(QuotingByTime.doctor_id == person_id,
                                   QuotingByTime.quoting_date == date).delete()
        new_quotas = quota_desc['day_quotas']
        for quota in new_quotas:
            quota_record = QuotingByTime()
            quota_record.quoting_date = date
            quota_record.doctor_id = person_id
            quota_record.QuotingTimeStart = safe_time_as_dt(quota['time_start'])
            quota_record.QuotingTimeEnd = safe_time_as_dt(quota['time_end'])
            quota_record.quotingType_id = quota['quoting_type']['id']
            res.append(quota_record)
    return res