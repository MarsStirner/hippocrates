# -*- coding: utf-8 -*-
import collections

from itertools import groupby

from sqlalchemy import func, and_, between
from sqlalchemy.orm import aliased

from hippocrates.blueprints.risar.lib.risk_groups.needles_haystacks import any_thing
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy, checkup_flat_codes, \
    pregnancy_card_attrs, risar_epicrisis, request_type_gynecological
from hippocrates.blueprints.risar.models.risar import RisarRiskGroup, RisarEpicrisis_Children
from hippocrates.blueprints.risar.models.radzinsky_risks import RisarRadzinskyRisks, \
    RisarRegionalRiskRate
from hippocrates.blueprints.risar.lib.specific import SpecificsManager

from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.models.actions import ActionType, Action, ActionProperty_Date, ActionProperty, ActionPropertyType
from nemesis.models.enums import PerinatalRiskRate
from nemesis.models.risar import rbRadzinskyRiskRate, rbRisarRegionalRiskRate
from nemesis.models.event import EventType, Event
from nemesis.models.exists import rbRequestType
from nemesis.models.diagnosis import rbDiagnosisKind, rbDiagnosisTypeN, Diagnosis, Diagnostic, Action_Diagnosis
from nemesis.systemwide import db, cache
from nemesis.models.client import Client


class StatsController(BaseModelController):
    @classmethod
    def get_selecter(cls):
        return StatsSelecter()

    def get_current_cards_overview(self, person_id, curation_level=None):
        """Различные метрики по текущим открытым картам"""
        sel = self.get_selecter()
        data = sel.get_current_cards_overview(person_id, curation_level)
        data2 = sel.get_current_cards_overview_checkup_skipped(person_id, curation_level)
        events_all = float(data.count_all or 0) if data else 0
        events_not_closed_42 = float(data.count_event_not_closed_42 or 0) if data else 0
        events_2_months = float(data.count_event_2m_no_inspection or 0) if data else 0
        events_missed_last_checkup = float(data2.count_event_skipped_checkup or 0) if data2 else 0
        return {
            'events_all': events_all,
            'events_not_closed_42': events_not_closed_42,
            'events_2_months': events_2_months,
            'events_missed_last_checkup': events_missed_last_checkup,
        }

    def get_cards_pregnancy_week_distribution(self, person_id, curation_level):
        """Распределение пациенток по сроку беременности"""
        distr_data = [
            [str(week_num), 0]
            for week_num in (range(1, 41) + ['40+'])
            ]
        sel = self.get_selecter()
        events_data = sel.get_events_preg_weeks(person_id, curation_level)
        for event_id, preg_week in events_data:
            if preg_week is None:
                pass
            elif 1 <= preg_week <= 40:
                distr_data[preg_week - 1][1] += 1
            else:
                distr_data[-1][1] += 1
        return {
            'preg_week_distribution': distr_data,
            'total_cards': len(events_data)
        }

    def get_risk_groups_distribution(self, person_id, curation_level):
        return dict(self.get_selecter().get_risk_group_counts(person_id, curation_level))

    def get_cards_urgent_hosp(self, person_id):
        """Карты пациенток, требующие срочной госпитализации"""
        sel = self.get_selecter()
        events = sel.get_events_urgent_hosp(person_id)
        return events

    def get_controlled_events(self, person_id, curation_level):
        """Карты пациенток, взятые на контроль пользователем"""
        sel = self.get_selecter()
        data = sel.get_controlled_events(person_id, curation_level)
        cards_count = int(data.cards_count or 0) if data else 0
        return {
            'cards_count': cards_count
        }

    def get_radz_risks(self, person_id, curation_level):
        return dict(self.get_selecter().get_radz_risk_counts(person_id, curation_level))

    def get_regional_risks(self, person_id, curation_level):
        return dict(self.get_selecter().get_regional_risk_counts(person_id, curation_level))


class StatsSelecter(BaseSelecter):
    def query_main(self, person_id, curation_level):
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        Client = self.model_provider.get('Client')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')

        query = self.model_provider.get_query('Event')
        query = query.join(
            EventType, rbRequestType, Client, Action, ActionType
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy, Event.execDate.is_(None),
            Action.deleted == 0, ActionType.flatCode == pregnancy_card_attrs
        )
        if curation_level:
            # карты куратора
            return query.join(
                PersonInEvent, Event.execPerson_id == PersonInEvent.id
            ).join(
                Organisation, PersonInEvent.org_id == Organisation.id
            ).join(
                OrganisationCurationAssoc, OrganisationCurationAssoc.org_id == Organisation.id
            ).join(
                PersonCurationAssoc, OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id
            ).join(
                rbOrgCurationLevel, PersonCurationAssoc.orgCurationLevel_id == rbOrgCurationLevel.id
            ).filter(
                PersonCurationAssoc.person_id == person_id,
                rbOrgCurationLevel.code == curation_level
            )
        else:
            # карты врача
            query = query.filter(Event.execPerson_id == person_id)
        return query

    def get_risk_group_counts(self, person_id, curation_level=None):
        query = self.query_main(person_id, curation_level)
        query = RisarRiskGroup.query.join(
            query.subquery()
        ).filter(
            RisarRiskGroup.deleted == 0,
        ).group_by(
            RisarRiskGroup.riskGroup_code,
        ).with_entities(
            RisarRiskGroup.riskGroup_code,
            func.count(func.distinct(RisarRiskGroup.event_id)),
        )
        self.query = query
        return self.get_all()

    def get_radz_risk_counts(self, person_id, curation_level=None):
        events_q = self.query_main(person_id, curation_level).subquery()
        query = RisarRadzinskyRisks.query.join(
            rbRadzinskyRiskRate
        ).join(
            events_q, events_q.c.id == RisarRadzinskyRisks.event_id
        ).group_by(
            RisarRadzinskyRisks.risk_rate_id,
        ).with_entities(
            rbRadzinskyRiskRate.code,
            func.count(func.distinct(RisarRadzinskyRisks.event_id)),
        )
        self.query = query
        return self.get_all()

    def get_regional_risk_counts(self, person_id, curation_level=None):
        if not SpecificsManager.has_regional_risks():
            return []
        events_q = self.query_main(person_id, curation_level).subquery()
        query = RisarRegionalRiskRate.query.join(
            rbRisarRegionalRiskRate
        ).join(
            events_q, events_q.c.id == RisarRegionalRiskRate.event_id
        ).group_by(
            RisarRegionalRiskRate.risk_rate_id,
        ).with_entities(
            rbRisarRegionalRiskRate.code,
            func.count(func.distinct(RisarRegionalRiskRate.event_id)),
        )
        self.query = query
        return self.get_all()

    def query_pregnancy_start_date(self):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')

        return self.model_provider.get_query('Event').join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'pregnancy_start_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('psd')
        )

    def query_epicrisis(self):
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')

        return self.model_provider.get_query('Action').join(
            ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == risar_epicrisis, ActionPropertyType.code == 'delivery_date'
        ).with_entities(
            Action.event_id.label('event_id'), Action.id.label('action_id'),
            ActionProperty_Date.value.label('delivery_date')
        )

    def get_current_cards_overview(self, person_id, curation_level=None):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')

        # subqueries
        # 1) epicrisis with delivery_date
        q_event_epicr = self.query_epicrisis().subquery('EventEpicrisis')

        # 2) event latest inspection
        # * самые поздние даты осмотров по обращениям
        q_action_begdates = self.model_provider.get_query('Action').join(
            Event, EventType, rbRequestType, ActionType,
        ).filter(
            Event.deleted == 0, Action.deleted == 0, rbRequestType.code == request_type_pregnancy,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
        ).group_by(
            Event.id
        ).subquery('MaxActionBegDates')

        # * id самых поздних осмотров (включая уже и дату и id, если даты совпадают) для каждого случая
        q_latest_checkups_id = self.model_provider.get_query('Action').join(
            q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                    q_action_begdates.c.event_id == Action.event_id)
        ).filter(
            Action.deleted == 0, ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
        ).group_by(
            Action.event_id
        ).subquery('EventLatestCheckups')

        # * итого: самый поздний осмотр для каждого случая
        q_latest_inspections = self.model_provider.get_query('Action').join(
            q_latest_checkups_id, q_latest_checkups_id.c.action_id == Action.id
        ).with_entities(
            Action.id.label('action_id'), Action.event_id.label('event_id'),
            Action.begDate.label('beg_date'), Action.endDate.label('end_date')
        ).subquery('EventLatestInspections')

        # main query
        query = self.query_main(person_id, curation_level)

        query = query.outerjoin(
            q_event_epicr, q_event_epicr.c.event_id == Event.id
        ).outerjoin(
            q_latest_inspections, q_latest_inspections.c.event_id == Event.id
        )

        query = query.with_entities(
            func.count(Event.id.distinct()).label('count_all'),
            func.sum(func.IF(
                and_(q_event_epicr.c.delivery_date.isnot(None),
                     # с даты родоразрешения прошло более 42 дней
                     func.datediff(func.curdate(), q_event_epicr.c.delivery_date) >= 42
                     ),
                1, 0)
            ).label('count_event_not_closed_42'),
            func.sum(func.IF(
                # с момента последнего осмотра (или даты постановки на учет) прошло более 2 месяцев (60 дней)
                func.datediff(func.curdate(),
                              func.coalesce(q_latest_inspections.c.beg_date, Event.setDate)) >= 60,
                1, 0)
            ).label('count_event_2m_no_inspection')
        )

        self.query = query
        return self.get_one()

    def get_current_cards_overview_checkup_skipped(self, person_id, curation_level=None):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')
        q_epicrisis = self.query_epicrisis().subquery('Epicrisis')

        # 2) event latest inspection
        # * самые поздние даты осмотров по обращениям
        q_action_begdates = self.model_provider.get_query('Action').join(
            Event, EventType, rbRequestType, ActionType
        ).filter(
            Event.deleted == 0, Action.deleted == 0, rbRequestType.code == request_type_pregnancy,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
        ).group_by(
            Event.id
        ).subquery('MaxActionBegDates')

        # * id самых поздних осмотров (включая уже и дату и id, если даты совпадают) для каждого случая
        q_latest_checkups_id = self.model_provider.get_query('Action').join(
            q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                    q_action_begdates.c.event_id == Action.event_id)
        ).filter(
            Action.deleted == 0, ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
        ).group_by(
            Action.event_id
        ).subquery('EventLatestCheckups')

        # * итого: самый поздний осмотр для каждого случая
        q_latest_inspections = self.model_provider.get_query('Action').join(
            q_latest_checkups_id, q_latest_checkups_id.c.action_id == Action.id
        ).join(
            ActionProperty, ActionPropertyType, ActionProperty_Date
        ).outerjoin(
            q_epicrisis, q_epicrisis.c.event_id == Action.event_id
        ).filter(
            ActionPropertyType.code == 'next_date', q_epicrisis.c.event_id.is_(None)
        ).with_entities(
            Action.id.label('action_id'), Action.event_id.label('event_id'),
            Action.begDate.label('beg_date'), Action.endDate.label('end_date'),
            ActionProperty_Date.value.label('next_date')
        ).subquery('EventLatestInspections')

        # main query
        query = self.query_main(person_id, curation_level)
        query = query.outerjoin(
            q_latest_inspections, q_latest_inspections.c.event_id == Event.id
        )
        query = query.with_entities(
            func.sum(
                func.IF(q_latest_inspections.c.next_date <= func.curdate(),
                        1,
                        0)
            ).label('count_event_skipped_checkup')
        )

        self.query = query
        return self.get_one()

    def get_events_preg_weeks(self, person_id, curation_level):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')

        # event pregnancy start date
        q_event_psd = self.query_pregnancy_start_date().subquery('EventPregnancyStartDate')

        # event predicted delivery date
        q_event_pdd = self.model_provider.get_query('Event')
        q_event_pdd = q_event_pdd.join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'predicted_delivery_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('pdd')
        ).subquery('EventPredictedDeliveryDate')

        # main query
        query = self.query_main(person_id, curation_level)

        query = query.outerjoin(
            q_event_psd, q_event_psd.c.event_id == Event.id
        ).outerjoin(
            q_event_pdd, q_event_pdd.c.event_id == Event.id
        ).with_entities(
            Event.id,
            # неделя беременности
            func.floor(
                func.datediff(
                    func.IF(func.coalesce(q_event_pdd.c.pdd, func.curdate()) < func.curdate(),
                            q_event_pdd.c.pdd,
                            func.curdate()),
                    q_event_psd.c.psd
                ) / 7
            ) + 1
        )

        self.query = query
        return self.get_all()

    def get_events_urgent_hosp(self, person_id):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')

        # main query
        query = self.query_main(person_id, None)

        # event prr query
        q_event_prr = self.model_provider.get_query('Event')
        q_event_prr = q_event_prr.join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'prenatal_risk_572'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Integer.value_.label('prr')
        ).subquery('EventPerinatalRiskRate')

        # event pregnancy start date
        q_event_psd = self.query_pregnancy_start_date().subquery('EventPregnancyStartDate')

        # event predicted delivery date
        q_event_pdd = self.model_provider.get_query('Event')
        q_event_pdd = q_event_pdd.join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == pregnancy_card_attrs, ActionPropertyType.code == 'predicted_delivery_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('pdd')
        ).subquery('EventPredictedDeliveryDate')

        query = query.join(
            q_event_prr,
            and_(Event.id == q_event_prr.c.event_id,
                 q_event_prr.c.prr.in_([PerinatalRiskRate.medium[0], PerinatalRiskRate.high[0]]))
        ).join(
            q_event_pdd, Event.id == q_event_pdd.c.event_id
        ).join(
            q_event_psd, Event.id == q_event_psd.c.event_id
        ).filter(
            # неделя беременности
            func.floor(
                func.datediff(
                    func.IF(func.coalesce(q_event_pdd.c.pdd, func.curdate()) < func.curdate(),
                            q_event_pdd.c.pdd,
                            func.curdate()),
                    q_event_psd.c.psd
                ) / 7
            ) + 1 >= 38
        ).order_by(
            q_event_pdd.c.pdd
        )

        self.query = query
        return self.get_all()

    def get_controlled_events(self, person_id, curation_level=None):
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        Client = self.model_provider.get('Client')
        rbRequestType = self.model_provider.get('rbRequestType')
        EventPersonsControl = self.model_provider.get('EventPersonsControl')

        query = self.model_provider.get_query('Event')
        query = query.join(
            EventType, rbRequestType, Client
        ).join(
            EventPersonsControl
        ).filter(
            Event.deleted == 0,
            rbRequestType.code.in_((request_type_pregnancy, request_type_gynecological)),
            Event.execDate.is_(None),
            EventPersonsControl.endDate.is_(None),
            EventPersonsControl.person_id == person_id
        )
        if curation_level:
            # карты куратора
            query = query.join(
                PersonInEvent, Event.execPerson_id == PersonInEvent.id
            ).join(
                Organisation, PersonInEvent.org_id == Organisation.id
            ).join(
                OrganisationCurationAssoc, OrganisationCurationAssoc.org_id == Organisation.id
            ).join(
                PersonCurationAssoc, OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id
            ).join(
                rbOrgCurationLevel, PersonCurationAssoc.orgCurationLevel_id == rbOrgCurationLevel.id
            ).filter(
                PersonCurationAssoc.person_id == person_id,
                rbOrgCurationLevel.code == curation_level
            )
        else:
            # карты врача
            query = query.filter(Event.execPerson_id == person_id)
        query = query.with_entities(
            func.count(Event.id.distinct()).label('cards_count'),
        )

        self.query = query
        return self.get_one()


mather_death_koef_diags = (
    'O72', 'O45', 'O46', 'O44.1', 'O67', 'O13', 'O14', 'O15', 'O75.3', 'O85',
    'O86', 'O88', 'O00-O08', 'O74', 'O75.1', 'O75.4', 'O89', 'O71.0', 'O71.1',
    'O71.3', 'O95', 'Z21', 'B20-B24', 'A34', 'A15-A19', 'B06', 'C51-C58',
    'E10.2', 'E11.2', 'E12.2', 'E13.2', 'E14.2', 'E10.3', 'E11.3', 'E12.3',
    'E13.3', 'E14.3', 'E21', 'E22', 'E24', 'C91.0', 'C92.0', 'C92.4', 'C92.5',
    'C93.0', 'C94.0', 'D46', 'C82', 'C83', 'C84', 'C85', 'C88', 'C90', 'C91',
    'C81', 'C92', 'D45', 'D47', 'D47.1', 'D47.3', 'C92.7', 'C93.1', 'C94.1',
    'C94.5', 'D61', 'D55', 'D58', 'D59', 'D56', 'D69.3', 'E80', 'F02', 'F04',
    'F06', 'F07', 'F09', 'F20', 'F22', 'F23', 'F24', 'F25', 'F29', 'F30',
    'F31', 'F32', 'F33', 'F71-F79', 'F99.1', 'F70', 'F84', 'F44', 'F10-F19',
    'F30-F39', 'G00-G09', 'G10-G13', 'G12.2', 'G20-G22', 'G24', 'G35', 'G40.0',
    'G40.2-G40.6', 'G40.8', 'G40.9', 'G46', 'G95', 'G47', 'G54', 'G61.0',
    'G70-G73', 'E83.0', 'C43.1', 'C69.0', 'C69.1', 'C69.2', 'C69.3', 'C69.4',
    'C69.5', 'C69.6', 'C69.8', 'C69.9', 'C72.3', 'I01', 'I05-I09', 'I50',
    'I26-I27', 'I33', 'I48', 'I47', 'I44.2', 'I74', 'I81-I82', 'I51.3', 'Q20',
    'Q21.0', 'Q21.1', 'Q25.0', 'Q25.3', 'Q25.1', 'Q23', 'I42.0', 'I42.5',
    'I42.1', 'I42.2', 'Q21.3', 'Q21.8', 'Q22.5', 'Q25.8-Q25.9', 'Q20.0',
    'Q20.8-Q20.9', 'Q25.2', 'Q25.5', 'Q21.8', 'Q21.1', 'I27.0', 'I40', 'I40.1',
    'I21', 'I33.0', 'I39', 'I31.1', 'I31.0', 'I45.6', 'I34.0', 'I34.2', 'T82',
    'T88.8', 'I71', 'I72.2', 'I72.3', 'I72.8', 'I77.6', 'I80', 'I74', 'I82',
    'I74.3', 'I74.8', 'I10', 'J96', 'I27.0', 'K25.4', 'K26.4', 'K31.1',
    'K73.2', 'K72.0', 'K74.6', 'K76.6', 'K76.0', 'K50.8', 'K51.0', 'K90.0',
    'K43.0', 'K56.5', 'K63.2', 'N00.0', 'N03', 'N18.9', 'Q64', 'C58', 'F00.0',
    'F99.9', 'Q74.3', 'Q77.4', 'Q77.5', 'Q77.1', 'Q78.0', 'Q73.0', 'M05.2',
    'M05.3', 'M06.8', 'M05.0', 'M06.1', 'M30.0', 'M30.1', 'M31.3', 'M31.4',
    'M32.1', 'M33.1', 'M33.2', 'M34.0', 'M35.0', 'M35.1', 'M45', 'D69.8',
    'D68.3',
)


@cache.memoize(timeout=60)
def get_list_of_alive_dead_actions(start_date, end_date):
    qr = db.select(
        (RisarEpicrisis_Children.alive, func.group_concat(RisarEpicrisis_Children.id.distinct())),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            rbRequestType.code == request_type_pregnancy,
            Action.event_id == Event.id,
            ActionType.id == Action.actionType_id,
            EventType.id == Event.eventType_id,
            RisarEpicrisis_Children.action_id == Action.id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            RisarEpicrisis_Children.alive.isnot(None),
            between(RisarEpicrisis_Children.date, start_date, end_date)
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, RisarEpicrisis_Children
        ),
        group_by=RisarEpicrisis_Children.alive
    ).distinct()
    return dict((k, v.split(',')) for k, v in db.session.execute(qr))


# @cache.memoize(timeout=60)
# def get_children_stat(start_date, end_date, children_ids=None, is_alive=True):
#     is_alive = safe_int(safe_bool(is_alive))
#     if children_ids:
#         selectable1 = db.select(
#             (RisarEpicrisis_Children.date, func.count(RisarEpicrisis_Children.id),),
#             whereclause=db.and_(
#                 ActionType.flatCode == 'epicrisis',
#                 rbRequestType.code == request_type_pregnancy,
#                 Action.event_id == Event.id,
#                 ActionType.id == Action.actionType_id,
#                 EventType.id == Event.eventType_id,
#                 rbRequestType.id == EventType.requestType_id,
#                 RisarEpicrisis_Children.action_id == Action.id,
#                 RisarEpicrisis_Children.alive == is_alive,
#                 Event.deleted == 0,
#                 Action.deleted == 0,
#                 RisarEpicrisis_Children.id.in_(children_ids),
#                 between(RisarEpicrisis_Children.date, start_date, end_date)
#             ),
#             from_obj=(
#                 Event, EventType, rbRequestType, Action, ActionType, RisarEpicrisis_Children
#             ),
#             group_by=(func.date(RisarEpicrisis_Children.date)),
#             order_by=(RisarEpicrisis_Children.date)
#         )
#         return collections.OrderedDict((x, y) for x, y in db.session.execute(selectable1))
#     return {}

@cache.memoize(timeout=60)
def get_children_stat(children_ids=None):
    if children_ids:
        selectable1 = db.select(
            (RisarEpicrisis_Children.date, func.count(RisarEpicrisis_Children.id.distinct()),),
            whereclause=db.and_(
                ActionType.flatCode == 'epicrisis',
                rbRequestType.code == request_type_pregnancy,
                Action.event_id == Event.id,
                ActionType.id == Action.actionType_id,
                EventType.id == Event.eventType_id,
                rbRequestType.id == EventType.requestType_id,
                RisarEpicrisis_Children.action_id == Action.id,
                Event.deleted == 0,
                Action.deleted == 0,
                RisarEpicrisis_Children.id.in_(children_ids),
            ),
            from_obj=(
                Event, EventType, rbRequestType, Action, ActionType, RisarEpicrisis_Children
            ),
            group_by=(func.date(RisarEpicrisis_Children.date)),
            order_by=(RisarEpicrisis_Children.date)
        )
        return collections.OrderedDict((x, y) for x, y in db.session.execute(selectable1))
    return {}


@cache.memoize(timeout=60)
def get_children_cards_info(children_ids=None):
    if not children_ids:
        return children_ids
    query = db.session.query(
        RisarEpicrisis_Children.id.distinct().label('id'),
        RisarEpicrisis_Children.date.label('children_date'),
        RisarEpicrisis_Children.action_id.label('action_id'),
        Action.event_id.label('event_id'),
        Event.externalId.label('external_id'),
        func.CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName).label('fio'),
    ).join(
        Action,
        Event, Client, EventType, rbRequestType,
        ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date,
    ).filter(
        RisarEpicrisis_Children.id.in_(children_ids)
    ).group_by('children_date').order_by('children_date')

    grouped_by_date = groupby(
        query.all(), key=lambda x: x.children_date
    )

    def make_card_info(row):
        return {
            'id': row.id,
            'action_id': row.action_id,
            'event_id': row.event_id,
            'external_id': row.external_id,
            'patient_fio': row.fio
        }

    return dict((idate, map(make_card_info, rows)) for idate, rows in grouped_by_date)


@cache.memoize(timeout=60)
def get_maternal_death(start_date, end_date):
    query = db.session.query(
        Action.id.label('action_id'),
        ActionProperty_Date.value.label('created_ymd'),
        Action.event_id.label('event_id'),
        Event.externalId.label('external_id'),
        func.CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName).label('fio'),
        func.group_concat(Diagnostic.MKB).label('diagnostic_mkbs')
    ).join(
        Event, Client, EventType, rbRequestType,
        ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date,
    ).filter(
        ActionType.flatCode == 'epicrisis',
        ActionPropertyType.code == 'death_date',
        rbRequestType.code == request_type_pregnancy,
        Action.event_id == Event.id,
        ActionProperty.action_id == Action.id,
        ActionPropertyType.id == ActionProperty.type_id,
        ActionType.id == Action.actionType_id,
        ActionProperty_Date.id == ActionProperty.id,
        EventType.id == Event.eventType_id,
        rbRequestType.id == EventType.requestType_id,
        Event.deleted == 0,
        Action.deleted == 0,
        between(
            ActionProperty_Date.value,
            start_date,
            end_date
        )
    ).join(
        Diagnostic, Diagnostic.action_id == Action.id
    ).join(
        Diagnosis
    ).join(
        Action_Diagnosis
    ).join(
        rbDiagnosisKind
    ).join(
        rbDiagnosisTypeN
    ).filter(
        Diagnosis.endDate.is_(None),
        rbDiagnosisKind.code == 'main',
        rbDiagnosisTypeN.code == 'pathanatomical',
    ).order_by(
        'created_ymd'
    ).group_by(Action.id)

    def make_card(card_info):
        return {
            'action_id': card_info[0],
            'event_id': card_info[2],
            'external_id': card_info[3],
            'patient_fio': card_info[4],
        }

    rows_for_maternal_death = set()
    for row in query.all():
        if any_thing(row.diagnostic_mkbs.split(','), mather_death_koef_diags, lambda x: x):
            rows_for_maternal_death.add(row[:5])

    grouped_by_date = groupby(
        rows_for_maternal_death, key=lambda x: x[1]
    )

    dc = {}
    for idate, cards_info in grouped_by_date:
        cards_info = list(cards_info)
        dc[idate] = {
            'cards': map(make_card, cards_info),
            'length': len(cards_info),
        }
    return dc


def get_amt_alive_children(start_date, end_date):
    children_ids = get_list_of_alive_dead_actions(start_date, end_date).get(1, [])
    alive_children = get_children_stat(children_ids)
    return float(sum(alive_children.values())) or 1.0


def get_amt_dead_chilren(start_date, end_date):
    children_ids = get_list_of_alive_dead_actions(start_date, end_date).get(0, [])
    dead_children = get_children_stat(children_ids)
    return float(sum(dead_children.values()))


def get_maternal_coefficient(start_date, end_date):
    sm = map(lambda x: x.get('length'), get_maternal_death(start_date, end_date).values())
    maternal_death_all = float(sum(sm))
    return maternal_death_all / get_amt_alive_children(start_date, end_date) * 100000


def get_infant_death_coefficient(start_date, end_date):
    dead = get_amt_dead_chilren(start_date, end_date)
    alive = get_amt_alive_children(start_date, end_date)
    return (dead / (dead + alive) * 1000)
