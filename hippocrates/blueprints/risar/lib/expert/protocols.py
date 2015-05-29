# -*- coding: utf-8 -*-
import itertools

from sqlalchemy.orm import eagerload

from nemesis.lib.utils import logger
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import ExpertScheme, ExpertSchemeMKB, EventMeasure, ExpertSchemeMeasureAssoc
from nemesis.models.exists import MKB


class EventMeasureManager(object):
    """Процесс создания мероприятий на основе диагнозов, указанных в осмотрах

    TODO:
      - Подумать как можно проверить, что после сохранения осмотра список мкб не был
    изменен, чтобы избежать перестройки мероприятий
      - Добавить проверки по протоколам
    """

    @classmethod
    def make_default(cls, action_id):
        action = Action.query.get(action_id)
        action_mkb_list = _get_event_mkb_list(action)
        logger.error('Action <{0}> mkbs: {1}'.format(action_id, action_mkb_list))
        obj = cls(action, action_mkb_list)
        return obj

    def __init__(self, action, action_mkb_list):
        self.action = action
        self.action_mkb_list = action_mkb_list
        self.period_start = None
        self.next_stage_date = None

    def generate_measures(self):
        act_scheme_measures = [ActionSchemeMeasure(act_mkb['action'], act_mkb['mkbs'])
                           for act_mkb in self.action_mkb_list]
        for act_sm in act_scheme_measures:
            for sm in act_sm.scheme_measures:
                print sm
                self.create_measure(sm, act_sm.action)
        db.session.commit()

    def refresh_measures_status(self, event_id):
        pass

    def create_measure(self, scheme_measure, source_action):
        em = EventMeasure()
        em.scheme_measure = scheme_measure.model
        beg, end = scheme_measure.get_time_interval()
        em.begDateTime = beg
        em.endDateTime = end
        status = scheme_measure.get_new_status()
        em.status = status
        em.source_action = source_action
        em.event = source_action.event

        db.session.add(em)

    def represent_measures(self):
        pass


def _get_event_mkb_list(action):
    # TODO: add mkb from rest of event actions
    mkb_list = []
    source_action_mkb = _get_action_mkbs(action)
    if source_action_mkb:
        mkb_list.append({
            'action': action,
            'mkbs': source_action_mkb
        })
    return mkb_list


def _get_action_mkbs(action):
    """mkb from action diagnoses"""
    prop_codes = ['diag', 'diag2', 'diag3']

    def get_mkb_list(prop_value):
        if not isinstance(prop_value, list):
            prop_value = [prop_value] if prop_value is not None else []
        return (diagnostic.mkb for diagnostic in prop_value)

    return list(itertools.chain.from_iterable(
        get_mkb_list(prop.value)
        for p_code, prop in action.propsByCode.iteritems()
        if p_code in prop_codes
    ))


class ActionSchemeMeasure(object):

    def __init__(self, action, mkb_list):
        self.action = action
        self.mkb_list = mkb_list
        self.scheme_measures = []
        self.init_schemes()

    def init_schemes(self):
        query = ExpertSchemeMeasureAssoc.query.join(
            ExpertScheme, ExpertSchemeMKB, MKB
        ).filter(
            MKB.DiagID.in_(self.mkb_list)
        )  # .options(eagerload(ExpertScheme.scheme_measures))
        self.scheme_measures = [SchemeMeasure(record) for record in query.all()]
        self._filter_by_schedules()

    def _filter_by_schedules(self):
        pass


class SchemeMeasure():
    def __init__(self, model):
        self.model = model

    def get_time_interval(self):
        return [None, None]

    def get_new_status(self):
        return 1