# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify, ALREADY_PRESENT_ERROR, INTERNAL_ERROR, Undefined
from .schemas import CardSchema

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import check_card_attrs_action_integrity, default_ET_Heuristic, default_AT_Heuristic
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy

from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_event_ext_id, safe_datetime, safe_date
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.client import Client
from nemesis.models.enums import EventPrimary, EventOrder
from nemesis.lib.data import create_action
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class CardXForm(CardSchema, XForm):
    """
    Класс-преобразователь для медицинской карты случая
    """
    target_obj_class = Event
    parent_obj_class = Client
    parent_id_required = False

    def _find_target_obj_query(self):
        return Event.query.join(EventType, rbRequestType).filter(
            Event.id == self.target_obj_id,
            Event.deleted == 0,
            rbRequestType.code == request_type_pregnancy
        )

    def check_duplicate(self, data):
        if self.new:
            q = db.session.query(Event.id).join(Client).filter(
                Client.id == self.parent_obj_id,
                Event.deleted == 0,
                Event.execDate.is_(None)
            )
            q_result = q.first()
            existing_event_id = q_result[0] if q_result else None
            if existing_event_id:
                raise ApiException(
                    ALREADY_PRESENT_ERROR,
                    u'Уже существует открытая карта с id = {0} для пациента с id = {1}'.format(
                        existing_event_id, self.parent_obj_id
                    )
                )

    def get_target_nf_msg(self):
        return u'Не найдена карта с id = {0}'.format(self.target_obj_id)

    def get_parent_nf_msg(self):
        return u'Не найден пациент с id = {0}'.format(self.parent_obj_id)

    def update_target_obj(self, data):
        if self.new:
            self.target_obj = Event()
            self.create_event(data)
        else:
            self.target_obj = self._find_target_obj_query().first()
            self.update_event(data)
        self._changed.append(self.target_obj)

    def update_event(self, data):
        event = self.target_obj
        event.setDate = safe_datetime(safe_date(data['card_set_date']))
        new_doctor = self.find_doctor(data['card_doctor'], data['card_LPU'])
        event.execPerson = new_doctor
        event.execPerson_id = new_doctor.id
        new_org = new_doctor.organisation
        event.organisation = new_org
        event.org_id = new_org.id

    def create_event(self, data):
        event = self.target_obj
        et = default_ET_Heuristic(request_type_pregnancy)
        if et is None:
            raise ApiException(INTERNAL_ERROR, u'Не настроен тип события - Случай беременности ОМС')
        event.eventType = et

        self.parent_obj = self.find_client(data['client_id'])
        event.client = self.parent_obj
        event.client_id = self.parent_obj.id
        event.setDate = safe_datetime(safe_date(data['card_set_date']))
        new_doctor = self.find_doctor(data['card_doctor'], data['card_LPU'])
        event.execPerson = new_doctor
        event.execPerson_id = new_doctor.id
        new_org = new_doctor.organisation
        event.organisation = new_org
        event.org_id = new_org.id

        event.orgStructure = new_doctor.org_structure
        event.isPrimaryCode = EventPrimary.primary[0]
        event.order = EventOrder.planned[0]
        event.note = ''
        event.externalId = get_new_event_ext_id(event.eventType.id, event.client_id)
        event.payStatus = 0

    def update_card_attrs(self):
        self.pcard = PregnancyCard.get_for_event(self.target_obj)
        if self.new:
            self.create_ca_action()
        else:
            check_card_attrs_action_integrity(self.pcard.attrs)
        self.pcard.reevaluate_card_attrs()
        self._changed.append(self.pcard.attrs)

    def create_ca_action(self):
        self.pcard = PregnancyCard.get_for_event(self.target_obj)
        at = default_AT_Heuristic(self.target_obj.eventType)
        if not at:
            raise ApiException(INTERNAL_ERROR, u'Нет типа действия с flatCode = cardAttributes')
        ca_action = create_action(at, self.target_obj)
        self.pcard._card_attrs_action = ca_action

    def delete_target_obj(self):
        self.target_obj_class.query.filter(
            self.target_obj_class.id == self.target_obj_id,
        ).update({'deleted': 1})

    @wrap_simplify
    def as_json(self):
        event = self.target_obj
        return {
            'card_id': event.id,
            'client_id': event.client_id,
            'card_set_date': safe_date(event.setDate),
            'card_doctor': self.from_person_rb(event.execPerson),
            "card_LPU": self.from_org_rb(event.organisation)
        }
