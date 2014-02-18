# -*- coding: utf-8 -*-
import datetime
from json import JSONEncoder

from blueprints.schedule.models.schedule import ScheduleTicket, ScheduleClientTicket


__author__ = 'mmalkov'


class MyJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        return JSONEncoder.default(self, o)


class Format:
    JSON = 0
    HTML = 1


class ScheduleVisualizer(object):
    class EmptyDay(object):
        def __init__(self, date):
            self.date = date

    def __init__(self):
        self.max_tickets = 0
        self.schedule = []

    def make_ticket(self, ticket):
        client = ticket.client
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client else 'free',
            'client': client.shortNameText if client else None,
            'attendance_type': ticket.attendanceType.code,
        }

    def make_empty_ticket(self):
        return {
            'status': 'empty',
        }

    def make_schedule(self, schedule):
        if isinstance(schedule, self.EmptyDay):
            return {
                'date': schedule.date,
                'tickets': [self.make_empty_ticket()] * self.max_tickets,
            }
        else:
            return {
                'id': schedule.id,
                'date': schedule.date,
                'office': schedule.office,
                'tickets': map(self.make_ticket, schedule.tickets) + [
                    self.make_empty_ticket()
                ] * (self.max_tickets - len(schedule.tickets)),
            }

    def make_person(self, person):
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def push_all(self, schedules, month_f, month_l):
        result = []
        one_day = datetime.timedelta(days=1)
        max_tickets = 0
        for schedule in schedules:
            if len(schedule.tickets) > max_tickets:
                max_tickets = len(schedule.tickets)

            while schedule.date > month_f:
                result.append(self.EmptyDay(month_f))
                month_f += one_day

            result.append(schedule)
            month_f += one_day

        while month_f < month_l:
            result.append(self.EmptyDay(month_f))
            month_f += one_day

        self.max_tickets = max_tickets

        self.schedule = [self.make_schedule(s) for s in result]


class ClientVisualizer(object):
    def __init__(self, mode=Format.JSON):
        self.__mode = mode

    def make_client_info(self, client):
        voluntaryPolicy = client.voluntaryPolicy
        compulsoryPolicy = client.compulsoryPolicy
        return {
            'id': client.id,
            'nameText': client.nameText,
            'sex': client.sex,
            'SNILS': client.formatted_SNILS or None,
            'document': unicode(client.document),
            'birthDate': client.birthDate
                if self.__mode == Format.JSON
                else client.birthDate.strftime('%d-%m-%Y'),
            'regAddress': None,
            'liveAddress': None,
            'contact': client.phones,
            'compulsoryPolicy': unicode(compulsoryPolicy) if compulsoryPolicy else None,
            'voluntaryPolicy': unicode(voluntaryPolicy) if voluntaryPolicy else None,
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