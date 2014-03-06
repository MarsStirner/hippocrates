# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import itertools

from blueprints.schedule.models.schedule import ScheduleTicket, ScheduleClientTicket, Schedule, rbReceptionType


__author__ = 'mmalkov'


class Format:
    JSON = 0
    HTML = 1


class ScheduleVisualizer(object):
    def __init__(self):
        self.reception_type = None
        self.client_id = None
        self.reception_types = [at.code for at in rbReceptionType.query]

    def make_ticket(self, ticket):
        client_id = ticket.client_id
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client_id else 'free',
            'client': ticket.client.shortNameText if client_id else None,
            'attendance_type': ticket.attendanceType,
        }

    def make_day(self, schedule):
        return {
            'id': schedule.id,
            'office': schedule.office,
            'tickets': [
                self.make_ticket(ticket)
                for ticket in schedule.tickets
                if not (self.client_id and ticket.client_id != self.client_id)
            ],
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
        }

    def make_person(self, person):
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_schedule(self, schedules, date_start, date_end, expand=False):
        one_day = datetime.timedelta(days=1)

        def new_rt():
            date_iter = date_start
            rt_group = []
            while date_iter < date_end:
                rt_group.append({
                    'date': date_iter,
                    'scheds': []
                })
                date_iter += one_day
            return {
                'max_tickets': 0,
                'schedule': rt_group,
            }
        if self.reception_type:
            result = {self.reception_type: new_rt()}
        else:
            result = dict((rt, new_rt()) for rt in self.reception_types)

        for schedule in schedules:
            if schedule.receptionType.code in result:
                result[schedule.receptionType.code]['schedule'][(schedule.date - date_start).days]['scheds'].\
                    append(self.make_day(schedule))

        for group in result.itervalues():
            group['max_tickets'] = max(
                sum(
                    len(sched['tickets'])
                    for sched in day['scheds']
                )
                for day in group['schedule']
            )

        for group in result.itervalues():
            for day in group['schedule']:
                if expand:
                    planned = 0
                    CITO = 0
                    extra = 0
                    busy = False
                    roa = None
                    for ticket in itertools.chain(*(sched['tickets'] for sched in day['scheds'])):
                        at = ticket['attendance_type'].code
                        if at == 'planned':
                            planned += 1
                        elif at == 'CITO':
                            CITO += 1
                        elif at == 'extra':
                            extra += 1
                        if not busy and ticket['client']:
                            busy = True
                    for sched in day['scheds']:
                        if not roa and sched['roa']:
                            roa = sched['roa']
                            break
                        del sched['roa']
                    day['summary'] = {
                        'planned_tickets': planned,
                        'CITO_tickets': CITO,
                        'extra_tickets': extra,
                        'busy_tickets': busy,
                    }
                    day['roa'] = roa
                else:
                    tickets = list(itertools.chain(*(sched['tickets'] for sched in day['scheds'])))
                    planned_tickets = sorted(filter(lambda t: t['attendance_type'].code == 'planned', tickets), key=lambda t: t['begDateTime'])
                    extra_tickets = filter(lambda t: t['attendance_type'].code == 'extra', tickets)
                    CITO_tickets = filter(lambda t: t['attendance_type'].code == 'CITO', tickets)
                    day['tickets'] = CITO_tickets + planned_tickets + extra_tickets
                    del day['scheds']
        return result

    def make_persons_schedule(self, persons, start_date, end_date, expand=False):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule(
                Schedule.query.filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date),
                start_date, end_date, expand
            )} for person in persons]

    def make_sched_description(self, schedule):
        planned = 0
        CITO = 0
        extra = 0
        busy = False
        for ticket in schedule.tickets:
            at = ticket.attendanceType.code
            if at == 'planned':
                planned += 1
            elif at == 'CITO':
                CITO += 1
            elif at == 'extra':
                extra += 1
            if not busy and ticket.client_ticket:
                busy = True
        return {
            'id': schedule.id,
            'office': schedule.office,
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
        }

    def collapse_scheds_description(self, scheds):
        planned = 0
        CITO = 0
        extra = 0
        roa = None
        busy = False
        office = None
        mini_scheds = []
        for sched in scheds:
            if not roa and sched['roa']:
                roa = sched['roa']
            if not busy and sched['busy']:
                busy = True
            if not office and sched['office']:
                office = sched['office']
            planned += sched['planned']
            CITO += sched['CITO']
            extra += sched['extra']
            mini_scheds.append({
                'begTime': sched['begTime'],
                'endTime': sched['endTime'],
            })
        return {
            'scheds': mini_scheds if not roa else [],
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'roa': roa,
            'office': office,
        }

    def make_schedule_description(self, schedules, date_start, date_end):
        one_day = datetime.timedelta(days=1)

        def new_rt():
            date_iter = date_start
            rt_group = []
            while date_iter < date_end:
                rt_group.append({
                    'date': date_iter,
                    'scheds': []
                })
                date_iter += one_day
            return {
                'max_tickets': 0,
                'schedule': rt_group,
            }
        result = dict((rt, new_rt()) for rt in self.reception_types)

        for schedule in schedules:
            if schedule.receptionType.code in result:
                result[schedule.receptionType.code]['schedule'][(schedule.date - date_start).days]['scheds'].\
                    append(self.make_sched_description(schedule))

        for group in result.itervalues():
            for day in group['schedule']:
                day.update(self.collapse_scheds_description(day['scheds']))

        return result

    def make_persons_schedule_description(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule_description(
                Schedule.query.filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date),
                start_date, end_date
            )} for person in persons]


class ClientVisualizer(object):
    def __init__(self, mode=Format.JSON):
        self.__mode = mode

    def make_client_info(self, client):

        socStatuses = [{'class': socStatus.soc_status_class.name,
                        'type': socStatus.name,
                        'begDate': socStatus.begDate.strftime('%d-%m-%Y') if socStatus.begDate else '',
                        'endDate': socStatus.endDate.strftime('%d-%m-%Y') if socStatus.endDate else ''
                        } for socStatus in client.socStatuses]
        allergies = [{'nameSubstance': allergy.name,
                      'power': allergy.power,
                      'createDate': allergy.createDate.strftime('%d-%m-%Y') if allergy.createDate else '',
                      'notes': allergy.notes
                      } for allergy in client.allergies]

        intolerances = [{'nameMedicament': intolerance.name,
                         'power': intolerance.power,
                         'createDate': intolerance.createDate.strftime('%d-%m-%Y') if allergy.createDate else '',
                         'notes': intolerance.notes
                         } for intolerance in client.intolerances]
        bloodHistory = [{'bloodGroup': blood.bloodType.name,
                         'bloodDate': blood.bloodDate.strftime('%d-%m-%Y') if blood.bloodDate else '',
                         'physician': blood.person,
                         } for blood in client.blood_history]

        document = {'number': client.document.number,
                    'serial': client.document.serial,
                    'date': client.document.date,
                    'endDate': client.document.endDate,
                    'typeCode': client.document.documentType.code,
                    'documentText': client.document} if client.document else {}

        return {
            'id': client.id,
            'lastName': client.lastName,
            'firstName': client.firstName,
            'patrName': client.patrName,
            'nameText': client.nameText,
            'sex': client.sex,
            'SNILS': client.formatted_SNILS or None,
            'document': document,
            'documentText': client.document,
            'birthDate': client.birthDate
                if self.__mode == Format.JSON
                else client.birthDate.strftime('%d-%m-%Y'),
            'regAddress': client.reg_addresses.first(),
            'liveAddress': client.loc_addresses.first(),
            'contact': client.phones,
            'compulsoryPolicy': client.compulsoryPolicy,
            'voluntaryPolicy': client.voluntaryPolicy,
            'socStatuses': socStatuses,
            'allergies': allergies,
            'intolerances': intolerances,
            'boolHistory': bloodHistory
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


class RbVisualizer(object):
    def make_rb_info(self, reference_book):
        reference_book.code
        return {'code': reference_book.code,
                'name': reference_book.name}
