# -*- coding: utf-8 -*-
import datetime
import itertools
import sqlalchemy

from weakref import WeakValueDictionary
from collections import defaultdict
from sqlalchemy import and_, func

from hippocrates.blueprints.risar.lib.helpers import lazy, LocalCache
from hippocrates.blueprints.risar.lib.utils import get_action, get_action_list
from hippocrates.blueprints.risar.lib.prev_children import get_previous_children
from hippocrates.blueprints.risar.lib.fetus import get_fetuses
from hippocrates.blueprints.risar.lib.expert.em_get import get_latest_measures_in_event
from hippocrates.blueprints.risar.models.fetus import RisarFetusState
from hippocrates.blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, checkup_flat_codes, \
    risar_anamnesis_pregnancy, pregnancy_card_attrs, gynecological_card_attrs, risar_anamnesis_transfusion, \
    puerpera_inspection_flat_code, risar_gyn_general_anamnesis_flat_code, risar_gyn_checkup_flat_codes, \
    request_type_gynecological, request_type_pregnancy, risar_epicrisis, first_inspection_flat_code,\
    second_inspection_flat_code, pc_inspection_flat_code
from nemesis.lib.data import create_action
from nemesis.models.actions import Action, ActionType, create_property
from nemesis.lib.utils import safe_bool
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


class PrimaryInspection(object):
    def __init__(self, action):
        self._action = action

    @property
    def action(self):
        return self._action


class RepeatedInspection(object):
    def __init__(self, action):
        self._action = action

    @property
    def action(self):
        return self._action

    @lazy
    def fetuses(self):
        return get_fetuses(self._action.id)


class Epicrisis(object):
    def __init__(self, event):
        self._event = event

    @lazy
    def action(self):
        return get_action(self._event, risar_epicrisis, True)


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
        self._epicrisis = Epicrisis(event)

    def check_card_attrs_action_integrity(self, action):
        """
        Проверка, что в action, соответствующего атрибутам карточки, существуют
        все необходимые свойства.
        :param action: действие с атрибутами
        :type action: nemesis.models.actions.Action
        :return: None
        """

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
        return get_action_list(self.event, checkup_flat_codes).order_by(Action.begDate).all()

    @lazy
    def primary_inspection(self):
        for checkup in self.checkups:
            if checkup.actionType.flatCode in (first_inspection_flat_code, pc_inspection_flat_code):
                 return PrimaryInspection(checkup)

    @lazy
    def latest_inspection(self):
        if self.checkups:
            checkup = self.checkups[-1]
            if checkup.actionType.flatCode in (first_inspection_flat_code, pc_inspection_flat_code):
                return PrimaryInspection(checkup)
            elif checkup.actionType.flatCode == second_inspection_flat_code:
                return RepeatedInspection(checkup)

    @lazy
    def latest_rep_inspection(self):
        for checkup in reversed(self.checkups):
            if checkup.actionType.flatCode == second_inspection_flat_code:
                return RepeatedInspection(checkup)

    @lazy
    def latest_inspection_fetus_ktg(self):
        """Последний повторный осмотр, где были заполнены данные КТГ для плода"""
        for checkup in reversed(self.checkups):
            if checkup.actionType.flatCode == second_inspection_flat_code:
                inspection = RepeatedInspection(checkup)
                for fetus in inspection.fetuses:
                    if safe_bool(fetus.ktg_input):
                        return inspection

    @lazy
    def checkups_puerpera(self):
        return get_action_list(self.event, puerpera_inspection_flat_code).all()

    @lazy
    def epicrisis(self):
        return self._epicrisis

    @lazy
    def radz_risk(self):
        from blueprints.risar.lib.radzinsky_risks.calc import get_radz_risk
        return get_radz_risk(self.event, True)

    def reevaluate_card_attrs(self):
        """
        Пересчёт атрибутов карточки беременной
        """
        from .card_attrs import reevaluate_risk_rate, \
            reevaluate_pregnacy_pathology, reevaluate_dates, reevaluate_preeclampsia_rate,\
            reevaluate_risk_groups, reevaluate_card_fill_rate_all
        from .radzinsky_risks.calc import reevaluate_radzinsky_risks

        with db.session.no_autoflush:
            reevaluate_risk_rate(self)
            reevaluate_pregnacy_pathology(self)
            reevaluate_dates(self)
            reevaluate_preeclampsia_rate(self)
            reevaluate_risk_groups(self)
            reevaluate_card_fill_rate_all(self)
            reevaluate_radzinsky_risks(self)

    @lazy
    def unclosed_mkbs(self):
        diagnostics = self.get_client_diagnostics(self.event.setDate, self.event.execDate)
        return set(
            d.MKB
            for d in diagnostics
            if d.diagnosis.endDate is None
        )

    @cache.cached_call
    def get_inspection_diagnoses(self):
        """МКБ, присутствовавшие на каждом осмотре"""
        # все версии диагнозов пациента
        diag_q = db.session.query(Diagnostic).join(
            Diagnosis
        ).filter(
            Diagnosis.deleted == 0,
            Diagnostic.deleted == 0,
            Diagnosis.client_id == self.event.client_id
        ).with_entities(
            Diagnosis.id,
            Diagnosis.setDate.label('beg_date'),
            func.coalesce(Diagnosis.endDate, func.curdate()).label('end_date'),
            Diagnostic.MKB.label('mkb')
        ).subquery('ClientDiagnostics')

        # осмотры, попадающие в интервалы действия диагнозов
        action_mkb_q = db.session.query(Action).join(
            ActionType
        ).join(
            diag_q, and_(func.date(Action.begDate) <= func.coalesce(diag_q.c.end_date, func.curdate()),
                         func.date(func.coalesce(Action.endDate, func.curdate())) >= diag_q.c.beg_date)
        ).filter(
            Action.deleted == 0,
            Action.event_id == self.event.id,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).with_entities(
            Action.id.label('action_id').distinct(), diag_q.c.mkb.label('mkb')
        )

        res = defaultdict(set)
        for action_id, mkb in action_mkb_q:
            res[action_id].add(mkb)
        return res

    @lazy
    def latest_measures_with_result(self):
        em_list = get_latest_measures_in_event(self.event.id, with_result=True)
        res = {}
        for em in em_list:
            res[em.measure.code] = em
        return res


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
