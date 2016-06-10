# -*- coding: utf-8 -*-

import datetime

import functools
import sqlalchemy

from weakref import WeakKeyDictionary, WeakValueDictionary
from collections import defaultdict
from sqlalchemy import and_, func

from blueprints.risar.lib.utils import get_action, get_action_list
from blueprints.risar.lib.prev_children import get_previous_children
from blueprints.risar.lib.fetus import get_fetuses
from blueprints.risar.lib.expert.em_get import get_latest_measures_in_event
from blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, checkup_flat_codes, \
    risar_anamnesis_pregnancy, risar_epicrisis, first_inspection_code, second_inspection_code, \
    pc_inspection_code
from nemesis.lib.data import create_action
from nemesis.lib.utils import safe_bool
from nemesis.models.actions import Action, ActionType
from nemesis.models.diagnosis import Diagnosis, Action_Diagnosis
from nemesis.models.diagnosis import Diagnostic
from nemesis.models.event import Event
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class lazy(object):
    cache = WeakKeyDictionary()

    def __init__(self, func):
        """
        :type func: types.MethodType
        :param func:
        :return:
        """
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance not in self.cache:
            self.cache[instance] = {}
        if self.name not in self.cache[instance]:
            result = self.func(instance)
            self.cache[instance][self.name] = result
            return result
        return self.cache[instance][self.name]


class Anamnesis(object):
    def __init__(self, event):
        self._event = event

    @lazy
    def mother(self):
        return get_action(self._event, risar_mother_anamnesis, True)

    @lazy
    def father(self):
        return get_action(self._event, risar_father_anamnesis, True)


class PreviousPregnancy(object):
    def __init__(self, action):
        self._action = action

    @property
    def action(self):
        return self._action

    @lazy
    def newborn_inspections(self):
        return get_previous_children(self._action.id)


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


class LocalCache(object):
    def __init__(self):
        self._cache = WeakKeyDictionary()

    def cached_call(self, func):
        name = func.__name__

        @functools.wraps(func)
        def wrapper(this, *args, **kwargs):

            if this not in self._cache:
                cache = self._cache[this] = {}
            else:
                cache = self._cache[this]

            frozen_kwargs = tuple(kwargs.items())
            if (name, args, frozen_kwargs) not in cache:
                result = cache[(name, args, frozen_kwargs)] = func(this, *args, **kwargs)
            else:
                result = cache[(name, args, frozen_kwargs)]
            return result

        return wrapper

    def clean(self, this):
        self._cache[this] = {}


class PregnancyCard(object):
    cache = LocalCache()

    def __init__(self, event):
        self._cached = {}
        self.event = event
        self._anamnesis = Anamnesis(event)
        self._epicrisis = Epicrisis(event)
        self._card_attrs_action = None

    @property
    def anamnesis(self):
        return self._anamnesis

    @lazy
    def checkups(self):
        return get_action_list(self.event, checkup_flat_codes).order_by(Action.begDate).all()

    @lazy
    def primary_inspection(self):
        for checkup in self.checkups:
            if checkup.actionType.flatCode in (first_inspection_code, pc_inspection_code):
                return PrimaryInspection(checkup)

    @lazy
    def latest_inspection(self):
        if self.checkups:
            checkup = self.checkups[-1]
            if checkup.actionType.flatCode in (first_inspection_code, pc_inspection_code):
                return PrimaryInspection(checkup)
            elif checkup.actionType.flatCode == second_inspection_code:
                return RepeatedInspection(checkup)

    @lazy
    def latest_rep_inspection(self):
        for checkup in reversed(self.checkups):
            if checkup.actionType.flatCode == second_inspection_code:
                return RepeatedInspection(checkup)

    @lazy
    def latest_inspection_fetus_ktg(self):
        """Последний повторный осмотр, где были заполнены данные КТГ для плода"""
        for checkup in reversed(self.checkups):
            if checkup.actionType.flatCode == second_inspection_code:
                inspection = RepeatedInspection(checkup)
                for fetus in inspection.fetuses:
                    if safe_bool(fetus.ktg_input):
                        return inspection

    @lazy
    def prev_pregs(self):
        return [
            PreviousPregnancy(action)
            for action in get_action_list(self.event, risar_anamnesis_pregnancy).all()
        ]

    @lazy
    def epicrisis(self):
        return self._epicrisis

    @lazy
    def radz_risk(self):
        from blueprints.risar.lib.radzinsky_risks.calc import get_radz_risk
        return get_radz_risk(self.event, True)

    @property
    def attrs(self):
        return self.get_card_attrs_action()

    def get_card_attrs_action(self, auto=False):
        if self._card_attrs_action is None:
            from blueprints.risar.lib.card_attrs import default_AT_Heuristic

            action = Action.query.join(ActionType).filter(
                Action.event == self.event,
                Action.deleted == 0,
                ActionType.flatCode == 'cardAttributes',
            ).first()
            if action is None and auto:
                action = create_action(default_AT_Heuristic().id, self.event)
                self._card_attrs_action = action
                self.reevaluate_card_attrs()
                db.session.add(action)
                db.session.commit()
            self._card_attrs_action = action
        return self._card_attrs_action

    def reevaluate_card_attrs(self):
        """
        Пересчёт атрибутов карточки беременной
        """
        from .card_attrs import check_card_attrs_action_integrity, reevaluate_risk_rate, \
            reevaluate_pregnacy_pathology, reevaluate_dates, reevaluate_preeclampsia_rate, reevaluate_risk_groups, \
            reevaluate_card_fill_rate_all
        from .radzinsky_risks.calc import reevaluate_radzinsky_risks
        with db.session.no_autoflush:
            action = self.attrs
            check_card_attrs_action_integrity(action)
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
            if d.endDate is None
        )

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
        :param beg_date:
        :param end_date:
        :param kinds:
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

    @classmethod
    def get_for_event(cls, event):
        """
        :rtype: PregnancyCard
        :param event:
        :return:
        """
        from flask import g
        if not hasattr(g, '_pregnancy_card_cache'):
            g._pregnancy_card_cache = WeakValueDictionary()
        if event.id not in g._pregnancy_card_cache:
            result = g._pregnancy_card_cache[event.id] = cls(event)
        else:
            result = g._pregnancy_card_cache[event.id]
        return result

