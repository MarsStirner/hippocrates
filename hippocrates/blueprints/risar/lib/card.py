# -*- coding: utf-8 -*-
from weakref import WeakKeyDictionary, WeakValueDictionary

import datetime

import functools
import sqlalchemy

from blueprints.risar.lib.utils import get_action, get_action_list
from blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, checkup_flat_codes, \
    risar_anamnesis_pregnancy
from nemesis.lib.data import create_action
from nemesis.models.actions import Action, ActionType
from nemesis.models.diagnosis import Diagnosis
from nemesis.models.diagnosis import Diagnostic
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
        self._card_attrs_action = None

    @property
    def anamnesis(self):
        return self._anamnesis

    @lazy
    def checkups(self):
        return get_action_list(self.event, checkup_flat_codes).all()

    @lazy
    def prev_pregs(self):
        return get_action_list(self.event, risar_anamnesis_pregnancy).all()

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
            reevaluate_pregnacy_pathology, reevaluate_dates, reevaluate_preeclampsia_rate, reevaluate_risk_groups, reevaluate_card_fill_rate_all
        action = self.attrs
        check_card_attrs_action_integrity(action)
        reevaluate_risk_rate(self)
        reevaluate_pregnacy_pathology(self)
        reevaluate_dates(self)
        reevaluate_preeclampsia_rate(self)
        reevaluate_risk_groups(self)
        reevaluate_card_fill_rate_all(self)

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
