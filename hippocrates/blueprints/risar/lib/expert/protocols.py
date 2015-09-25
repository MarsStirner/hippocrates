# -*- coding: utf-8 -*-

import datetime

from collections import defaultdict
from sqlalchemy.orm import aliased

from nemesis.lib.utils import safe_date, safe_int, safe_datetime, safe_bool
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKBAssoc, EventMeasure, ExpertProtocol,
    ExpertSchemeMeasureAssoc, rbMeasureType, Measure)
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus, MeasureScheduleType
from blueprints.risar.lib.utils import get_event_diag_mkbs
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.lib.time_converter import DateTimeUtil
from blueprints.risar.lib.datetime_interval import DateTimeInterval, get_intersection_type, IntersectionType


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
        actual_mkbs = get_actual_mkbs(action)
        # logger.debug('Action <{0}> mkbs: {1}'.format(action_id, action_mkb_list))
        obj = cls(action, actual_mkbs['action'], actual_mkbs['event'], start_date, end_date)
        return obj

    def __init__(self, action, action_mkb_list=None, event_mkb_list=None, period_start_date=None, period_end_date=None):
        self.source_action = action
        self.action_mkb_list = action_mkb_list
        self.event_mkb_list = event_mkb_list
        self.existing_measures = None
        # self.period_start_date = period_start_date
        # self.period_end_date = period_end_date
        self.context = None

    def generate_measures(self):
        # basic plan:
        # 0) delete existing (temporary step)
        # 1) select scheme measures that fit source action mkbs
        # 2) filter scheme measures by theirs schedules (is SM acceptable for now)
        # 3) create event measures from schemes
        #   - EMs that fit time interval from current action to next action should be presented in single instance
        #   - EMs that lie in time interval, relative to reference date, should contain only subset of EM group, where
        #     each element falls into time interval from current action to next action
        # 4) resolve conflicts between old and new event measures
        #   4.1) filter duplicates by SchemeMeasure among created and existing actual EMs
        #   - based on event_measure.scheme_measure.apply_type:
        #
        #     [EMs that reside on time interval from current action to next action]
        #   - check for existing event measures from current action that have same SchemeMeasure.id
        #     - if not present: create new
        #     - else: pass or perform more sophisticated checks (date, status, ...)
        #
        #     [EMs, forming a group, that reside on time interval, relative to reference date.
        #      This interval can contain EMs from different actions]
        #   - or check for existing event measures from all actions (previous and current)
        #     - if not present: create new
        #     - else:
        #       - check whether EM from previous actions fits current EM group
        #         (and what if EM from previous actions now becomes invalid on dates because of significant change of
        #          current action pregnancy week?)
        #         - if fits: ignore it
        #         - else: ignore it? [overall it can be more EM in a group, than defined in schedule???]
        #       - somehow, based on data from previous EMs in group, create missing EMs
        #   4.2) filter duplicates by Measure among created and existing actual EMs
        #     - do not remove Em that have same Measure but different SchemeMeasure
        # 5) handle create-alert flag
        #   - just return number of newly created EMs
        # 6) update expired status on existing EMs, that should have ended before current action
        # 7) save new and update old event measures

        # TODO: ~_~
        # self._clear_existing_measures()
        # return

        # prepare
        self.context = MeasureGeneratorRisarContext(self.source_action, self.action_mkb_list, self.event_mkb_list)
        self._load_existing_measures()

        # go
        spawner_list = self._select_scheme_measures()
        sm_to_exist_list = self._filter_scheme_measures(spawner_list)
        em_list = self._create_event_measures(sm_to_exist_list)
        em_list = self._filter_em_duplicates_by_sm(em_list)
        em_list = self._filter_em_duplicates_by_measure(em_list)
        expired_em_list = self._update_expired_event_measures()
        self.save_event_measures(*(em_list+expired_em_list))
        return len(em_list)

    def _load_existing_measures(self):
        self.existing_measures = defaultdict(list)
        self.existing_action_measures = defaultdict(list)
        query = db.session.query(EventMeasure).filter(
            EventMeasure.event_id == self.source_action.event_id,
            EventMeasure.deleted == 0
        )
        for em in query:
            self.existing_measures[em.schemeMeasure_id].append(em)
            if em.sourceAction_id == self.source_action.id:
                self.existing_action_measures[em.schemeMeasure_id].append(em)

    def _clear_existing_measures(self):
        db.session.query(EventMeasure).filter(
            EventMeasure.sourceAction_id == self.source_action.id
        ).delete()
        db.session.commit()

    def _update_expired_event_measures(self):
        cur_dt = datetime.datetime.now()
        em_list = []
        for sm_id, em_list in self.existing_measures.iteritems():
            for em in em_list:
                if em.endDateTime < cur_dt and em.status != MeasureStatus.cancelled[0]:
                    em.status = MeasureStatus.cancelled[0]
                    em_list.append(em)
        return em_list

    def _select_scheme_measures(self):
        return [
            ActionMkbSpawner(self.source_action, mkb)
            for mkb in self.action_mkb_list
        ]

    def _filter_scheme_measures(self, spawner_list):
        """Return _unique_ scheme_measures, that form event_measures, that
         should exist in event according to current action state.

        :param spawner_list:
        :return:
        """
        unique_sm_id_list = set()
        unique_sm_list = []
        for mkb_spawner in spawner_list:
            for sm in mkb_spawner.scheme_measures:
                if sm not in unique_sm_id_list and self.context.is_scheme_measure_acceptable(sm, mkb_spawner.mkb_code):
                    unique_sm_id_list.add(sm.id)
                    unique_sm_list.append(sm)
        return unique_sm_list

    def _group_by_measure(self, scheme_measures):
        result = defaultdict(list)
        for sm in scheme_measures:
            result[sm.measure_id].append(sm)
        return result

    def _group_by_sm(self, em_list):
        grouped_em = defaultdict(list)
        for em in em_list:
            grouped_em[em.scheme_measure.id].append(em)
        return grouped_em

    def _create_event_measures(self, sm_list):
        # grouping does not make sense in current algorithm implementation
        grouped_sm = self._group_by_measure(sm_list)
        new_em_list = []

        for m_id, sm_list in grouped_sm.iteritems():
            for sm in sm_list:
                if is_multi_scheme_measure(sm):
                    for beg, end in self.context.get_sm_time_interval_list(sm):
                        status = self.context.get_new_status(sm)
                        em = self.create_measure(sm, beg, end, status)
                        new_em_list.append(em)
                else:
                    beg, end = self.context.get_new_sm_time_interval(sm)
                    status = self.context.get_new_status(sm)
                    em = self.create_measure(sm, beg, end, status)
                    new_em_list.append(em)
        return new_em_list

    def _filter_em_duplicates_by_sm(self, em_list):
        # 4.1) filter duplicates by SchemeMeasure among created and existing actual EMs
        #   - based on event_measure.scheme_measure.apply_type:
        #
        #     [EMs that reside on time interval from current action to next action]
        #   - check for existing event measures from current action that have same SchemeMeasure.id
        #     - if not present: create new
        #     - else: pass or perform more sophisticated checks (date, status, ...)
        #
        #     [EMs, forming a group, that reside on time interval, relative to reference date.
        #      This interval can contain EMs from different actions]
        #   - or check for existing event measures from all actions (previous and current)
        #     - if not present: create new
        #     - else:
        #       - check whether EM from previous actions fits current EM group
        #         (and what if EM from previous actions now becomes invalid on dates because of significant change of
        #          current action pregnancy week?)
        #         - if fits: ignore it
        #         - else: ignore it? [overall it can be more EM in a group, than defined in schedule???]
        #       - somehow, based on data from previous EMs in group, create missing EMs

        grouped_em = self._group_by_sm(em_list)
        result = []
        for sm_id, em_list in grouped_em.iteritems():
            scheme_measure = em_list[0].scheme_measure
            apply_type_code = scheme_measure.schedule.apply_type.code
            if apply_type_code == 'before_next_visit':
                filtered_em = self._filter_single_em_sm_producer(scheme_measure, em_list)
                if filtered_em:
                    result.append(filtered_em)
            elif apply_type_code == 'range_up_to':
                filtered_em = self._filter_single_em_sm_producer(scheme_measure, em_list)
                if filtered_em:
                    result.append(filtered_em)
            elif apply_type_code == 'bounds':
                filtered_em_list = self._filter_multiple_em_sm_producer(scheme_measure, em_list)
                result.extend(filtered_em_list)
        return result

    def _filter_single_em_sm_producer(self, sm, em_list):
        sm_id = sm.id
        assert len(em_list) == 1, u'More than 1 EM, created from SM.id = {0}'.format(sm_id)
        if sm_id in self.existing_action_measures:
            pass
            # or perform more sophisticated checks (date, status, ...)
        else:
            return em_list[0]

    def _filter_multiple_em_sm_producer(self, sm, em_list):
        # TODO:
        return em_list

    def _filter_em_duplicates_by_measure(self, em_list):
        # assuming there are not duplicates by scheme_measures
        # but still can be event measure duplicates by measure from different schemes
        # ignoring for now
        return em_list

    def create_measure(self, scheme_measure, beg_dt, end_dt, status):
        em = EventMeasure()
        em.scheme_measure = scheme_measure
        em.begDateTime = beg_dt
        em.endDateTime = end_dt
        em.status = status
        em.source_action = self.source_action
        em.event = self.source_action.event
        return em

    def save_event_measures(self, *event_measures):
        db.session.add_all(event_measures)
        db.session.commit()


class MeasureGeneratorRisarContext(object):

    def __init__(self, action, action_mkb_list, event_mkb_list):
        self.inspection_date = None
        self.next_inspection_date = None
        self.is_first_inspection = None
        self.pregnancy_week = None
        self.existing_diagnoses = None
        self.actual_diagnoses = None
        self.source_action = action
        self.action_mkb_list = action_mkb_list
        self.event_mkb_list = event_mkb_list
        self.load()

    def load(self):
        self.inspection_date = safe_date(self.source_action.begDate)
        self.next_inspection_date = safe_date(self.source_action.propsByCode['next_date'].value)
        self.is_first_inspection = self.source_action.actionType.flatCode == first_inspection_code
        self.pregnancy_week = safe_int(self.source_action.propsByCode['pregnancy_week'].value)
        self.existing_diagnoses = self.event_mkb_list + self.action_mkb_list
        self.actual_diagnoses = self.action_mkb_list

    def is_scheme_measure_acceptable(self, sm, mkb_code):
        return all(self.st_handlers[sched_type.id](self, sm, mkb_code) for sched_type in sm.schedule.schedule_types)

    def _check_st_afv(self, sm, mkb_code):
        return self.is_first_inspection

    def _check_st_wpr(self, sm, mkb_code):
        # assuming units in weeks, TODO: check units and add conversions
        return sm.schedule.boundsLowEventRange <= self.pregnancy_week <= sm.schedule.boundsHighEventRange

    def _check_st_uds(self, sm, mkb_code):
        return mkb_code not in self.existing_diagnoses

    def _check_st_ipd(self, sm, mkb_code):
        return any(mkb.DiagID in self.existing_diagnoses for mkb in sm.schedule.additional_mkbs)

    st_handlers = {
        MeasureScheduleType.getId('after_visit'): lambda *args: True,
        MeasureScheduleType.getId('after_first_visit'): _check_st_afv,
        MeasureScheduleType.getId('within_pregnancy_range'): _check_st_wpr,
        MeasureScheduleType.getId('upon_med_indication'): lambda *args: True,
        MeasureScheduleType.getId('upon_diag_set'): _check_st_uds,
        MeasureScheduleType.getId('in_presence_diag'): _check_st_ipd,
    }

    def get_new_sm_time_interval(self, scheme_measure):
        apply_type_code = scheme_measure.schedule.apply_type.code
        if apply_type_code == 'before_next_visit':
            start_date = self.inspection_date
            end_date = self.next_inspection_date
        elif apply_type_code == 'range_up_to':
            start_date = self.inspection_date
            add_val = scheme_measure.schedule.boundsHighApplyRange
            add_unit_code = scheme_measure.schedule.bounds_high_apply_range_unit.code
            range_end = DateTimeUtil.add_to_date(self.inspection_date, add_val, add_unit_code)
            end_date = range_end if range_end <= self.next_inspection_date else self.next_inspection_date
        else:
            start_date = end_date = None
        return [start_date, end_date]

    def get_sm_time_interval_list(self, scheme_measure):
        apply_type_code = scheme_measure.schedule.apply_type.code
        interval_list = []
        if apply_type_code == 'bounds':
            return self._calc_bounds_sm_dates(scheme_measure)
        return interval_list

    def _calc_bounds_sm_dates(self, scheme_measure):
        cur_w = self.pregnancy_week
        next_w = cur_w + (self.next_inspection_date - self.inspection_date).days / 7
        range_w_start = scheme_measure.schedule.boundsLowApplyRange  # assume in weeks TODO: check units and add conversions
        range_w_end = scheme_measure.schedule.boundsHighApplyRange  # assume in weeks TODO: check units and add conversions
        range_count = scheme_measure.schedule.count or 1
        range_period = scheme_measure.schedule.apply_period  # assume in days TODO: check units and add conversions

        date_list = []
        if get_intersection_type(
            DateTimeInterval(cur_w, next_w),
            DateTimeInterval(range_w_start, range_w_end)
        ) != IntersectionType.none:
            # TODO: fix this
            start_date = DateTimeUtil.add_to_date(self.inspection_date, range_w_start - cur_w, DateTimeUtil.week)  # can result be before event date?
            end_date = DateTimeUtil.add_to_date(self.inspection_date, range_w_end - cur_w, DateTimeUtil.week)
            step = (end_date - start_date).days / range_period
            while start_date < end_date:
                date_list.append(
                    (start_date + datetime.timedelta(days=0), start_date + datetime.timedelta(days=step))
                )
                start_date = start_date + datetime.timedelta(days=step)
        return date_list

    def get_new_status(self, scheme_measure):
        st_list = scheme_measure.schedule.schedule_types
        if len(st_list) == 1 and st_list[0].code == 'upon_med_indication':
            status = MeasureStatus.upon_med_indications[0]
        else:
            status = MeasureStatus.assigned[0]
        return status


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
            self.query = self.query.join(
                ExpertSchemeMeasureAssoc, Measure, rbMeasureType
            ).filter(rbMeasureType.id.in_(flt['measure_type_id_list']))
        if 'beg_date_from' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime >= safe_datetime(flt['beg_date_from']))
        if 'beg_date_to' in flt:
            self.query = self.query.filter(EventMeasure.begDateTime <= safe_datetime(flt['beg_date_to']))
        if 'end_date_from' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime >= safe_datetime(flt['end_date_from']))
        if 'end_date_to' in flt:
            self.query = self.query.filter(EventMeasure.endDateTime <= safe_datetime(flt['end_date_to']))
        if 'measure_status_id_list' in flt:
            self.query = self.query.filter(EventMeasure.status.in_(flt['measure_status_id_list']))
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
        em_selecter = EventMeasureSelecter(event)
        if query_filter is not None:
            paginate = safe_bool(query_filter.get('paginate', True))
            per_page = safe_int(query_filter.get('per_page')) or 20
            page = safe_int(query_filter.get('page')) or 1
            em_selecter.apply_filter(**query_filter)
        else:
            paginate = True
            per_page = 20
            page = 1
        em_selecter.apply_sort_order()

        if paginate:
            return self._paginate_data(em_selecter, per_page, page)
        else:
            return self._list_data(em_selecter)

    def _paginate_data(self, selecter, per_page, page):
        em_data = selecter.paginate(per_page, page)
        return {
            'count': em_data.total,
            'total_pages': em_data.pages,
            'measures': [
                self.represent_measure(event_measure) for event_measure in em_data.items
            ]
        }

    def _list_data(self, selecter):
        em_data = selecter.get_all()
        return {
            'measures': [
                self.represent_measure(event_measure) for event_measure in em_data
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


class ActionMkbSpawner(object):

    def __init__(self, action, mkb):
        self.action = action
        self.mkb_code = mkb
        self.scheme_measures = []
        self.load_schemes()

    def load_schemes(self):
        query = ExpertSchemeMeasureAssoc.query.join(
            ExpertScheme, ExpertSchemeMKBAssoc, ExpertProtocol, MKB
        ).filter(
            ExpertProtocol.deleted == 0,
            ExpertScheme.deleted == 0,
            ExpertSchemeMeasureAssoc.deleted == 0,
            MKB.DiagID == self.mkb_code
        )
        self.scheme_measures = [sm for sm in query.all()]


def get_actual_mkbs(action):
    action_mkb_codes = [mkb.DiagID for mkb in get_event_diag_mkbs(action.event, action_id=action.id)]
    event_mkb_codes = [mkb.DiagID for mkb in get_event_diag_mkbs(action.event, without_action_id=action.id)]
    result = {
        'action': action_mkb_codes,
        'event': event_mkb_codes
    }
    return result


def is_multi_scheme_measure(scheme_measure):
    return scheme_measure.schedule.apply_type.code == 'bounds'