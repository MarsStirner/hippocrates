# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify
from .schemas import AppointmentListSchema, AppointmentSchema

from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from nemesis.models.actions import Action
from nemesis.systemwide import db
from nemesis.lib.utils import format_time


logger = logging.getLogger('simple')


class AppointmentListXForm(AppointmentListSchema, XForm):
    target_id_required = False
    parent_obj_class = Event

    def __init__(self, *args, **kwargs):
        XForm.__init__(self, *args, **kwargs)
        self.appointment_list = []

    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        pass

    def find_appointments(self):
        query = db.session.query(EventMeasure).join(
            Action, EventMeasure.appointmentAction_id == Action.id
        ).filter(
            EventMeasure.deleted == 0,
            Action.deleted == 0,
            EventMeasure.event_id == self.parent_obj_id
        ).with_entities(Action)
        self.appointment_list = query.all()

    @wrap_simplify
    def as_json(self):
        return [str(appointment.id) for appointment in self.appointment_list]


class AppointmentXForm(AppointmentSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    @wrap_simplify
    def as_json(self):
        action = self.target_obj
        res = {
            'measure_code': action.em_appointment.measure.code,
            'diagnosis': self.or_undefined(self.from_mkb_rb(self._get_prop_val(action, 'DiagnosisDirection'))),
            'time': self.or_undefined(format_time(self._get_prop_val(action, 'time'))),
            'date': self.or_undefined(self._get_prop_val(action, 'date')),
            'parameters': self.or_undefined(self._get_prop_val(action, 'additional')),
            'referral_lpu': self.or_undefined(self.from_org_rb(self._get_prop_val(action, 'LPUDirection'))),
            'referral_date': self.or_undefined(self._get_prop_val(action, 'DateDirection')),
            'comment': self.or_undefined(self._get_prop_val(action, 'Comment')),
            'appointed_lpu': self.or_undefined(getattr(self._get_prop_val(action, 'Doctor'), 'org_id', None)),
            'appointed_doctor': self.or_undefined(action.modifyPerson_id),
        }
        return res

    def _get_prop_val(self, action, code):
        if code in action.propsByCode:
            return action.propsByCode[code].value
