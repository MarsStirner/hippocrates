# -*- coding: utf-8 -*-

import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ..xform import XForm
from .schemas import ScheduleTicketsSchema


from nemesis.models.event import Event
from nemesis.models.schedule import ScheduleClientTicket, ScheduleTicket, Schedule
from nemesis.models.person import Person
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class ScheduleTicketsXForm(ScheduleTicketsSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_id_required = False

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        pass

    def __init__(self, *args, **kwargs):
        super(ScheduleTicketsXForm, self).__init__(*args, **kwargs)
        self.tickets = []

    def find_tickets(self):
        if not self.parent_obj:
            self.find_parent_obj(self.parent_obj_id)

        event = self.parent_obj
        query = db.session.query(ScheduleClientTicket).join(
            ScheduleTicket, Schedule, Schedule.person
        ).filter(
            ScheduleClientTicket.deleted == 0,
            ScheduleTicket.deleted == 0,
            Schedule.deleted == 0,
            ScheduleClientTicket.client_id == event.client_id,
        )
        # дата-вемя начала талона попадает в диапазон даты-времени карты случая
        query = query.filter(
            func.STR_TO_DATE(func.CONCAT(Schedule.date, ' ', ScheduleTicket.begTime),
                             '%Y-%m-%d %H:%i:%s') >= event.setDate
        )
        if event.execDate:
            query = query.filter(
                func.STR_TO_DATE(func.CONCAT(Schedule.date, ' ', ScheduleTicket.begTime),
                                 '%Y-%m-%d %H:%i:%s') <= event.execDate
            )

        query = query.with_entities(
            ScheduleClientTicket.id,
            Schedule.date,
            ScheduleTicket.begTime,
            Person
        ).options(joinedload(Person.organisation, innerjoin=True))
        self.tickets = query.all()

    def as_json(self):
        self.find_tickets()

        res = [
            {
                'schedule_ticket_id': ticket[0],
                'hospital': self.from_org_rb(ticket[3].organisation if ticket[3] else None),
                'doctor': self.from_person_rb(ticket[3]),
                'date': ticket[1],
                'time': ticket[2],
            }
            for ticket in self.tickets
        ]
        return res
