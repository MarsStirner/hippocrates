# -*- coding: utf-8 -*-

import logging

from ..xform import (XForm, wrap_simplify, VALIDATION_ERROR, ALREADY_PRESENT_ERROR,
     NOT_FOUND_ERROR, MIS_BARS_CODE, Undefined)
from .schemas import ConciliumSchema

from hippocrates.blueprints.risar.lib.concilium import get_concilium_by_id, update_concilium
from hippocrates.blueprints.risar.models.risar import RisarConcilium, RisarConcilium_Identification

from nemesis.lib.utils import safe_date, safe_bool_none, safe_int
from nemesis.lib.apiutils import ApiException
from nemesis.models.event import Event
from nemesis.models.exists import rbAccountingSystem
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class ConciliumXForm(ConciliumSchema, XForm):
    """
    Класс-преобразователь для консилиумов
    """
    target_obj_class = RisarConcilium
    parent_obj_class = Event

    def __init__(self, *args, **kwargs):
        XForm.__init__(self, *args, **kwargs)
        self.external_id = None
        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).first()

    def _find_target_obj_query(self):
        q = RisarConcilium.query.filter(
            RisarConcilium.event_id == self.parent_obj_id
        )
        if self.target_obj_id:
            q = q.filter(self.target_obj_class.id == self.target_obj_id)
        return q

    def check_duplicate(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'для check_duplicate необходим "external_id"'
            )
        q = self._find_target_obj_query().join(
            RisarConcilium_Identification
        ).join(rbAccountingSystem).filter(
            RisarConcilium_Identification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if target_obj_exist:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует консилиум с внешним id = {0}'.format(self.external_id)
            )

    def check_external_id(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'для check_external_id необходим "external_id"'
            )
        q = RisarConcilium_Identification.query.join(rbAccountingSystem).filter(
            RisarConcilium_Identification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
            RisarConcilium_Identification.concilium_id == self.target_obj_id,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if not target_obj_exist:
            raise ApiException(
                NOT_FOUND_ERROR,
                u'Не найден консилиум с id = {0} и внешним id = {1}'.format(self.target_obj_id, self.external_id)
            )

    def get_target_nf_msg(self):
        return u'Не найден консилиум с id = {0}'.format(self.target_obj_id)

    def get_parent_nf_msg(self):
        return u'Не найдена карта с id = {0}'.format(self.parent_obj_id)

    def convert_and_format(self, data):
        res = {}
        org_code = data['hospital']
        org = self.find_org(org_code)
        doctor = self.find_doctor(data['doctor'], org_code)
        mkb = self.find_mkb(data['diagnosis'])
        res.update({
            'hospital': org,
            'hospital_id': org.id,
            'doctor': doctor,
            'doctor_id': doctor.id,
            'mkb_id': mkb.id,
            'mkb': mkb
        })
        res.update({
            'date': safe_date(data['date']),
            'patient_presence': safe_int(safe_bool_none(data.get('patient_presence'))),
            'reason': data.get('reason') or '',
            'patient_condition': data.get('patient_condition'),
            'decision': data.get('decision') or '',
        })

        members = []
        for member in data.get('doctors', []):
            doc = self.find_doctor(member['doctor'], org_code)
            members.append({
                'person_id': doc.id,
                'person': doc,
                'opinion': member.get('opinion')
            })
        res.update(members=members)
        return res

    def update_target_obj(self, data):
        data = self.convert_and_format(data)

        event = self.parent_obj = self.find_event(self.parent_obj_id)
        concilium = self.target_obj = get_concilium_by_id(
            self.target_obj_id, event, True
        )

        changed, deleted = update_concilium(concilium, data)
        self._changed.extend(changed)
        self._deleted.extend(deleted)
        self.save_external_data()

    def save_external_data(self):
        if self.new:
            external_ident = RisarConcilium_Identification(
                concilium_id=self.target_obj_id,
                external_id=self.external_id,
                external_system_id=self.external_system.id,
                concilium=self.target_obj,
                external_system=self.external_system
            )
            self._changed.append(external_ident)

    def delete_external_data(self):
        RisarConcilium_Identification.query.filter(
            RisarConcilium_Identification.concilium_id == self.target_obj_id,
            RisarConcilium_Identification.external_id == self.external_id,
            RisarConcilium_Identification.external_system_id == self.external_system.id,
        ).delete()

    def delete_target_obj(self):
        # db cascade deletes of RisarConcilium_Members and RisarConcilium_Identification
        db.session.query(self.target_obj_class).filter(
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.event_id == self.parent_obj_id
        ).delete()

        self.delete_external_data()

    @wrap_simplify
    def as_json(self):
        concilium = self.target_obj
        return {
            'concilium_id': concilium.id,
            'external_id': self.external_id,
            'date': concilium.date,
            'hospital': self.from_org_rb(concilium.hospital),
            'doctor': self.from_person_rb(concilium.doctor),
            'patient_presence': self.or_undefined(safe_bool_none(concilium.patient_presence)),
            'diagnosis': self.from_mkb_rb(concilium.mkb),
            'reason': concilium.reason,
            'patient_condition': self.or_undefined(concilium.patient_condition),
            'decision': concilium.decision,
            'doctors': self._represent_concilium_members()
        }

    def _represent_concilium_members(self):
        members = self.target_obj.members
        return [
            {
                'doctor': self.from_person_rb(member.person),
                'opinion': self.or_undefined(member.opinion)
            }
            for member in members
        ]
