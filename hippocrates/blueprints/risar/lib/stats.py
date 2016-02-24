# -*- coding: utf-8 -*-

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased

from blueprints.risar.risar_config import request_type_pregnancy, checkup_flat_codes
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.models.enums import PerinatalRiskRate


class StatsController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return StatsSelecter()

    def get_current_cards_overview(self, person_id, curation_level=None):
        sel = self.get_selecter()
        data = sel.get_current_cards_overview(person_id, curation_level)
        events_all = float(data.count_all or 0) if data else 0
        events_45 = float(data.count_event_45_not_closed or 0) if data else 0
        events_2_months = float(data.count_event_2m_no_inspection or 0) if data else 0
        events_undefined_risk = float(data.count_event_prr_undefined or 0) if data else 0
        return {
            'events_all': events_all,
            'events_45': events_45,
            'events_2_months': events_2_months,
            'events_undefined_risk': events_undefined_risk
        }


class StatsSelecter(BaseSelecter):

    def get_current_cards_overview(self, person_id, curation_level=None):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Date = self.model_provider.get('ActionProperty_Date')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')
        Person = self.model_provider.get('Person')
        PersonInEvent = aliased(Person, name='PersonInEvent')
        PersonCurationAssoc = self.model_provider.get('PersonCurationAssoc')
        rbOrgCurationLevel = self.model_provider.get('rbOrgCurationLevel')
        OrganisationCurationAssoc = self.model_provider.get('OrganisationCurationAssoc')
        Organisation = self.model_provider.get('Organisation')

        # subqueries
        # 1) event pregnancy start date
        q_event_psd = self.model_provider.get_query('Event')
        q_event_psd = q_event_psd.join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Date
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == 'pregnancy_start_date'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Date.value.label('psd')
        ).subquery('EventPregStartDate')

        # 2) event latest inspection
        q_action_begdates = self.model_provider.get_query('Action')
        q_action_begdates = q_action_begdates.join(
            Event, EventType, rbRequestType, ActionType,
        ).filter(
            Event.deleted == 0, Action.deleted == 0, rbRequestType.code == request_type_pregnancy,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
        ).group_by(
            Event.id
        ).subquery('MaxActionBegDates')

        q_latest_inspections = self.model_provider.get_query('Action')
        q_latest_inspections = q_latest_inspections.join(
            q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                    q_action_begdates.c.event_id == Action.event_id)
        ).with_entities(
            Action.id.label('action_id')
        ).subquery('EventLatestInspections')

        q_latest_inspection = self.model_provider.get_query('Action')
        q_latest_inspection = q_latest_inspection.join(
            q_latest_inspections, q_latest_inspections.c.action_id == Action.id
        ).with_entities(
            Action.id.label('action_id'), Action.begDate.label('beg_date'), Action.event_id.label('event_id')
        ).order_by(
            Action.id.desc()
        ).limit(1).subquery('EventLatestInspection')

        # 3) event perinatal risk rate
        q_event_prr = self.model_provider.get_query('Event')
        q_event_prr = q_event_prr.join(
            EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy,
            Action.deleted == 0, ActionProperty.deleted == 0,
            ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == 'prenatal_risk_572'
        ).with_entities(
            Event.id.label('event_id'), ActionProperty_Integer.value_.label('prr')
        ).subquery('EventPerinatalRiskRate')

        # main query
        query = self.model_provider.get_query('Event')
        query = query.join(
            EventType, rbRequestType, Action, ActionType
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy, Event.execDate.is_(None),
            Action.deleted == 0, ActionType.flatCode == 'cardAttributes'
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

        query = query.outerjoin(
            q_event_psd, q_event_psd.c.event_id == Event.id
        ).outerjoin(
            q_latest_inspection, q_latest_inspection.c.event_id == Event.id
        ).outerjoin(
            q_event_prr, q_event_prr.c.event_id == Event.id
        )

        query = query.group_by(
            Event.execPerson_id
        ).with_entities(
            Event.execPerson_id
        ).add_columns(
            func.count(Event.id.distinct()).label('count_all'),
            func.sum(func.IF(
                and_(q_event_psd.c.psd.isnot(None),
                     # с даты начала случая прошло от 45 недель
                     func.floor(func.datediff(func.curdate(), q_event_psd.c.psd) / 7) + 1 >= 45
                     ),
                1, 0)
            ).label('count_event_45_not_closed'),
            func.sum(func.IF(
                # с момента последнего осмотра (или даты постановки на учет) прошло более 2 месяцев (60 дней)
                func.datediff(func.curdate(),
                              func.coalesce(q_latest_inspection.c.beg_date, Event.setDate)) / 30 >= 2,
                1, 0)
            ).label('count_event_2m_no_inspection'),
            func.sum(func.IF(
                # степень перинатального риска не определена (или отсутствует в случае)
                or_(q_event_prr.c.prr.is_(None),
                     q_event_prr.c.prr == PerinatalRiskRate.undefined[0]),
                1, 0)
            ).label('count_event_prr_undefined')
        )

        self.query = query
        return self.get_one()
