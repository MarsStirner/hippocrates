# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, CheckupsXForm, wrap_simplify
from .schemas import AppointmentListSchema, AppointmentSchema

from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from nemesis.models.actions import Action
from nemesis.systemwide import db


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


class AppointmentXForm(AppointmentSchema, CheckupsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

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
            # 'time': self.or_undefined(self.from_mkb_rb(self._get_prop_val(action, 'Time'))),
            # 'date': self.or_undefined(self.from_mkb_rb(self._get_prop_val(action, 'Date'))),
            # 'parameters': an_props['ReceiptDate'].value,
            # 'referral_lpu': an_props['IssueDate'].value,
            # 'referral_date': self.person.organisation and self.person.organisation.TFOMSCode or '',
            'comment': self.or_undefined(self._get_prop_val(action, 'Comment')),
        }
        return res

    def _get_prop_val(self, action, code):
        if code in action.propsByCode:
            return action.propsByCode[code].value
