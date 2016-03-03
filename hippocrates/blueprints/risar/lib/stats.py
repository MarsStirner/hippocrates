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
        """Различные метрики по текущим открытым картам"""
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
            elif preg_week <= 40:
                distr_data[preg_week - 1][1] += 1
            else:
                distr_data[-1][1] += 1
        return {
            'preg_week_distribution': distr_data,
            'total_cards': len(events_data)
        }

    def get_risk_groups_distribution(self, person_id, curation_level):
        return dict(self.get_selecter().get_risk_group_counts(person_id, curation_level))


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
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')

        query = self.model_provider.get_query('Event')
        query = query.join(
            EventType, rbRequestType, Action, ActionType
        ).filter(
            Event.deleted == 0, rbRequestType.code == request_type_pregnancy, Event.execDate.is_(None),
            Action.deleted == 0, ActionType.flatCode == 'cardAttributes'
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
        from ..models.risar import RisarRiskGroup

        query = self.query_main(person_id, curation_level)
        query = query.join(RisarRiskGroup).filter(
            RisarRiskGroup.deleted == 0,
        ).group_by(
            RisarRiskGroup.riskGroup_code,
        ).with_entities(
            RisarRiskGroup.riskGroup_code,
            func.count(func.distinct(RisarRiskGroup.event_id)),
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
                ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == 'pregnancy_start_date'
            ).with_entities(
                Event.id.label('event_id'), ActionProperty_Date.value.label('psd')
            )

    def get_current_cards_overview(self, person_id, curation_level=None):
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_Integer = self.model_provider.get('ActionProperty_Integer')

        # subqueries
        # 1) event pregnancy start date
        q_event_psd = self.query_pregnancy_start_date().subquery('EventPregnancyStartDate')

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
        query = self.query_main(person_id, curation_level)

        query = query.outerjoin(
            q_event_psd, q_event_psd.c.event_id == Event.id
        ).outerjoin(
            q_latest_inspection, q_latest_inspection.c.event_id == Event.id
        ).outerjoin(
            q_event_prr, q_event_prr.c.event_id == Event.id
        )

        query = query.with_entities(
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
            ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == 'predicted_delivery_date'
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