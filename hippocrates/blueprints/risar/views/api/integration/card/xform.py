# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, and_, func
from ..xform import XForm, wrap_simplify, ALREADY_PRESENT_ERROR, INTERNAL_ERROR, Undefined
from .schemas import CardSchema

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import default_ET_Heuristic, default_AT_Heuristic
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy, request_type_gynecological, \
    pregnancy_card_attrs

from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_event_ext_id, safe_datetime, safe_date
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType, MKB
from nemesis.models.client import Client
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
from nemesis.models.diagnosis import Diagnosis, Diagnostic
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
    ginek_event_type_code = '97'  # Гинекологический приём (ОМС)
    pregn_event_type_code = '98'  # Случай беременности (ОМС)

    def _find_target_obj_query(self):
        return Event.query.join(EventType, rbRequestType).filter(
            Event.id == self.target_obj_id,
            Event.deleted == 0,
            rbRequestType.code == request_type_pregnancy
        )

    def _find_list_query(self):
        return Event.query.join(EventType, rbRequestType).filter(
            Event.deleted == 0,
            or_(
                Event.execDate == None,
                Event.result_id == None,
            ),
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

    def find_target(self):
        self.target_obj = self._find_target_obj_query().first()

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
        # работа метода пока только по беременным картам
        et = default_ET_Heuristic(request_type_pregnancy)
        # if data.get('pregnant'):
        #     et = default_ET_Heuristic(request_type_pregnancy)
        # else:
        #     et = default_ET_Heuristic(request_type_gynecological)
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
            "card_LPU": self.from_org_rb(event.organisation),
            # "pregnant": event.eventType.code == self.pregn_event_type_code,
            # работа метода пока только по беременным картам
            "pregnant": True,
        }

    def get_list(self, filters=None):
        q = self._find_list_query()
        filters = filters or {}
        if 'id' in filters:
            q = q.filter(
                self.target_obj_class.id == filters['id']
            )
        if 'pregnancyWeek' in filters:
            q = self._get_filtered_by_preg_week_events_query()
        return q.all()

    def _get_filtered_by_preg_week_events_query(self):
        # main query
        query = self._find_list_query()
        query = query.join(Action, ActionType).filter(
            Action.deleted == 0, ActionType.flatCode == pregnancy_card_attrs
        )

        # event pregnancy start date
        q_event_psd = self._find_list_query().join(
            Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'pregnancy_start_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('psd')
        ).subquery('EventPregnancyStartDate')

        # event predicted delivery date
        q_event_pdd = self._find_list_query().join(
            Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'predicted_delivery_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('pdd')
        ).subquery('EventPredictedDeliveryDate')

        # diags queries
        q_diags_main = db.session.query(Diagnostic).join(Diagnosis).join(
            Event, Event.client_id == Diagnosis.client_id,
        ).filter(
            Diagnosis.deleted == 0, Diagnostic.deleted == 0,
        ).group_by(Diagnostic.diagnosis_id)
        max_diagn_dates_sq = q_diags_main.with_entities(
            func.max(Diagnostic.setDate).label('set_date'),
            Diagnostic.diagnosis_id.label('diagnosis_id')
        ).subquery()
        diagn_ids_sq = q_diags_main.join(
            max_diagn_dates_sq, and_(Diagnostic.setDate == max_diagn_dates_sq.c.set_date,
                                     Diagnostic.diagnosis_id == max_diagn_dates_sq.c.diagnosis_id)
        ).with_entities(
            func.max(Diagnostic.id).label('diagnostic_id'),
        ).subquery()

        q_diags = db.session.query(Diagnostic).join(
            diagn_ids_sq, diagn_ids_sq.c.diagnostic_id == Diagnostic.id
        ).join(Diagnosis).join(
            MKB, Diagnostic.MKB == MKB.DiagID,
        ).with_entities(
            Diagnosis.id.label('diagnosis_id'), Diagnosis.client_id.label('client_id'),
            Diagnosis.setDate.label('ds_set_date'), Diagnosis.endDate.label('ds_end_date'),
            MKB.DiagID.label('mkb')
        ).group_by(
            Diagnosis.id
        ).subquery('ClientDiags')

        # final main query
        fltrd_q = query.join(
            q_event_pdd, Event.id == q_event_pdd.c.event_id
        ).join(
            q_event_psd, Event.id == q_event_psd.c.event_id
        ).outerjoin(
            q_diags, and_(q_diags.c.client_id == Event.client_id,
                          q_diags.c.ds_set_date <= func.coalesce(Event.execDate, func.curdate()),
                          func.coalesce(q_diags.c.ds_end_date, func.curdate()) >= Event.setDate)
        ).filter(
            or_(
                # неделя беременности = 32
                func.floor(
                    func.datediff(
                        func.IF(func.coalesce(q_event_pdd.c.pdd, func.curdate()) < func.curdate(),
                                q_event_pdd.c.pdd,
                                func.curdate()),
                        q_event_psd.c.psd
                    ) / 7
                ) + 1 == 32,
                # неделя беременности = 28 и есть действующий диагноз мкб O30.xx (двойня)
                and_(
                    func.floor(
                        func.datediff(
                            func.IF(func.coalesce(q_event_pdd.c.pdd, func.curdate()) < func.curdate(),
                                    q_event_pdd.c.pdd,
                                    func.curdate()),
                            q_event_psd.c.psd
                        ) / 7
                    ) + 1 == 28,
                    q_diags.c.diagnosis_id.isnot(None),
                    q_diags.c.mkb.like(u'O30.%')
                )
            )
        ).with_entities(Event.id.distinct().label('event_id')).subquery('FilteredEvents')
        query = db.session.query(Event).join(
            fltrd_q, Event.id == fltrd_q.c.event_id
        )
        return query
