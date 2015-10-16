# -*- coding: utf-8 -*-

import datetime
import logging

from collections import defaultdict

from nemesis.lib.utils import safe_date, safe_int, safe_datetime
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKBAssoc, EventMeasure, ExpertProtocol,
    ExpertSchemeMeasureAssoc, MeasureSchedule, rbMeasureScheduleApplyType)
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
        # Базовый алгоритм:
        # 1) Выбрать все необходимые данные:
        #   - Выбрать текущие действующие* мероприятия случая (EM) (-> EM_list_exist) и их схемы (-> SM_list_exist)
        #   - Выбрать все МКБ из диагнозов обращения
        #   - Выбрать все актуальные МКБ из диагнозов обращения
        #   - Выбрать все актуальные МКБ из текущего осмотра
        #   - Инициализировать различные вспомогательные атрибуты
        # 2) Выбрать набор расписаний схем (SM) (-> SM_list), соответствующих МКБ текущего осмотра
        # 3) Отфильтровать SM_list в зависимости от условий применения:
        #   a) верхнего уровня (можно их назвать событиями применения)
        #     - Note: в данный момент используется только одно событие применения (Каждое посещение), которое
        #       определяет работу алгоритма. В будущем могут появиться новые события применения,
        #       которые будут дополнять работу алгоритма.
        #   b) нижнего уровня:
        #     - провести проверку удовлетворяют ли схемы, порожденные текущим осмотром, условиям применения (Первое
        #       посещение, Поздняя явка, При первичной постановке диагноза, При наличии дополнительных диагнозов)
        # 4) Обработать SM_list_exist:
        #   - если МКБ схемы отсутствует в списке актуальных МКБ обращения, то отменить интервалы, которые еще не
        #     наступили (Может быть можно решить это через удаление оставшихся необработанных схем в конце генерации?)
        #     Также можно использовать проверку на наличие такой схемы в SM_list и если нет, то отменять?
        #     В итоге максимум на что может повлиять этот шаг - это отменить созданные ранее, которые перестали быть
        #     актуальными.
        # 5) Обработать SM_list:
        #   [В зависимости от типа применения и списка уже существующих EM и использующихся SM]
        #   [Фиксированное количество применений от осмотра]
        #   - подготовить новый набор EM для создания (с датой начала равной дате осмотра)
        #     [? подумать, может ли изменение параметров осмотра вызвать коллизии между ранее созданными EM и заново
        #      создаваемыми - может, например, дата осмотра]
        #   - если SM по данному экшену(!) уже есть в списке созданных
        #     - проверить, что существующие интервалы совпадают с создаваемыми (см. ниже) и если нет, то
        #       - отменить все EM по этой схеме и осмотру, которые можно отменить**
        #
        #   [Фиксированные границы применения]
        #   - подготовить новый набор EM для создания (с датой начала равной опорной дате)
        #   - сравнить список созданных с новым списком:
        #     - проходя по списку созданных, сравнивать каждое EM с новосозданным и если появилось различие, то
        #       - оставшиеся элементы, включая текущий, в списке созданных отменить*** в случае, если это возможно**
        #       - оставшиеся элементы в списке новых поместить в список на создание
        #       - сопоставление ранее созданных с пересоздаваемыми EM не проводить. Могут появиться дубли EM в рамках
        #         одной группы, но у них будут различные статусы
        #     Здесь также обработается случай, когда текущий осмотр никак не связан с этими интервалами, но на осмотре
        #     уточняется неделя беременности и из-за этого меняется опорная дата, от которой рассчитываются интервалы.
        #
        #   [Фиксированные границы начала применения]
        #   - подготовить новый набор EM для создания (дата начала будет равна опорной дате или в случае, когда дата
        #     начала окажется в прошлом *и* в SM_list_exist нет текущей схемы, то в качестве даты начала использовать
        #     дату осмотра, но только если она попадает в диапазон начала применения; иначе - игнорировать текущую SM)
        #   - сравнить список созданных с новым списком:
        #     - проходя по списку созданных, сравнивать каждое EM с новосозданным и если появилось различие, то
        #       - оставшиеся элементы, включая текущий, в списке созданных отменить*** в случае, если это возможно**
        #       - оставшиеся элементы в списке новых поместить в список на создание
        #       - сопоставление ранее созданных с пересоздаваемыми EM не проводить. Могут появиться дубли EM в рамках
        #         одной группы, но у них будут различные статусы
        #     Здесь также обработается случай, когда текущий осмотр никак не связан с этими интервалами, но на осмотре
        #     уточняется неделя беременности и из-за этого меняется опорная дата, от которой рассчитываются интервалы.
        #
        #   [Продолжительное безграничное применение]
        #   - если данная SM отсутствует в списке существующих, то
        #     - подготовить одиночное EM для создания (с датой начала равной дате осмотра)
        #
        # В результате будут сформирвоаны 2 списка EM - которые нужно создать и которые нужно обновить
        # 6) Проверить на дубликаты EM, имеющих одинаковые Measure (среди существующих и создаваемых)
        #   - оставлять только одно EM с более коротким(быстрым) сроком, оставшиеся помечать статусом Отмены с дублем
        # 5) Обработать отметку об изменении набора мероприятий
        #   - просто вернуть флаг, отражающий есть ли изменения или нет
        # 6) обновить статус на Просрочено у существующих EM, которые должны быть закончены до текущего осмотра
        # 7) создать новые и обновить старые EM из двух сформированных списков на сохранение
        # ---
        # Сноски:
        # * - действующие определяются датами и статусами
        # ** - можно отменять те EM, у которых нет направления и результата и установлен подходящий статус
        # *** - под отменой подразумевается перевод в статус Отменено для EM, с которыми не было взаимодействия
        # пользователя и в статус "Отменено, но с мероприятием работали" в случае, если для мероприятия было создано
        # направление или результат. Также стоит учитывать текущие статусы EM.
        # ---
        #
        # basic plan:
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
                    em = self.create_measure(sm, beg, end, status, act)
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

    def create_measure(self, scheme_measure, beg_dt, end_dt, status, action=None):
        em = EventMeasure()
        em.scheme_measure = scheme_measure
        em.begDateTime = beg_dt
        em.endDateTime = end_dt
        em.status = status
        source_action = action if action is not None else self.source_action
        em.source_action = source_action
        em.event = source_action.event
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