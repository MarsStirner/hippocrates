# -*- coding: utf-8 -*-

from collections import deque

from sqlalchemy import func, and_
from sqlalchemy.orm import aliased

from blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from blueprints.risar.lib.time_converter import DateTimeUtil
from blueprints.risar.lib.utils import get_action, get_action_list
from blueprints.risar.risar_config import (checkup_flat_codes, risar_mother_anamnesis, risar_epicrisis,
    first_inspection_code, second_inspection_code)
from blueprints.risar.risar_config import request_type_pregnancy
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.lib.utils import safe_date, initialize_name
from nemesis.models.actions import Action
from nemesis.models.enums import CardFillRate


def make_card_fill_timeline(card):
    """Построить таймлайн заполнения карты пациентки.

    Таймлайн представляет собой информацию о наличии определенных сущностей в карте
    пациентки и содержит следующие разделы:
      - анамнез (обязательно)
      - первичный осмотр (обязательно)
      - повторные осмотры - добавляются последовательно на основе имеющихся осмотров, плюс
        1 плановый осмотр. Количество повторных осмотров ограничивается максимальной датой
        случая - датой эпикриза. При наличии эпикриза осмотры позднее него не попадут в выборку, а
        плановый осмотр будет добавляться только, если с момента последнего существующего осмотра
        прошло более `waiting_period` дней.
      - эпикриз - только если имеется дата начала случая

    :param event:
    :return информация по сущностям карты в виде списка элементов, упорядоченных
    по фактической/плановой дате
    """
    event = card.event
    card_attrs_action = card.attrs
    anamnesis = get_action(event, risar_mother_anamnesis)
    inspections = get_action_list(event, checkup_flat_codes).order_by(Action.begDate).all()
    first_inspection = last_inspection = None
    if inspections:
        if inspections[0].actionType.flatCode == first_inspection_code:
            first_inspection = inspections[0]
        last_inspection = inspections[-1]
    epicrisis = get_action(event, risar_epicrisis)
    preg_start_date = card_attrs_action['pregnancy_start_date'].value
    event_start_date = safe_date(event.setDate)
    cur_date = DateTimeUtil.get_current_date()

    inspections_iter = iter(
        (inspection for inspection in inspections
         if inspection.actionType.flatCode == second_inspection_code)
    )

    def get_next_repeated_inspection():
        try:
            return next(inspections_iter)
        except StopIteration:
            return None

    rules = {
        'anamnesis': {
            'waiting_period': 7,
            'get_document': lambda: anamnesis,
            'section_name': u'Анамнез'
        },
        'first_inspection': {
            'waiting_period': 7,
            'get_document': lambda: first_inspection,
            'section_name': u'Первичный осмотр'
        },
        'repeated_inspection': {
            'waiting_period': 30,
            'get_document': get_next_repeated_inspection,
            'section_name': u'Повторный осмотр'
        },
        'epicrisis': {
            'waiting_period': 329,  # 47 недель
            'get_document': lambda: epicrisis,
            'section_name': u'Эпикриз'
        }
    }

    def make_timeline_item(section, planned_date, fill_rate, document, delay_days, inspection_num):
        document_date = safe_date(document.begDate) if document else None
        display_date = planned_date if not document_date else document_date
        preg_week = get_pregnancy_week(event, card_attrs_action, display_date)
        if section not in ('first_inspection', 'repeated_inspection'):
            inspection_num = None
        return {
            'display_date': display_date,
            'planned_date': planned_date,
            'fill_rate': CardFillRate(fill_rate),
            'delay_days': delay_days,
            'preg_week': preg_week,
            'section': section,
            'section_name': rules[section]['section_name'],
            'document': {
                'id': document.id,
                'name': document.actionType.name,
                'beg_date': document.begDate,
                'set_person': document.setPerson,
            } if document else None,
            'inspection_num': inspection_num
        }

    timeline = []
    q = deque()
    q.extend(('anamnesis', 'first_inspection', ))
    if preg_start_date:
        q.append('epicrisis')
    latest_date = event_start_date
    max_date = epicrisis_planned_date = None
    if preg_start_date:
        epicrisis_planned_date = DateTimeUtil.add_to_date(
            preg_start_date, rules['epicrisis']['waiting_period'], DateTimeUtil.day
        )
        epicrisis_date = safe_date(epicrisis.begDate if epicrisis else None)
        max_date = (
            epicrisis_date
            if epicrisis_date and epicrisis_date < epicrisis_planned_date
            else epicrisis_planned_date
        )
    inspection_num = 1
    while len(q):
        section = q.popleft()

        document = rules[section]['get_document']()

        # итерация с текущей датой >= максимальной возможна только для секции эпикриза или
        # для секции повторного осмотра, для которой найдется существующий повторный осмотр;
        # иначе - это плановый повторный осмотр, который будет не обязателен из-за наличия
        # эпикриза планового или фактического
        if max_date and latest_date >= max_date and (
            section != 'epicrisis' and document is None
        ):
            latest_date = max_date
            continue

        document_date = safe_date(document.begDate) if document is not None else None
        if section == 'epicrisis':
            due_date = epicrisis_planned_date
        else:
            due_date = DateTimeUtil.add_to_date(latest_date, rules[section]['waiting_period'], DateTimeUtil.day)

        fill_rate = (
            CardFillRate.filled[0]
            if document is not None else (
                CardFillRate.waiting[0]
                if cur_date <= due_date else CardFillRate.not_filled[0]
            )
        )
        # при наличии документа [-, 0, +]
        # при отсутствии документа: либо 0, если плановая дата еще не прошла, либо +, если плановая дата уже прошла
        delay = (
            (document_date - due_date).days
            if document_date
            else max(0, (cur_date - due_date).days)
        )
        item = make_timeline_item(section, due_date, fill_rate, document, delay, inspection_num)
        timeline.append(item)

        if section in ('first_inspection', 'repeated_inspection') and document is not None:
            latest_date = document_date
            inspection_num += 1
            q.appendleft('repeated_inspection')

    timeline = sorted(timeline, key=lambda t: t['display_date'])

    return timeline


class CFRController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return CFRSelecter()

    def get_doctor_card_fill_rates(self, doctor_id):
        sel = self.get_selecter()
        data = sel.get_doctor_cfrs(doctor_id)
        return {
            'cfr_filled': getattr(data, 'count_cfr_filled', 0),
            'cfr_not_filled': getattr(data, 'count_cfr_nf', 0),
            'cfr_anamnesis_not_filled': getattr(data,'count_cfr_anamnesis_nf', 0),
            'cfr_fi_not_filled': getattr(data, 'count_cfr_fi_nf', 0),
            'cfr_ri_not_filled': getattr(data, 'count_cfr_ri_nf', 0),
            'cfr_epicrisis_not_filled': getattr(data, 'count_cfr_epicrisis_nf', 0),
            'cards_count': getattr(data, 'count_all', 0),
        }

    def get_card_fill_rates_lpu_overview(self, curator_id):
        def make_lpu_cfr_stats(cfrs, cards_count):
            total = float(cards_count or 0)
            not_filled = float(cfrs.count_cfr_nf or 0)
            fill_pct = round(not_filled / total * 100) if total != 0 else 0
            return {
                'org_id': cfrs.id,
                'org_name': cfrs.shortName,
                'cfr_not_filled': not_filled,
                'cards_count': total,
                'fill_pct': fill_pct
            }

        sel = self.get_selecter()
        cfrs_data = sel.get_cfrs_lpu_overview(curator_id)
        cards_count = sel.get_curator_cards_count(curator_id, '3')
        return [
            make_lpu_cfr_stats(lpu_cfrs, cards_count)
            for lpu_cfrs in cfrs_data
        ]

    def get_card_fill_rates_doctor_overview(self, curator_id, curation_level):
        def make_doctor_cfr_stats(cfrs):
            total = float(cfrs.count_all or 0)
            not_filled = float(cfrs.count_cfr_nf or 0)
            doctor_name = initialize_name(cfrs.lastName, cfrs.firstName, cfrs.patrName)
            return {
                'doctor_id': cfrs.doctor_id,
                'doctor_name': doctor_name,
                'org_id': cfrs.org_id,
                'org_name': cfrs.shortName,
                'cfr_not_filled': not_filled,
                'cards_count': total
            }

        sel = self.get_selecter()
        data = sel.get_cfrs_doctor_overview(curator_id, curation_level)
        return [
            make_doctor_cfr_stats(doctor_cfrs)
            for doctor_cfrs in data
        ]


class CFRSelecter(BaseSelecter):

    def get_doctor_cfrs(self, doctor_id, only_open=True):
        Action = self.model_provider.get('Action')
        Event = self.model_provider.get('Event')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')
        query = self.model_provider.get_query('Action')

        query = query.join(
            Event, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ).filter(
            Action.deleted == 0, Event.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == 'cardAttributes',
            Event.execPerson_id == doctor_id
        ).group_by(
            Event.execPerson_id
        ).with_entities(
            Event.execPerson_id
        ).add_columns(
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.filled[0]), 1, 0)
                     ).label('count_cfr_filled'),
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_nf'),
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate_anamnesis',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_anamnesis_nf'),
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate_first_inspection',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_fi_nf'),
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate_repeated_inspection',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_ri_nf'),
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate_epicrisis',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_epicrisis_nf'),
            func.count(Event.id.distinct()).label('count_all')
        )
        if only_open:
            query = query.filter(Event.execDate == None)
        self.query = query
        return self.get_one()

    def get_cfrs_lpu_overview(self, curator_id, only_open=True):
        Event = self.model_provider.get('Event')
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')
        query = self.model_provider.get_query('Person')

        query = query.join(
            PersonCurationAssoc, rbOrgCurationLevel
        ).join(
            OrganisationCurationAssoc, OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id
        ).join(
            Organisation, OrganisationCurationAssoc.org_id == Organisation.id
        ).join(
            PersonInEvent, PersonInEvent.org_id == Organisation.id
        ).join(
            Event, Event.execPerson_id == PersonInEvent.id
        ).join(
            Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ).filter(
            Person.id == curator_id,
            rbOrgCurationLevel.code == '3',
            Event.deleted == 0,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == 'cardAttributes',
            ActionPropertyType.code == 'card_fill_rate'
        ).group_by(
            PersonInEvent.org_id
        ).with_entities(
            Organisation.id, Organisation.shortName
        ).add_columns(
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_nf'),
            func.count(Event.id.distinct()).label('count_all')
        ).order_by(
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).desc()
        )
        if only_open:
            query = query.filter(Event.execDate == None)
        self.query = query
        return self.get_all()

    def get_curator_cards_count(self, curator_id, curation_level, only_open=True):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')
        query = self.model_provider.get_query('Person')

        query = query.join(
            PersonCurationAssoc, rbOrgCurationLevel
        ).join(
            OrganisationCurationAssoc, OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id
        ).join(
            Organisation, OrganisationCurationAssoc.org_id == Organisation.id
        ).join(
            PersonInEvent, PersonInEvent.org_id == Organisation.id
        ).join(
            Event, Event.execPerson_id == PersonInEvent.id
        ).join(
            EventType, rbRequestType
        ).filter(
            Person.id == curator_id,
            rbOrgCurationLevel.code == curation_level,
            rbRequestType.code == request_type_pregnancy,
            Organisation.deleted == 0, PersonInEvent.deleted == 0, Event.deleted == 0,
        ).with_entities(
            func.count(Event.id.distinct()).label('count_all')
        )
        if only_open:
            query = query.filter(Event.execDate == None)
        self.query = query
        return self.get_first()

    def get_cfrs_doctor_overview(self, curator_id, curation_level, only_open=True):
        Event = self.model_provider.get('Event')
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')
        query = self.model_provider.get_query('Person')

        query = query.join(
            PersonCurationAssoc, rbOrgCurationLevel
        ).join(
            OrganisationCurationAssoc, OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id
        ).join(
            Organisation, OrganisationCurationAssoc.org_id == Organisation.id
        ).join(
            PersonInEvent, PersonInEvent.org_id == Organisation.id
        ).join(
            Event, Event.execPerson_id == PersonInEvent.id
        ).join(
            Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ).filter(
            Person.id == curator_id,
            Organisation.deleted == 0, PersonInEvent.deleted == 0, Event.deleted == 0,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == 'cardAttributes',
            ActionPropertyType.code == 'card_fill_rate',
            rbOrgCurationLevel.code == curation_level
        ).group_by(
            PersonInEvent.id
        ).with_entities(
            PersonInEvent.id.label('doctor_id'), PersonInEvent.firstName, PersonInEvent.lastName, PersonInEvent.patrName,
            Organisation.id.label('org_id'), Organisation.shortName
        ).add_columns(
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).label('count_cfr_nf'),
            func.count(Event.id.distinct()).label('count_all')
        ).order_by(
            func.sum(func.IF(and_(ActionPropertyType.code == 'card_fill_rate',
                                  ActionProperty_Integer.value_ == CardFillRate.not_filled[0]), 1, 0)
                     ).desc()
        )
        if only_open:
            query = query.filter(Event.execDate == None)
        self.query = query
        return self.get_all()