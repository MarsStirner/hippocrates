# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm import lazyload, joinedload

from ..xform import XForm, VALIDATION_ERROR
from .schemas import ScheduleTicketsSchema, ScheduleTicketSchema

from nemesis.models.schedule import ScheduleClientTicket, ScheduleTicket, Schedule, rbAttendanceType,\
    rbReceptionType
from nemesis.models.person import Person
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_time
from nemesis.lib.apiutils import ApiException


logger = logging.getLogger('simple')


class ScheduleTicketsXForm(ScheduleTicketsSchema, XForm):
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
        super(ScheduleTicketsXForm, self).__init__(*args, **kwargs)
        self.person = None
        self.tickets = []

    def init_and_check_params(self, lpu_code, doctor_code, data=None):
        self.person = self.parent_obj = self.find_doctor(doctor_code, lpu_code)
        super(ScheduleTicketsXForm, self).check_params(None, self.person.id, data)

    def find_tickets(self, **args):
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

        query = db.session.query(ScheduleClientTicket).join(
            ScheduleTicket, Schedule
        ).join(
            Person, Schedule.person_id == Person.id
        ).filter(
            ScheduleClientTicket.deleted == 0, ScheduleTicket.deleted == 0, Schedule.deleted == 0,
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
        query = query.with_entities(
            ScheduleClientTicket,
            Schedule.date,
            ScheduleTicket.begTime,
            ScheduleTicket.endTime,
            Person
        ).options(joinedload(Person.organisation, innerjoin=True))
        self.tickets = query.all()

    def as_json(self):
        res = [
            {
                'schedule_ticket_id': ticket[0].id,
                'hospital': self.from_org_rb(ticket[4].organisation if ticket[4] else None),
                'doctor': self.from_person_rb(ticket[4]),
                'patient': str(ticket[0].client_id),
                'date': ticket[1],
                'time_begin': ticket[2],
                'time_end': ticket[3],
            }
            for ticket in self.tickets
        ]
        return res


class ScheduleTicketXForm(ScheduleTicketSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_id_required = False
    target_obj_class = ScheduleClientTicket

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        return ScheduleClientTicket.query.filter(
            ScheduleClientTicket.id == self.target_obj_id,
            ScheduleClientTicket.deleted == 0
        ).options(
            lazyload('*'),
        )

    def convert_and_format(self, data):
        res = {}
        person = self.find_doctor(data['doctor'], data['hospital'])
        patient = self.find_client(data['patient'])
        res.update({
            'schedule_ticket_id': data.get('schedule_ticket_id'),
            'person': person,
            'patient': patient,
            'date': safe_date(data['date']),
            'time_begin': safe_time(data['time_begin']),
            'time_end': safe_time(data['time_end'])
        })
        return res

    def _get_new_sct(self, data):
        rec_type = rbReceptionType.query.filter(rbReceptionType.code == 'amb').first()
        s = Schedule(
            person=data['person'], date=data['date'],
            begTime=data['time_begin'], endTime=data['time_end'],
            numTickets=1, receptionType=rec_type
        )
        attendace = rbAttendanceType.cache().by_code()[u'planned']
        st = ScheduleTicket(
            begTime=data['time_begin'], endTime=data['time_end'],
            attendanceType=attendace
        )
        s.tickets.append(st)
        sct = ScheduleClientTicket(
            ticket=st, client=data['patient'],
            event_id=data.get('event_id')
        )
        return sct

    def _delete_existing_sct(self, sct):
        sct.ticket.schedule.deleted = 1
        sct.ticket.deleted = 1
        sct.deleted = 1
        self._changed.extend([sct.ticket.schedule, sct.ticket, sct])

    def update_target_obj(self, data):
        data = self.convert_and_format(data)
        if self.new:
            sct = self._get_new_sct(data)
        else:
            self.find_target_obj(self.target_obj_id)
            existing_sct = self.target_obj
            sct = self._get_new_sct(data)
            if existing_sct.event_id is not None and existing_sct.client_id == sct.client.id and\
                    existing_sct.ticket.schedule.person_id == sct.ticket.schedule.person_id:
                sct.event_id = existing_sct.event_id
            self._delete_existing_sct(existing_sct)

        self.target_obj = sct
        self._changed.append(sct)

    def delete_target_obj(self):
        self.find_target_obj(self.target_obj_id)
        self._delete_existing_sct(self.target_obj)

    def as_json(self):
        sct = self.target_obj
        st = sct.ticket
        s = st.schedule
        return {
            'schedule_ticket_id': str(sct.id),
            'hospital': self.from_org_rb(s.person.organisation),
            'doctor': self.from_person_rb(s.person),
            'patient': str(sct.client_id),
            'date': s.date,
            'time_begin': st.begTime,
            'time_end': st.endTime,
        }