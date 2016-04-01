# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify
from .schemas import CardSchema

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.card_attrs import check_card_attrs_action_integrity
from blueprints.risar.views.api.chart import default_AT_Heuristic, default_ET_Heuristic
from nemesis.models.enums import EventPrimary, EventOrder

from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_event_ext_id, safe_datetime, safe_date
from nemesis.models.event import Event
from nemesis.lib.data import create_action



logger = logging.getLogger('simple')


class CardXForm(XForm, CardSchema):
    """
    Класс-преобразователь для медицинской карты случая
    """

    def __init__(self):
        self.event = None
        self.pcard = None
        self.new = False

    @property
    def ca_action(self):
        return self.pcard.attrs if self.pcard is not None else None

    def _find_event_query(self, event_id):
        return Event.query.filter(Event.id == event_id, Event.deleted == 0)

    def find_card(self, card_id=None, data=None):
        if card_id is None:
            # Ручная валидация
            if data is None:
                raise Exception('CardXForm.find_card called for creation without "data"')

            event = Event()
            self.new = True
        else:
            event = self._find_event_query(card_id).first()
            if not event:
                raise ApiException(404, u'Карта с id = {0} не найдена'.format(card_id))
        self.event = event

    def update_card(self, data):
        # with db.session.no_autoflush:
        if self.new:
            self.create_event(data)
        else:
            self.update_event(data)

    def update_event(self, data):
        self.event.setDate = safe_datetime(data['card_set_date'])
        new_doctor = self.find_doctor('card_doctor')
        self.event.execPerson = new_doctor
        self.event.execPerson_id = new_doctor.id
        new_org = self.find_org(data['card_LPU'])
        self.event.organisation = new_org
        self.event.org_id = new_org.id

        self.pcard = PregnancyCard.get_for_event(self.event)
        check_card_attrs_action_integrity(self.pcard.attrs)

    def create_event(self, data):
        event = self.event
        et = default_ET_Heuristic()
        if et is None:
            raise ApiException(500, u'Не настроен тип события - Случай беременности ОМС')
        event.eventType = et

        client = self.find_client(data['client_id'])
        event.client = client
        event.cleint_id = client.id
        event.setDate = safe_datetime(data['card_set_date'])
        new_doctor = self.find_doctor(data['card_doctor'])
        event.execPerson = new_doctor
        event.execPerson_id = new_doctor.id
        new_org = self.find_org(data['card_LPU'])
        event.organisation = new_org
        event.org_id = new_org.id

        event.orgStructure = new_doctor.org_structure
        event.isPrimaryCode = EventPrimary.primary[0]
        event.order = EventOrder.planned[0]
        event.note = ''
        event.externalId = get_new_event_ext_id(event.eventType.id, client.id)
        event.payStatus = 0

    def update_card_attrs(self):
        # with db.session.no_autoflush:
        if self.new:
            self.create_ca_action()

        self.pcard.reevaluate_card_attrs()

    def create_ca_action(self):
        self.pcard = PregnancyCard.get_for_event(self.event)
        at = default_AT_Heuristic()
        if not at:
            raise ApiException(500, u'Нет типа действия с flatCode = cardAttributes')
        ca_action = create_action(at.id, self.event)
        self.pcard._card_attrs_action = ca_action

    @wrap_simplify
    def as_json(self):
        event = self.event
        return {
            'card_id': event.id,
            'client_id': event.client_id,
            'card_set_date': safe_date(event.setDate),
            'card_doctor': event.execPerson.regionalCode,  # TODO: what code
            "card_LPU": event.organisation.TFOMSCode
        }
