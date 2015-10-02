# -*- coding: utf-8 -*-

import datetime
import logging

from collections import defaultdict
from sqlalchemy.orm import aliased

from nemesis.lib.utils import safe_date, safe_int, safe_datetime, safe_bool
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKBAssoc, EventMeasure, ExpertProtocol,
    ExpertSchemeMeasureAssoc, rbMeasureType, Measure, MeasureSchedule, rbMeasureScheduleApplyType)
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus, MeasureScheduleTypeKind
from blueprints.risar.lib.utils import get_event_diag_mkbs
from blueprints.risar.lib.pregnancy_dates import get_pregnancy_start_date
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.lib.time_converter import DateTimeUtil
from blueprints.risar.lib.datetime_interval import DateTimeInterval, get_intersection_type, IntersectionType

logger = logging.getLogger('simple')


class EventMeasureGenerator(object):
    """Класс, отвечающий за процесс создания мероприятий на основе диагнозов,
    указанных в осмотрах.
    """

    def __init__(self, action):
        self.source_action = action
        self.existing_measures = None
        self.context = None
        self.aux_changed_em_list = []

    def generate_measures(self):
        # basic plan:
        # 0) delete existing (temporary step)
        # 1) select scheme measures that fit source action mkbs
        #   - also include SM from previous actions, if they are still actual (schedule apply type kind is repetitive)
        # 2) filter scheme measures by theirs schedules (is SM acceptable for now)
        #   - filter by current action conditions
        #   - process SM from previous actions accordingly
        # 3) create event measures from schemes
        #   - EMs that fit time interval from current action to next action should be presented in single instance
        #   - EMs that lie in time interval, relative to reference date, should contain only subset of EM group, where
        #     each element falls into time interval from current action to next action
        # 4) resolve conflicts between old and new event measures
        # 4.1) filter duplicates by SchemeMeasure among created and existing actual EMs
        #   - based on event_measure.scheme_measure.apply_type:
        #
        #     [EMs that reside on time interval from current action to next action (current interval)]
        #   - check for existing event measures from current action that have same SchemeMeasure.id
        #     - if not present: put EM in create list
        #     - else: pass or perform more sophisticated checks (date, status, ...)
        #
        #     [EMs, forming a group, that reside on time interval, relative to reference date.
        #      This interval can contain EMs from different actions]
        #   - or process EM group and check for existing event measures from all actions (previous and current)
        #
        #       [maintaining reference for existing EM, that fits current time interval]
        #     - if EM intersects current interval:
        #       - check if there exists EM from previous actions that intersects this EM
        #         - if previous EM exists and it is active (e.g. not cancelled): don't recreate this EM
        #         - else: put EM in create list
        #       - if there are EM left in existing EM list after loop end, then mark them:
        #         - if EM is used (action created): set status to "cancelled, but was started"
        #         - else: set status to "cancelled"
        #
        #     - else [EM doesn't lay in current interval]: ignore it
        #       [can process if needed:
        #       - if EM wasn't created in previous actions: ignore it
        #       - if EM is for future actions: ignore it
        #       - else: ignore it]
        #
        #     - NOTES:
        #       - overall, because of various date shifts between various actions, there can be more or less EMs in
        #         a group, than defined in schedule
        #       - EMs from previous actions can become invalid by dates because of significant change of
        #         current action defining date (e.g. pregnancy week). This should be resolved by using existing
        #         EM list, sorted in begDateTime order, and checking for suitable EM, that fits processed time interval
        # 4.2) filter duplicates by Measure among created and existing actual EMs
        #   - do not remove Em that have same Measure but different SchemeMeasure
        # 5) handle create-alert flag
        #   - just return number of newly created EMs
        # 6) update expired status on existing EMs, that should have ended before current action
        # 7) save new and update old event measures

        # prepare
        self.context = MeasureGeneratorRisarContext(self.source_action)
        self._load_existing_measures()

        # go
        logger.debug(u'> EM generation: start, event_id = {0}'.format(self.source_action.event_id))

        current_action_sm_list = self._select_scheme_measures()
        logger.debug(u'> EM generation [Unfiltered SM]: got SM list from current action id = {0}. Count = {1}'.format(
            self.source_action.id,
            reduce(lambda cur, c: cur + len(c.scheme_measures), current_action_sm_list, 0)
        ))
        sm_to_exist_list = self._filter_sm_from_current_action(current_action_sm_list)
        logger.debug(u'> EM generation [Filtered SM]: SM list from current action id = {0}, which EM should exist. '
                     u'Count = {1} (filtered)'.format(
            self.source_action.id,
            reduce(lambda cur, c: cur + len(c.scheme_measures), current_action_sm_list, 0)
        ))

        existing_em_sm_list = self._select_previous_scheme_measures()
        logger.debug(u'> EM generation [Unfiltered SM]: got SM list from previous EMs. Count = {0}'.format(
            len(existing_em_sm_list)
        ))
        prev_sm_to_exist_swawner_list = self._filter_sm_from_existing_em(existing_em_sm_list)
        logger.debug(u'> EM generation [Filtered SM]: SM list from previous EMs, which EM should exist. '
                     u'Count = {0} (filtered)'.format(
            len(prev_sm_to_exist_swawner_list)
        ))

        new_em_list = self._create_event_measures(sm_to_exist_list)
        em_list_from_prev_em = self._create_event_measures_from_prev_em(prev_sm_to_exist_swawner_list)
        new_em_list.extend(em_list_from_prev_em)
        logger.debug('> EM generation: all EM that should exist created')

        new_em_list = self._filter_em_duplicates_by_sm(new_em_list)
        logger.debug('> EM generation: EM list filtered by SM')

        new_em_list = self._filter_em_duplicates_by_measure(new_em_list)
        logger.debug('> EM generation: EM list filtered by Measure')

        expired_em_list = self._update_expired_event_measures()
        logger.debug('> EM generation: expired EM list processed')

        self.save_event_measures(*(new_em_list + expired_em_list + self.aux_changed_em_list))
        logger.debug('> EM generation: all data saved')
        return len(new_em_list)

    def _load_existing_measures(self):
        self.existing_measures = defaultdict(list)
        self.existing_action_measures = defaultdict(list)
        query = db.session.query(EventMeasure).filter(
            EventMeasure.event_id == self.source_action.event_id,
            EventMeasure.deleted == 0
        ).order_by(
            EventMeasure.begDateTime,
            EventMeasure.id
        )
        for em in query:
            self.existing_measures[em.schemeMeasure_id].append(em)
            if em.sourceAction_id == self.source_action.id:
                self.existing_action_measures[em.schemeMeasure_id].append(em)

    def clear_existing_measures(self):
        db.session.query(EventMeasure).filter(
            EventMeasure.sourceAction_id == self.source_action.id
        ).delete()
        db.session.commit()

    def _update_expired_event_measures(self):
        cur_dt = datetime.datetime.now()
        result = []
        for sm_id, em_list in self.existing_measures.iteritems():
            for em in em_list:
                if em.endDateTime < cur_dt and em.status != MeasureStatus.cancelled[0]:
                    em.status = MeasureStatus.overdue[0]
                    result.append(em)
        return result

    def _select_scheme_measures(self):
        return [
            ActionMkbSpawner(self.source_action, mkb)
            for mkb in self.context.actual_action_mkb
        ]

    def _filter_sm_from_current_action(self, spawner_list):
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

    def _select_previous_scheme_measures(self):
        current_mkb_list = self.context.get_actual_event_diagnoses()
        em_mkb_flt_q = db.session.query(EventMeasure.id.distinct().label('flt_em_id')).join(
            ExpertSchemeMeasureAssoc, ExpertScheme, ExpertSchemeMKBAssoc, MKB
        ).filter(
            EventMeasure.deleted == 0,
            EventMeasure.event_id == self.source_action.event_id,
            EventMeasure.sourceAction_id != self.source_action.id,
            MKB.DiagID.in_(current_mkb_list) if current_mkb_list else False
        ).subquery('EmMkbFilter')

        query = db.session.query(EventMeasure, Action.begDate).join(
            ExpertSchemeMeasureAssoc, MeasureSchedule, rbMeasureScheduleApplyType
        ).join(
            Action, (EventMeasure.sourceAction_id == Action.id)
        ).join(
            em_mkb_flt_q, (EventMeasure.id == em_mkb_flt_q.c.flt_em_id)
        ).filter(
            EventMeasure.deleted == 0,
            EventMeasure.event_id == self.source_action.event_id,
            rbMeasureScheduleApplyType.code == 'bounds'
        )

        current_dt_interval = self.context.get_current_datetime_interval()
        result = []
        for event_measure, action_beg_date in query:
            scheme_measure = event_measure.scheme_measure
            # can filter sm that are still actual on sql level, but not now
            em_group_range_bound_max = scheme_measure.schedule.boundsHighApplyRange  # assumed in weeks, TODO: check units
            end_date = DateTimeUtil.add_to_date(action_beg_date, em_group_range_bound_max, DateTimeUtil.week)  # TODO: units
            em_group_interval = DateTimeInterval(action_beg_date, end_date)
            intersection_em_group = get_intersection_type(current_dt_interval, em_group_interval)
            if IntersectionType.is_intersection(intersection_em_group):
                result.append(
                    EventMeasureSpawner(event_measure)
                )
        return result

    def _filter_sm_from_existing_em(self, spawner_list):
        """Return _unique_ scheme_measures, that form event_measures, that
         should exist in event and that were first spawned in previous actions.

        :param spawner_list:
        :return:
        """
        unique_sm_id_action_id_list = set()
        unique_sm_em_spawner_list = []
        for em_spawner in spawner_list:
            k = (em_spawner.scheme_measure.id, em_spawner.action.id)
            if k not in unique_sm_id_action_id_list:
                unique_sm_id_action_id_list.add(k)
                unique_sm_em_spawner_list.append(em_spawner)
        return unique_sm_em_spawner_list

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
        new_em_list = []

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

    def _create_event_measures_from_prev_em(self, em_spawner_list):
        new_em_list = []

        for em_spawner in em_spawner_list:
            act = em_spawner.action
            sm = em_spawner.scheme_measure
            if is_multi_scheme_measure(sm):
                for beg, end in self.context.get_sm_time_interval_list(sm, act):
                    status = self.context.get_new_status(sm)
                    em = self.create_measure(sm, beg, end, status)
                    new_em_list.append(em)
            # else: pass
            # normally there should not be such case
        return new_em_list

    def _filter_em_duplicates_by_sm(self, em_list):
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
        existing_em_list = self.existing_measures.get(sm.id, [])
        eem_len = len(existing_em_list)
        eem_idx = 0
        current_time_interval = self.context.get_current_datetime_interval()
        result = []
        for em in em_list:
            new_em_time_interval = DateTimeInterval(em.begDateTime, em.endDateTime)
            intersection_cur_interval = get_intersection_type(
                new_em_time_interval,
                current_time_interval
            )
            if not IntersectionType.is_no_intersection(intersection_cur_interval):
                prev_em_fits = False
                while eem_idx < eem_len:
                    prev_em = existing_em_list[eem_idx]
                    interval_prev_em = DateTimeInterval(prev_em.begDateTime, prev_em.endDateTime)
                    intersection_em = get_intersection_type(
                        interval_prev_em,
                        new_em_time_interval
                    )
                    if not IntersectionType.is_no_intersection(intersection_em) and prev_em.is_active:  # TODO: think about active
                        # existing EM fits, don't create new
                        prev_em_fits = True
                        break
                    eem_idx += 1

                if not prev_em_fits:
                    result.append(em)

        # existing, that are unnecessary
        # current eem_idx points to EM that intersects current_time_interval
        if eem_idx + 1 < eem_len:
            for i in range(eem_idx + 1, eem_len):
                em = existing_em_list[i]
                if em.is_used:  # TODO: think about property
                    # TODO: fix status - cancelled, but was assigned
                    em.status = MeasureStatus.cancelled[0]
                else:
                    em.status = MeasureStatus.cancelled[0]
                self.aux_changed_em_list.append(em)
        return result

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

    def __init__(self, action):
        self.inspection_date = None
        self.inspection_datetime = None
        self.next_inspection_date = None
        self.next_inspection_datetime = None
        self.is_first_inspection = None
        self.pregnancy_week = None
        self.pregnancy_start_date = None
        self.source_action = action
        self.all_existing_mkb = set()
        self.actual_existing_mkb = set()
        self.actual_action_mkb = set()
        self.load()

    def load(self):
        self.inspection_date = safe_date(self.source_action.begDate)
        self.inspection_datetime = safe_datetime(self.source_action.begDate)
        self.next_inspection_date = safe_date(self.source_action.propsByCode['next_date'].value)
        self.next_inspection_datetime = safe_datetime(self.next_inspection_date)
        self.is_first_inspection = self.source_action.actionType.flatCode == first_inspection_code
        self.pregnancy_week = safe_int(self.source_action.propsByCode['pregnancy_week'].value)
        self.pregnancy_start_date = get_pregnancy_start_date(self.source_action.event)
        assert isinstance(self.pregnancy_start_date, datetime.date), 'No pregnancy start date in event'
        self._load_mkb_lists()

    def _load_mkb_lists(self):
        all_diag_event = get_event_diag_mkbs(self.source_action.event, without_action_id=self.source_action.id)
        for diag in all_diag_event:
            self.all_existing_mkb.add(diag.DiagID)

        actual_diag_event = get_event_diag_mkbs(self.source_action.event, without_action_id=self.source_action.id,
                                                opened=True)
        for diag in actual_diag_event:
            self.actual_existing_mkb.add(diag.DiagID)

        actual_diag_action = get_event_diag_mkbs(self.source_action.event, action_id=self.source_action.id, opened=True)
        for diag in actual_diag_action:
            self.actual_action_mkb.add(diag.DiagID)

    def is_scheme_measure_acceptable(self, sm, mkb_code):
        return all(self.st_handlers[sched_type.code](self, sm, mkb_code) for sched_type in sm.schedule.schedule_types)

    def _check_st_afv(self, sm, mkb_code):
        return self.is_first_inspection

    def _check_st_wpr(self, sm, mkb_code):
        # assuming units in weeks, TODO: check units and add conversions
        return sm.schedule.boundsLowEventRange <= self.pregnancy_week <= sm.schedule.boundsHighEventRange

    def _check_st_uds(self, sm, mkb_code):
        return mkb_code not in self.all_existing_mkb

    def _check_st_ipd(self, sm, mkb_code):
        return any(mkb.DiagID in self.actual_existing_mkb for mkb in sm.schedule.additional_mkbs)

    st_handlers = {
        'after_visit': lambda *args: True,
        'after_first_visit': _check_st_afv,
        'within_pregnancy_range': _check_st_wpr,
        'upon_med_indication': lambda *args: True,
        'upon_diag_set': _check_st_uds,
        'in_presence_diag': _check_st_ipd,
    }

    def get_new_sm_time_interval(self, scheme_measure):
        apply_type_code = scheme_measure.schedule.apply_type.code
        if apply_type_code == 'before_next_visit':
            start_date = self.inspection_datetime
            end_date = self.next_inspection_datetime
        elif apply_type_code == 'range_up_to':
            start_date = self.inspection_datetime
            add_val = scheme_measure.schedule.boundsHighApplyRange
            add_unit_code = scheme_measure.schedule.bounds_high_apply_range_unit.code
            range_end = DateTimeUtil.add_to_date(self.inspection_datetime, add_val, add_unit_code)
            end_date = range_end if range_end <= self.next_inspection_datetime else self.next_inspection_datetime
        else:
            start_date = end_date = None
        return [start_date, end_date]

    def get_sm_time_interval_list(self, scheme_measure, source_action=None):
        apply_type_code = scheme_measure.schedule.apply_type.code
        interval_list = []
        if apply_type_code == 'bounds':
            if is_sm_bounds_relative_to_inspection(scheme_measure):
                em_group_range_bound_max = scheme_measure.schedule.boundsHighApplyRange  # assume in weeks TODO: check units and add conversions
                em_group_range_period = scheme_measure.schedule.applyPeriod  # assume in days TODO: check units and add conversions
                start_date = (
                    safe_datetime(source_action.begDate)
                    if source_action is not None
                    else self.inspection_datetime
                )
                end_date = DateTimeUtil.add_to_date(start_date, em_group_range_bound_max, DateTimeUtil.week)
                interval_list = self._calc_bounds_sm_dates(
                    MeasureScheduleTypeKind.absolute_dates[0],
                    start_date, end_date, em_group_range_period, None,
                    DateTimeInterval(start_date, end_date)
                )
            elif is_sm_bounds_relative_to_ref_date(scheme_measure):
                em_group_range_w_start = scheme_measure.schedule.boundsLowEventRange  # assume in weeks TODO: check units and add conversions
                em_group_range_w_end = scheme_measure.schedule.boundsHighEventRange  # assume in weeks TODO: check units and add conversions
                em_group_range_period = scheme_measure.schedule.applyPeriod  # assume in days TODO: check units and add conversions
                start_date = DateTimeUtil.add_to_date(self.pregnancy_start_date, em_group_range_w_start, DateTimeUtil.week)
                end_date = DateTimeUtil.add_to_date(self.pregnancy_start_date, em_group_range_w_end, DateTimeUtil.week)
                interval_list = self._calc_bounds_sm_dates(
                    MeasureScheduleTypeKind.relative_dates[0],
                    start_date, end_date, em_group_range_period, None,
                    DateTimeInterval(em_group_range_w_start, em_group_range_w_end)
                )
        return interval_list

    def _calc_bounds_sm_dates(self, sched_type_kind, start_date, end_date, period, period_unit, em_group_interval):
        dt_list = []

        if sched_type_kind == MeasureScheduleTypeKind.absolute_dates[0]:
            # TODO: check
            current_interval_dt = self.get_current_datetime_interval()
            intersection_em_group = get_intersection_type(current_interval_dt, em_group_interval)
            if not IntersectionType.is_no_intersection(intersection_em_group):
                while start_date < end_date:
                    dt_list.append((
                        safe_datetime(start_date + datetime.timedelta(days=0)),
                        safe_datetime(DateTimeUtil.add_to_date(start_date, period, DateTimeUtil.day))  # TODO: unit
                    ))
                    start_date = DateTimeUtil.add_to_date(start_date, period, DateTimeUtil.day)
        elif sched_type_kind == MeasureScheduleTypeKind.relative_dates[0]:
            current_interval_weeks = self.get_current_preg_weeks_interval()
            intersection_em_group = get_intersection_type(current_interval_weeks, em_group_interval)
            if not IntersectionType.is_no_intersection(intersection_em_group):
                while start_date < end_date:
                    dt_list.append((
                        safe_datetime(start_date + datetime.timedelta(days=0)),
                        safe_datetime(DateTimeUtil.add_to_date(start_date, period, DateTimeUtil.day))  # TODO: unit
                    ))
                    start_date = DateTimeUtil.add_to_date(start_date, period, DateTimeUtil.day)
        return dt_list

    def get_new_status(self, scheme_measure):
        st_list = scheme_measure.schedule.schedule_types
        if len(st_list) == 1 and st_list[0].code == 'upon_med_indication':
            status = MeasureStatus.upon_med_indications[0]
        else:
            status = MeasureStatus.assigned[0]
        return status

    def get_current_preg_weeks_interval(self):
        """Вернуть интервал в неделях беременности от текущего осмотра до следующего"""
        cur_w = self.pregnancy_week
        next_w = cur_w + (self.next_inspection_date - self.inspection_date).days / 7  # TODO: check this, +1?
        return DateTimeInterval(cur_w, next_w)

    def get_current_datetime_interval(self):
        """Вернуть интервал дат-времени от текущего осмотра до следующего"""
        return DateTimeInterval(self.inspection_datetime, self.next_inspection_datetime)

    def get_actual_event_diagnoses(self):
        return self.actual_existing_mkb


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


class EventMeasureSpawner(object):

    def __init__(self, em):
        self.event_measure = em
        self.scheme_measure = em.scheme_measure
        self.action = em.source_action


def is_multi_scheme_measure(scheme_measure):
    return scheme_measure.schedule.apply_type.code == 'bounds'


def is_sm_bounds_relative_to_inspection(scheme_measure):
    allowed_codes = ['after_visit', 'after_first_visit', 'upon_med_indication']
    forbidden_codes = ['within_pregnancy_range']
    result = False
    for st in scheme_measure.schedule.schedule_types:
        if st.code in forbidden_codes:
            return False
        if st.code in allowed_codes:
            result = True
    return result


def is_sm_bounds_relative_to_ref_date(scheme_measure):
    allowed_codes = ['within_pregnancy_range']
    forbidden_codes = ['after_visit', 'after_first_visit', 'upon_med_indication']
    result = False
    for st in scheme_measure.schedule.schedule_types:
        if st.code in forbidden_codes:
            return False
        if st.code in allowed_codes:
            result = True
    return result