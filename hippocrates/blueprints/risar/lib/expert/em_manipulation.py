# -*- coding: utf-8 -*-

from blueprints.risar.lib.utils import fill_action

from nemesis.systemwide import db
from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action


class EventMeasureController(object):

    def __init__(self):
        pass

    def cancel(self, em):
        em.status = MeasureStatus.cancelled[0]
        return em

    def make_assigned(self, em):
        if em.status == MeasureStatus.created[0]:
            em.status = MeasureStatus.assigned[0]
        return em

    def get_new_appointment(self, em):
        event_id = em.event_id
        action_type_id = em.scheme_measure.measure.appointmentAt_id
        appointment = create_action(action_type_id, event_id)
        return appointment

    def create_appointment(self, em, json_data):
        appointment = self.get_new_appointment(em)
        appointment = fill_action(appointment, json_data)
        em.appointment_action = appointment
        self.make_assigned(em)
        return appointment

    def update_appointment(self, em, appointment, json_data):
        appointment = fill_action(appointment, json_data)
        em.appointment_action = appointment
        return appointment

    def store(self, *entity_list):
        db.session.add_all(entity_list)
        db.session.commit()
