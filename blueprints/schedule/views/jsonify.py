# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime

from blueprints.schedule.models.schedule import ScheduleTicket, ScheduleClientTicket, Schedule, rbAttendanceType


__author__ = 'mmalkov'


class Format:
    JSON = 0
    HTML = 1


class ScheduleVisualizer(object):
    class EmptyDay(object):
        def __init__(self, date):
            self.date = date

    def __init__(self):
        self.attendance_type = None
        self.client_id = None
        self.attendance_types = [at.code for at in rbAttendanceType.query]

    def make_ticket(self, ticket):
        client = ticket.client
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client else 'free',
            'client': client.shortNameText if client else None,
            # 'attendance_type': ticket.attendanceType.code,
        }

    def make_day(self, schedule, attendance_type):
        if isinstance(schedule, self.EmptyDay):
            return {
                'date': schedule.date,
                'tickets': [],
            }
        else:
            tickets = [
                self.make_ticket(ticket)
                for ticket in schedule.tickets
                if not (self.client_id and ticket.client and ticket.client.id != self.client_id) and
                   not (attendance_type and ticket.attendanceType.code != attendance_type)
            ]
            return {
                'id': schedule.id,
                'date': schedule.date,
                'office': schedule.office,
                'tickets': tickets,
            } if tickets else {
                'date': schedule.date,
                'tickets': [],
            }

    def make_person(self, person):
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_schedule(self, schedules, date_start, date_end):
        sub_result = []
        one_day = datetime.timedelta(days=1)
        for schedule in schedules:
            while date_start < schedule.date < date_end:
                sub_result.append(self.EmptyDay(date_start))
                date_start += one_day

            sub_result.append(schedule)
            date_start += one_day

        while date_start < date_end:
            sub_result.append(self.EmptyDay(date_start))
            date_start += one_day

        result_schedule = {}
        for at_code in ([self.attendance_type] if self.attendance_type else self.attendance_types):
            grouped_schedule = [
                self.make_day(s, at_code)
                for s in sub_result
            ]
            result_schedule[at_code] = {
                'schedule': grouped_schedule,
                'max_tickets': max([len(day['tickets']) for day in grouped_schedule])
            }

        return result_schedule

    def make_persons_schedule(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule(
                Schedule.query.filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date <= end_date
                ).order_by(Schedule.date),
                start_date, end_date
            )} for person in persons]


class ClientVisualizer(object):
    def __init__(self, mode=Format.JSON):
        self.__mode = mode

    def make_client_info(self, client):
        return {
            'id': client.id,
            'nameText': client.nameText,
            'sex': client.sex,
            'SNILS': client.formatted_SNILS or None,
            'document': client.document,
            'birthDate': client.birthDate
                if self.__mode == Format.JSON
                else client.birthDate.strftime('%d-%m-%Y'),
            'regAddress': client.reg_addresses.first(),
            'liveAddress': client.loc_addresses.first(),
            'contact': client.phones,
            'compulsoryPolicy': client.compulsoryPolicy,
            'voluntaryPolicy': client.voluntaryPolicy,
        }

    def make_records(self, client):
        return map(
            self.make_record,
            client.appointments.
                join(ScheduleClientTicket.ticket).
                filter(ScheduleClientTicket.deleted == 0).
                order_by(ScheduleTicket.begDateTime.desc())
        )

    def make_record(self, record):
        return {
            'id': record.id,
            'mark': None,
            'begDateTime': record.ticket.begDateTime
                if self.__mode == Format.JSON
                else record.ticket.begDateTime.strftime('%d-%m-%Y %H:%M'),
            'office': record.ticket.schedule.office,
            'person': record.ticket.schedule.person,
            'createPerson': record.createPerson,
            'note': record.note,
        }

class PersonTreeVisualizer(object):
    def make_person(self, person):
        return {
            'id': person.id,
            'name': person.shortNameText,
        }

    def make_speciality(self, speciality):
        return {
            'id': speciality.id,
            'name': speciality.name,
            'persons': [],
        }

    def make_tree(self, persons):
        specs = defaultdict(list)
        for person in persons:
            if person.speciality:
                specs[person.speciality.name].append(self.make_person(person))