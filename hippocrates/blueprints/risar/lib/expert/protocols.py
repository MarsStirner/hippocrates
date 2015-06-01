# -*- coding: utf-8 -*-
import itertools

from nemesis.lib.utils import logger, safe_date
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import ExpertScheme, ExpertSchemeMKB, EventMeasure, ExpertSchemeMeasureAssoc
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus


def measure_manager_factory(role, action):
    if role == 'generate':
        start_date = safe_date(action.begDate)
        end_date = safe_date(action.propsByCode['next_date'].value)
        return EventMeasureManager.make_generator(action.id, start_date, end_date)
    elif role == 'represent':
        return EventMeasureManager.make_representer(action.id)



class EventMeasureManager(object):
    """Процесс создания мероприятий на основе диагнозов, указанных в осмотрах

    TODO:
      - Подумать как можно проверить, что после сохранения осмотра список мкб не был
    изменен, чтобы избежать перестройки мероприятий
      - Добавить проверки по протоколам
    """

    @classmethod
    def make_generator(cls, action_id, start_date, end_date):
        action = Action.query.get(action_id)
        action_mkb_list = _get_event_mkb_list(action)
        logger.debug('Action <{0}> mkbs: {1}'.format(action_id, action_mkb_list))
        obj = cls(action, action_mkb_list, start_date, end_date)
        return obj

    @classmethod
    def make_representer(cls, action_id):
        action = Action.query.get(action_id)
        obj = cls(action)
        return obj

    def __init__(self, action, action_mkb_list=None, period_start_date=None, period_end_date=None):
        self.action = action
        self.action_mkb_list = action_mkb_list
        self.period_start_date = period_start_date
        self.period_end_date = period_end_date

    def generate_measures(self):
        self.clear_existing_measures()
        act_scheme_measures = [
            ActionSchemeMeasure(act_mkb['action'], act_mkb['mkbs'])
            for act_mkb in self.action_mkb_list
        ]
        for act_sm in act_scheme_measures:
            for sm in act_sm.scheme_measures:
                self.create_measure(sm, act_sm.action)
        db.session.commit()

    def clear_existing_measures(self):
        db.session.query(EventMeasure).filter(
            EventMeasure.sourceAction_id == self.action.id
        ).delete()

    def refresh_measures_status(self, event_id):
        pass

    def create_measure(self, scheme_measure, source_action):
        em = EventMeasure()
        em.scheme_measure = scheme_measure.model
        beg, end = scheme_measure.get_time_interval(self.period_start_date, self.period_end_date)
        em.begDateTime = beg
        em.endDateTime = end
        status = scheme_measure.get_new_status()
        em.status = status
        em.source_action = source_action
        em.event = source_action.event

        db.session.add(em)

    def represent_measures(self):
        query = EventMeasure.query.filter(EventMeasure.sourceAction_id == self.action.id)
        return [
            self._represent_measure(event_measure) for event_measure in query
        ]

    def _represent_measure(self, measure):
        return {
            'id': measure.id,
            'event_id': measure.event_id,
            'beg_datetime': measure.begDateTime,
            'end_datetime': measure.endDateTime,
            'status': MeasureStatus(measure.status),
            'source_action_id': measure.sourceAction_id,
            'action_id': measure.action_id,
            'scheme_measure': self._represent_scheme_measure(measure.scheme_measure)
        }

    def _represent_scheme_measure(self, scheme_measure):
        return {
            'scheme': self._represent_scheme(scheme_measure.scheme),
            'measure': self._represent_measure_rb(scheme_measure.measure)
        }

    def _represent_scheme(self, scheme):
        return {
            'id': scheme.id,
            'code': scheme.code,
            'name': scheme.name
        }

    def _represent_measure_rb(self, measure):
        return {
            'id': measure.id,
            'code': measure.code,
            'name': measure.name
        }


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
        )
        self.scheme_measures = [SchemeMeasure(record) for record in query.all()]
        self._filter_by_schedules()

    def _filter_by_schedules(self):
        pass


class SchemeMeasure():
    def __init__(self, model):
        self.model = model

    def get_time_interval(self, start_date, end_date):
        sched_type_code = self.model.schedule.schedule_type.code
        if sched_type_code == 'after_visit':
            start_date = start_date
            end_date = end_date
        elif sched_type_code == 'upon_med_indication':
            start_date = end_date = None
        else:
            start_date = end_date = None
        return [start_date, end_date]

    def get_new_status(self):
        code = self.model.schedule.schedule_type.code
        if code == 'after_visit':
            status = MeasureStatus.assigned[0]
        elif code == 'upon_med_indication':
            status = MeasureStatus.upon_med_indications[0]
        elif code == 'interval_single':
            status = MeasureStatus.assigned[0]
        elif code == 'upon_diag_set':
            status = MeasureStatus.assigned[0]
        else:
            status = MeasureStatus.assigned[0]
        return status