# -*- coding: utf-8 -*-

from blueprints.risar.lib.utils import format_action_data

from nemesis.systemwide import db
from nemesis.models.enums import MeasureStatus
from nemesis.lib.data import create_action, update_action


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

    def get_new_appointment(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.scheme_measure.measure.appointmentAt_id
        appointment = create_action(action_type_id, event_id, properties=action_props, data=action_data)
        return appointment

    def create_appointment(self, em, json_data):
        json_data = format_action_data(json_data)
        if 'properties' in json_data:
            props = json_data.pop('properties')
        else:
            props = []
        appointment = self.get_new_appointment(em, json_data, props)
        em.appointment_action = appointment
        self.make_assigned(em)
        return appointment

    def update_appointment(self, em, appointment, json_data):
        json_data = format_action_data(json_data)
        appointment = update_action(appointment, **json_data)
        em.appointment_action = appointment
        return appointment

    def get_new_em_result(self, em, action_data=None, action_props=None):
        event_id = em.event_id
        action_type_id = em.scheme_measure.measure.resultAt_id
        em_result = create_action(action_type_id, event_id, properties=action_props, data=action_data)
        return em_result

    def create_em_result(self, em, json_data):
        json_data = format_action_data(json_data)
        if 'properties' in json_data:
            props = json_data.pop('properties')
        else:
            props = []
        em_result = self.get_new_em_result(em, json_data, props)
        em.result_action = em_result
        self.make_assigned(em)
        return em_result

    def update_em_result(self, em, em_result, json_data):
        json_data = format_action_data(json_data)
        em_result = update_action(em_result, **json_data)
        em.result_action = em_result
        return em_result

    def store(self, *entity_list):
        db.session.add_all(entity_list)
        db.session.commit()
