# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime

from blueprints.schedule.models.schedule import ScheduleTicket, ScheduleClientTicket


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

    def make_ticket(self, ticket):
        client = ticket.client
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client else 'free',
            'client': client.shortNameText if client else None,
            'attendance_type': ticket.attendanceType.code,
        }

    def make_day(self, schedule):
        if isinstance(schedule, self.EmptyDay):
            return {
                'date': schedule.date,
                'tickets': [],
            }
        else:
            return {
                'id': schedule.id,
                'date': schedule.date,
                'office': schedule.office,
                'tickets': [
                    self.make_ticket(ticket)
                    for ticket in schedule.tickets
                    if not (self.client_id and ticket.client and ticket.client.id != self.client_id) and
                       not (self.attendance_type and ticket.attendanceType.code != self.attendance_type)
                ],
            }

    def make_person(self, person):
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_schedule(self, schedules, date_start, date_end):
        result = []
        one_day = datetime.timedelta(days=1)
        for schedule in schedules:
            while date_start < schedule.date < date_end:
                result.append(self.EmptyDay(date_start))
                date_start += one_day

            result.append(schedule)
            date_start += one_day

        while date_start < date_end:
            result.append(self.EmptyDay(date_start))
            date_start += one_day

        return [self.make_day(s) for s in result]


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
        appointments = client.appointments.join(ScheduleClientTicket.ticket).order_by(ScheduleTicket.begDateTime.desc()).all()
        return map(self.make_record, appointments)

    def make_record(self, record):
        person = record.ticket.schedule.person
        createPerson = record.createPerson
        return {
            'id': record.id,
            'mark': None,
            'begDateTime': record.ticket.begDateTime
                if self.__mode == Format.JSON
                else record.ticket.begDateTime.strftime('%d-%m-%Y %H:%M'),
            'office': record.ticket.schedule.office,
            'person': person.nameText if person else None,
            'createPerson': createPerson.nameText if createPerson else None,
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