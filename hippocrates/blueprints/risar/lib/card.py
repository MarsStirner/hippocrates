# -*- coding: utf-8 -*-
import datetime
from weakref import WeakValueDictionary

import itertools
import sqlalchemy

from hippocrates.blueprints.risar.lib.helpers import lazy, LocalCache
from hippocrates.blueprints.risar.lib.utils import get_action, get_action_list
from hippocrates.blueprints.risar.lib.prev_children import get_previous_children
from hippocrates.blueprints.risar.models.fetus import RisarFetusState
from hippocrates.blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, checkup_flat_codes, \
    risar_anamnesis_pregnancy, pregnancy_card_attrs, gynecological_card_attrs, risar_anamnesis_transfusion, \
    puerpera_inspection_flat_code, risar_gyn_general_anamnesis_flat_code, risar_gyn_checkup_flat_codes, request_type_pregnancy, \
    request_type_gynecological
from nemesis.lib.data import create_action
from nemesis.models.actions import Action, ActionType, create_property
from nemesis.models.diagnosis import Diagnosis, Action_Diagnosis
from nemesis.models.diagnosis import Diagnostic
from nemesis.models.event import Event
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class PreviousPregnancy(object):
    def __init__(self, action):
        self._action = action

    @property
    def action(self):
        return self._action

    @lazy
    def newborn_inspections(self):
        return get_previous_children(self._action)


class AbstractCard(object):
    cache = LocalCache()
    action_type_attrs = None

    def __init__(self, event):
        self._cached = {}
        self.event = event
        self._card_attrs_action = None

    def check_card_attrs_action_integrity(self, action):
        return

    @property
    def attrs(self):
        result = self.get_card_attrs_action()
        self.check_card_attrs_action_integrity(result)
        return result

    def get_card_attrs_action(self, auto=False):
        if self._card_attrs_action is None:
            from hippocrates.blueprints.risar.lib.card_attrs import default_AT_Heuristic

            action = Action.query.join(ActionType).filter(
                Action.event == self.event,
                Action.deleted == 0,
                ActionType.flatCode == self.action_type_attrs,
            ).first()
            if action is None and auto:
                action = create_action(default_AT_Heuristic(self.event.eventType), self.event)
                self._card_attrs_action = action
                self.reevaluate_card_attrs()
                db.session.add(action)
                db.session.commit()
            self._card_attrs_action = action
        return self._card_attrs_action

    @lazy
    def transfusions(self):
        return get_action_list(self.event, risar_anamnesis_transfusion).all()

    @lazy
    def intolerances(self):
        return list(itertools.chain(self.event.client.allergies, self.event.client.intolerances))

    @lazy
    def prev_pregs(self):
        return map(PreviousPregnancy, get_action_list(self.event, risar_anamnesis_pregnancy))

    def reevaluate_card_attrs(self):
        pass

    @classmethod
    def get_for_event(cls, event):
        """
        :rtype: AbstractCard
        :param event:
        :return:
        """
        klass = classes.get(event.eventType.requestType.code, cls)
        from flask import g
        if not hasattr(g, '_card_cache'):
            g._card_cache = WeakValueDictionary()
        if event.id not in g._card_cache:
            result = g._card_cache[event.id] = klass(event)
        else:
            result = g._card_cache[event.id]
        return result

    @cache.cached_call
    def get_client_diagnostics(self, beg_date, end_date=None, including_closed=False):
        """
        :type beg_date: datetime.date
        :type end_date: datetime.date | NoneType
        :type including_closed: bool
        :param beg_date:
        :param end_date:
        :param including_closed:
        :return:
        """
        client = self.event.client
        query = db.session.query(Diagnostic).join(
            Diagnosis
        ).filter(
            Diagnosis.client == client,
            Diagnosis.deleted == 0,
            Diagnostic.deleted == 0,
        )
        if end_date is not None:
            query = query.filter(
                Diagnostic.createDatetime <= end_date,
                Diagnosis.setDate <= end_date,
            )
        if not including_closed:
            query = query.filter(
                db.or_(
                    Diagnosis.endDate.is_(None),
                    Diagnosis.endDate >= beg_date,
                )
            )
        query = query.group_by(
            Diagnostic.diagnosis_id
        )
        query = query.with_entities(sqlalchemy.func.max(Diagnostic.id).label('zid')).subquery()
        query = db.session.query(Diagnostic).join(query, query.c.zid == Diagnostic.id)
        return query.all()

    @cache.cached_call
    def get_event_diagnostics(self, beg_date, end_date=None, kind_ids=None, including_closed=False):
        """
        :type beg_date: datetime.date
        :type end_date: datetime.date | NoneType
        :type including_closed: bool
        :type kind_ids: list<int|long>
        :param beg_date:
        :param end_date:
        :param kind_ids:
        :param including_closed:
        :return:
        """
        query = db.session.query(Diagnostic).join(
            Diagnosis
        ).join(
            Event, Event.client_id == Diagnosis.client_id,
                   ).filter(
            Event.id == self.event.id,
            Event.execDate.is_(None),
            Event.deleted == 0,
            Diagnosis.deleted == 0,
            Diagnostic.deleted == 0,
        )
        if kind_ids:
            query = query.join(Action_Diagnosis).join(Action).filter(
                Action.event_id == Event.id,
                Action_Diagnosis.diagnosisKind_id.in_(kind_ids),
                Action.deleted == 0,
                Action_Diagnosis.deleted == 0,
            )
        if end_date is not None:
            query = query.filter(
                Diagnostic.createDatetime <= end_date,
                Diagnosis.setDate <= end_date,
            )
        if not including_closed:
            query = query.filter(
                db.or_(
                    Diagnosis.endDate.is_(None),
                    Diagnosis.endDate >= beg_date,
                )
            )
        query = query.group_by(
            Diagnostic.diagnosis_id
        )
        query = query.with_entities(sqlalchemy.func.max(Diagnostic.id).label('zid')).subquery()
        query = db.session.query(Diagnostic).join(query, query.c.zid == Diagnostic.id)
        return query.all()


class PregnancyCard(AbstractCard):
    """
    @type event: nemesis.models.event.Event
    """
    cache = LocalCache()
    action_type_attrs = pregnancy_card_attrs

    class Anamnesis(object):
        def __init__(self, event):
            self._event = event

        @lazy
        def mother(self):
            return get_action(self._event, risar_mother_anamnesis, True)

        @lazy
        def father(self):
            return get_action(self._event, risar_father_anamnesis, True)

    class Fetus(object):
        def __init__(self, action):
            self._action = action

        @lazy
        def states(self):
            return RisarFetusState.query.filter(
                RisarFetusState.action == self._action,
                RisarFetusState.deleted == 0,
            ).order_by(RisarFetusState.id).all()

        @property
        def action(self):
            return self._action

    def __init__(self, event):
        super(PregnancyCard, self).__init__(event)
        self._anamnesis = self.Anamnesis(event)

    def check_card_attrs_action_integrity(self, action):
        """
        Проверка, что в action, соответствующего атрибутам карточки, существуют
        все необходимые свойства.
        :param action: действие с атрибутами
        :type action: nemesis.models.actions.Action
        :return: None
        """
        from nemesis.models.actions import create_property

        property_type_codes = [
            'pregnancy_pathology_list', 'preeclampsia_susp', 'preeclampsia_comfirmed',
            'card_fill_rate', 'card_fill_rate_anamnesis', 'card_fill_rate_first_inspection',
            'card_fill_rate_repeated_inspection', 'card_fill_rate_epicrisis'
        ]
        for apt_code in property_type_codes:
            if apt_code not in action.propsByCode:
                create_property(action, apt_code)

    @property
    def anamnesis(self):
        return self._anamnesis

    @lazy
    def checkups(self):
        return get_action_list(self.event, checkup_flat_codes).all()

    @lazy
    def checkups_puerpera(self):
        return get_action_list(self.event, puerpera_inspection_flat_code).all()

    def reevaluate_card_attrs(self):
        """
        Пересчёт атрибутов карточки беременной
        """
        from .card_attrs import reevaluate_risk_rate, \
            reevaluate_pregnacy_pathology, reevaluate_dates, reevaluate_preeclampsia_rate, reevaluate_risk_groups, reevaluate_card_fill_rate_all

        with db.session.no_autoflush:
            reevaluate_risk_rate(self)
            reevaluate_pregnacy_pathology(self)
            reevaluate_dates(self)
            reevaluate_preeclampsia_rate(self)
            reevaluate_risk_groups(self)
            reevaluate_card_fill_rate_all(self)


class GynecologicCard(AbstractCard):
    cache = LocalCache()
    action_type_attrs = gynecological_card_attrs

    def __init__(self, event):
        super(GynecologicCard, self).__init__(event)

    @lazy
    def anamnesis(self):
        return get_action(self.event, risar_gyn_general_anamnesis_flat_code, True)

    @lazy
    def checkups(self):
        return get_action_list(self.event, risar_gyn_checkup_flat_codes).all()


classes = {
    request_type_pregnancy: PregnancyCard,
    request_type_gynecological: GynecologicCard,
}
