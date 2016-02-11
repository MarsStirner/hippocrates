# -*- coding: utf-8 -*-
from weakref import WeakKeyDictionary

from blueprints.risar.lib.card_attrs import get_card_attrs_action
from blueprints.risar.lib.utils import get_action, get_action_list
from blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, checkup_flat_codes, \
    risar_anamnesis_pregnancy

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
        return get_action(self._event, risar_mother_anamnesis)

    @lazy
    def father(self):
        return get_action(self._event, risar_father_anamnesis)


class PregnancyCard(object):
    def __init__(self, event):
        self.event = event
        self._anamnesis = Anamnesis(event)

    @property
    def anamnesis(self):
        return self._anamnesis

    @lazy
    def checkups(self):
        return get_action_list(self.event, checkup_flat_codes).all()

    @lazy
    def prev_pregs(self):
        return get_action_list(self.event, risar_anamnesis_pregnancy).all()

    @lazy
    def attrs(self):
        return get_card_attrs_action(self.event)

    @classmethod
    def get_for_event(cls, event):
        """
        :rtype: PregnancyCard
        :param event:
        :return:
        """
        from flask import g
        if not hasattr(g, '_pregnancy_card_cache'):
            g._pregnancy_card_cache = {}
        if event.id not in g._pregnancy_card_cache:
            result = g._pregnancy_card_cache[event.id] = cls(event)
        else:
            result = g._pregnancy_card_cache[event.id]
        return result
