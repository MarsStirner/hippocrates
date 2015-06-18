# -*- coding: utf-8 -*-
import itertools

from sqlalchemy.orm import aliased

from nemesis.lib.utils import safe_date, safe_int, safe_datetime
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKB, EventMeasure, ExpertSchemeMeasureAssoc,
    rbMeasureType, Measure)
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus


class EventMeasureGenerator(object):
    """Класс, отвечающий за процесс создания мероприятий на основе диагнозов,
    указанных в осмотрах.

    TODO:
      - Подумать как можно проверить, что после сохранения осмотра список мкб
    не был изменен, чтобы избежать перестройки мероприятий
      - Добавить проверки по протоколам
    """

    @classmethod
    def create_for_risar(cls, action_id):
        action = Action.query.get(action_id)
        start_date = safe_date(action.begDate)
        end_date = safe_date(action.propsByCode['next_date'].value)
        action_mkb_list = _get_event_mkb_list(action)
        # logger.debug('Action <{0}> mkbs: {1}'.format(action_id, action_mkb_list))
        obj = cls(action, action_mkb_list, start_date, end_date)
        return obj

    def __init__(self, action, action_mkb_list=None, period_start_date=None, period_end_date=None):
        self.action = action
        self.action_mkb_list = action_mkb_list
        self.period_start_date = period_start_date
        self.period_end_date = period_end_date

    def generate_measures(self):
        # self.clear_existing_measures()
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


class EventMeasureSelecter(object):

    def __init__(self, event, action=None):
        self.event = event
        self.query = EventMeasure.query.filter(EventMeasure.event_id == self.event.id)

    def apply_filter(self, action_id=None, **flt):
        if 'id' in flt:
            self.query = self.query.filter(EventMeasure.id == flt['id'])
            return self
        if action_id:
            self.query = self.query.filter(EventMeasure.sourceAction_id == action_id)
        if 'measure_type_id_list' in flt:
            if len(flt['measure_type_id_list']):
                self.query = self.query.join(
                    ExpertSchemeMeasureAssoc, Measure, rbMeasureType
                ).filter(rbMeasureType.id.in_(flt['measure_type_id_list']))
            else:
                self.query = self.query.filter(1 == 0)
        if 'beg_date_from' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime >= safe_datetime(flt['beg_date_from']))
        if 'beg_date_to' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime <= safe_datetime(flt['beg_date_to']))
        if 'end_date_from' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime >= safe_datetime(flt['end_date_from']))
        if 'end_date_to' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime <= safe_datetime(flt['end_date_to']))
        if 'measure_status_id_list' in flt:
            if len(flt['measure_status_id_list']):
                self.query = self.query.filter(EventMeasure.status.in_(flt['measure_status_id_list']))
            else:
                self.query = self.query.filter(1 == 0)
        return self

    def apply_sort_order(self, **order_options):
        desc_order = order_options.get('order', 'ASC') == 'DESC'
        if order_options:
            pass
        else:
            source_action = aliased(Action, name='SourceAction')
            self.query = self.query.join(
                source_action, EventMeasure.sourceAction_id == source_action.id
            ).order_by(
                source_action.begDate.desc(),
                EventMeasure.begDateTime.desc(),
                EventMeasure.id.desc()
            )
        return self

    def get_all(self):
        return self.query.all()

    def paginate(self, per_page=20, page=1):
        return self.query.paginate(page, per_page, False)


class EventMeasureRepr(object):

    def represent_by_action(self, action):
        if not action.id:
            return []
        em_selecter = EventMeasureSelecter(action.event, action)
        em_selecter.apply_filter(action_id=action.id)
        em_data = em_selecter.get_all()
        return [
            self.represent_measure(event_measure) for event_measure in em_data
        ]

    def represent_by_event(self, event, query_filter=None):
        per_page = safe_int(query_filter.get('per_page')) or 20 if query_filter is not None else 20
        page = safe_int(query_filter.get('page')) or 1 if query_filter is not None else 1
        em_selecter = EventMeasureSelecter(event)
        if query_filter:
            em_selecter.apply_filter(**query_filter)
        em_selecter.apply_sort_order()
        em_data = em_selecter.paginate(per_page, page)
        return {
            'count': em_data.total,
            'total_pages': em_data.pages,
            'measures': [
                self.represent_measure(event_measure) for event_measure in em_data.items
            ]
        }

    def represent_measure(self, measure):
        return {
            'id': measure.id,
            'event_id': measure.event_id,
            'beg_datetime': measure.begDateTime,
            'end_datetime': measure.endDateTime,
            'status': MeasureStatus(measure.status),
            'source_action': self.represent_source_action(measure.source_action),
            'action_id': measure.action_id,
            'scheme_measure': self.represent_scheme_measure(measure.scheme_measure)
        }

    def represent_scheme_measure(self, scheme_measure):
        return {
            'scheme': self.represent_scheme(scheme_measure.scheme),
            'measure': self.represent_measure_rb(scheme_measure.measure)
        }

    def represent_scheme(self, scheme):
        return {
            'id': scheme.id,
            'code': scheme.code,
            'name': scheme.name
        }

    def represent_measure_rb(self, measure):
        return {
            'id': measure.id,
            'code': measure.code,
            'name': measure.name,
            'measure_type': measure.measure_type
        }

    def represent_source_action(self, action):
        return {
            'id': action.id,
            'beg_date': action.begDate
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