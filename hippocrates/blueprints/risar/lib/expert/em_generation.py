# -*- coding: utf-8 -*-

import datetime
import logging

from collections import defaultdict

from nemesis.lib.data import get_client_diagnostics
from nemesis.lib.utils import safe_date, safe_int, safe_datetime
from nemesis.systemwide import db
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKBAssoc, EventMeasure, ExpertProtocol,
    ExpertSchemeMeasureAssoc)
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus, EventMeasureActuality
from blueprints.risar.lib.expert.utils import (em_final_status_list, em_garbage_status_list,
    is_em_cancellable, is_em_touched, is_em_in_final_status)
from blueprints.risar.lib.utils import is_event_late_first_visit
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
        self.existing_em_list = None
        self.context = None
        self.aux_changed_em_list = []

    def clear_existing_measures(self):
        db.session.query(EventMeasure).filter(
            EventMeasure.sourceAction_id == self.source_action.id
        ).delete()
        db.session.commit()

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
        # 4) Обработать EM_list_exist и SM_list_exist:
        #   - если МКБ схемы отсутствует в списке актуальных МКБ обращения, то отменить интервалы, которые еще не
        #     наступили. Также можно использовать проверку на наличие такой схемы в SM_list и если нет, то отменять?
        #     В итоге максимум на что может повлиять этот шаг - это отменить созданные ранее EM, которые перестали быть
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
        #     NOTES:
        #       - сопоставление ранее созданных с пересоздаваемыми EM не проводить. Могут появиться дубли EM в рамках
        #         одной группы, но у них будут различные статусы
        #       - Здесь также обработается случай, когда текущий осмотр никак не связан с этими интервалами, но
        #         на осмотре уточняется неделя беременности и из-за этого меняется опорная дата, от которой
        #         рассчитываются интервалы.
        #
        #   [Фиксированные границы начала применения]
        #   - подготовить новый набор EM для создания (дата начала рассчитывается по минимальной границе начала
        #     относительно опорной даты, а в случае если она будет меньше даты текущего осмотра и EM не были созданы
        #     ранее по этой схеме - EM_list_exist, то датой начала будет дата осмотра, но только в том случае, если она
        #     не выходит за рассчитанную дату по максимальной границе начала относительно опорной даты, в случае чего
        #     интервал не будет создаваться вообще)
        #   - сравнить список созданных с новым списком:
        #     - проходя по списку созданных, сравнивать каждое EM с новосозданным и если появилось различие, то
        #       - оставшиеся элементы, включая текущий, в списке созданных отменить*** в случае, если это возможно**
        #       - оставшиеся элементы в списке новых поместить в список на создание
        #     NOTES:
        #       - сопоставление ранее созданных с пересоздаваемыми EM не проводить. Могут появиться дубли EM в рамках
        #         одной группы, но у них будут различные статусы
        #       - Здесь также обработается случай, когда текущий осмотр никак не связан с этими интервалами, но
        #         на осмотре уточняется неделя беременности и из-за этого меняется опорная дата, от которой
        #         рассчитываются интервалы.
        #
        #   [Продолжительное безграничное применение]
        #   - если данная SM отсутствует в списке существующих, то
        #     - подготовить одиночное EM для создания (с датой начала равной дате осмотра)
        #
        # В результате будут сформированы 2 списка EM - которые нужно создать и которые нужно обновить
        # 6) Проверить на дубликаты EM, имеющих одинаковые Measure (среди существующих и создаваемых)
        #   - оставлять только одно EM с более коротким(быстрым) сроком, оставшиеся помечать статусом Отмены с дублем
        # 7) Обработать отметку об изменении набора мероприятий
        #   - просто вернуть флаг, отражающий есть ли изменения или нет
        # 8) обновить статус на Просрочено у существующих EM, которые должны быть закончены до текущего осмотра
        # 9) создать новые и обновить старые EM из двух сформированных списков на сохранение
        # ---
        # Сноски:
        # * - действующие определяются датами и статусами
        # ** - можно отменять те EM, у которых нет направления и результата и установлен подходящий статус
        # *** - под отменой подразумевается перевод в статус Отменено для EM, с которыми не было взаимодействия
        # пользователя и в статус "Отменено, но с мероприятием работали" в случае, если для мероприятия было создано
        # направление или результат. Также стоит учитывать текущие статусы EM.
        # ---

        # prepare
        self.context = MeasureGeneratorRisarContext(self.source_action)
        self._load_existing_measures()

        # go
        msg = u'> EM generation [Start]: event_id = {0}, current action_id = {1}'.format(
            self.source_action.event_id,
            self.source_action.id
        )
        logger.debug(msg)

        current_action_sm_list = self._select_scheme_measures_from_current_state()
        msg = u'> EM generation [Get new SMs]: got SM list from current action id = {0}. Count = {1}'.format(
            self.source_action.id,
            reduce(lambda cur, c: cur + len(c.scheme_measures), current_action_sm_list, 0)
        )
        logger.debug(msg)

        sm_to_exist_list = self._filter_sm_from_current_state(current_action_sm_list)
        msg = (u'> EM generation [Filter new SMs]: SM list from current action id = {0}, which EM should exist. '
               u'Count = {1} (filtered)').format(
            self.source_action.id,
            len(sm_to_exist_list)
        )
        logger.debug(msg)

        existing_em_count = reduce(lambda cur, item: cur + len(item[1]), self.existing_em_list.iteritems(), 0)
        cancelled_em_list = self._process_existing_em_list(sm_to_exist_list)
        self.aux_changed_em_list.extend(cancelled_em_list)
        msg = u'> EM generation [Process existing EMs]: {0} EMs were cancelled, new count = {1}'.format(
            len(cancelled_em_list),
            existing_em_count - len(cancelled_em_list)
        )
        logger.debug(msg)

        new_em_list = self._create_event_measures(sm_to_exist_list)
        msg = u'> EM generation [Create EMs of current action SMs]: got all EMs that should exist, count = {0}'.format(
            len(new_em_list)
        )
        logger.debug(msg)

        old_changed_em_len = len(self.aux_changed_em_list)
        new_em_list = self._process_new_em_list(new_em_list)
        msg = (u'> EM generation [Filter renewed EMs of current action]: after comparing - {0} cancelled existing EMs, '
               u'{1} - new or recreated EMs').format(
            len(self.aux_changed_em_list) - old_changed_em_len,
            len(new_em_list)
        )
        logger.debug(msg)

        # TODO: implement this step
        new_em_list = self._filter_em_duplicates_by_measure(new_em_list)
        logger.debug(u'> EM generation [filter all by Measure]')

        expired_em_list = self._update_expired_event_measures(new_em_list)
        msg = u'> EM generation [Process expired EMs]: total number of EMs, set to overdue - {0}'.format(
            len(expired_em_list)
        )
        logger.debug(msg)

        edited_items = (new_em_list + expired_em_list + self.aux_changed_em_list)
        self.save_event_measures(*edited_items)
        logger.debug(u'> EM generation: all data saved')
        return bool(new_em_list)

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

    def _group_by_sm_action(self, em_list):
        grouped_em = defaultdict(list)
        for em in em_list:
            key = (em.schemeMeasure_id, em.sourceAction_id)
            grouped_em[key].append(em)
        return grouped_em

    def _filter_actual_existing_ems(self, em_list):
        """Оставить среди существующих EM только такие, которые влияют на проверки при
        сравнении с заново сформированным списком тех EM, которые должны существовать
        по текущим параметрам."""
        return [em for em in em_list if em.is_actual == EventMeasureActuality.actual[0]]

    def _get_cond_start_dt(self, sm):
        """Получение даты начала для вычисления интервалов EM для способа применения
        "Фиксированные границы начала применения".

        Дата начала рассчитывается по минимальной границе начала относительно опорной даты,
        а в случае если она будет меньше даты текущего осмотра и EM не были созданы ранее по этой схеме, то
        датой начала будет дата осмотра, но только в том случае, если она не выходит за рассчитанную дату
        по максимальной границе начала относительно опорной даты, в случае чего интервал не будет
        создаваться вообще.
        """
        min_beg_range = sm.schedule.applyBoundRangeLow
        min_beg_range_unit_code = sm.schedule.apply_bound_range_low_unit.code
        max_beg_range = sm.schedule.applyBoundRangeLowMax
        max_beg_range_unit_code = sm.schedule.apply_bound_range_low_max_unit.code
        ref_date = self.context.get_reference_dt()
        inspection_dt = self.context.inspection_datetime
        pos_start_dt_min = DateTimeUtil.add_to_date(ref_date, min_beg_range, min_beg_range_unit_code)
        # TODO: исправить проблему для ситуации, когда были созданы EM по одной схеме,
        # после чего параметры расписания схемы существенно поменялись.
        # В этом случае существующие EM являются неактуальными и должны быть отмечены этим признаком,
        # и EM должны быть пересозданы по новым данным схемы.
        if sm.id in self.existing_em_list.keys():
            start_dt = self.existing_em_list[sm.id][0].begDateTime
        else:
            pos_start_dt_max = DateTimeUtil.add_to_date(ref_date, max_beg_range, max_beg_range_unit_code)
            if pos_start_dt_min < inspection_dt <= pos_start_dt_max:
                start_dt = inspection_dt
            else:
                start_dt = pos_start_dt_min
        return start_dt

    def _load_existing_measures(self):
        self.existing_em_list = defaultdict(list)
        self.existing_action_em_list = defaultdict(list)
        query = db.session.query(EventMeasure).filter(
            EventMeasure.event_id == self.source_action.event_id,
            EventMeasure.deleted == 0,
            EventMeasure.schemeMeasure_id > 0,  # отсекаем ручные мероприятия
            EventMeasure.status.notin_(tuple(em_garbage_status_list)),
            EventMeasure.is_actual == EventMeasureActuality.actual[0]
        ).order_by(
            EventMeasure.begDateTime,
            EventMeasure.id
        )
        for em in query:
            self.existing_em_list[em.schemeMeasure_id].append(em)
            if em.sourceAction_id == self.source_action.id:
                self.existing_action_em_list[em.schemeMeasure_id].append(em)

    def _select_scheme_measures_from_current_state(self):
        mkb_list = self.context.actual_existing_mkb.union(self.context.actual_action_mkb)
        return [
            ActionMkbSpawner(self.source_action, mkb)
            for mkb in mkb_list
        ]

    def _filter_sm_from_current_state(self, spawner_list):
        unique_sm_id_list = set()
        unique_sm_list = []
        for mkb_spawner in spawner_list:
            for sm in mkb_spawner.scheme_measures:
                if (sm.id not in unique_sm_id_list and
                        self.context.is_sm_apply_event_after_each_visit(sm) and
                        self.context.is_scheme_measure_acceptable(
                            sm,
                            mkb_spawner.mkb_code,
                            self.existing_em_list.get(sm.id)
                        )):
                    unique_sm_id_list.add(sm.id)
                    unique_sm_list.append(sm)
        return unique_sm_list

    def _process_existing_em_list(self, sm_to_exist_list):
        """Отменить созданные ранее EM, которые еще не наступили, вследствие того,
        что МКБ таких схем перестал быть актуальным.
        # TODO: доработать описание
        """
        # TODO: check and think
        current_dt_point = DateTimeInterval(self.context.inspection_datetime, None)
        renew_sm_id_list = set([sm.id for sm in sm_to_exist_list])
        result = []
        for sm_id, em_list in self.existing_em_list.iteritems():
            scheme_measure = em_list[0].scheme_measure
            apply_code = scheme_measure.schedule.apply_type.code
            if apply_code == 'rel_obj_date_count':
                grouped_em = self._group_by_sm_action(em_list)
                for (g_sm_id, source_action_id), g_em_list in grouped_em.iteritems():
                    if source_action_id != self.source_action.id:
                        for em in g_em_list:
                            intersect = get_intersection_type(
                                current_dt_point,
                                DateTimeInterval(em.begDateTime, em.endDateTime)
                            )
                            if intersect == IntersectionType.none_left:
                                upd_em = self.cancel_or_deactualize_em(em, MeasureStatus.cancelled_changed_data[0])
                                if upd_em is not None:
                                    result.append(upd_em)
            else:
                if sm_id not in renew_sm_id_list:
                    for em in em_list:
                        intersect = get_intersection_type(
                            current_dt_point,
                            DateTimeInterval(em.begDateTime, em.endDateTime)
                        )
                        if intersect == IntersectionType.none_left:
                            upd_em = self.cancel_or_deactualize_em(em, MeasureStatus.cancelled_changed_data[0])
                            if upd_em is not None:
                                result.append(upd_em)
        return result

    def _create_event_measures(self, sm_list):
        """Сформировать полный список EM с такими атрибутами, которые будут определяться
        на основе текущих данных осмотра и случая. Даты рассчитываются на основе
        способов применения в схемах.

        :param sm_list:
        :return:
        """
        new_em_list = []
        for sm in sm_list:
            apply_code = sm.schedule.apply_type.code
            time_intervals = []
            if apply_code == 'rel_obj_date_count':
                start_dt = self.context.inspection_datetime
                time_intervals = self.context.make_counted_time_intervals(start_dt, sm)
            elif apply_code == 'rel_ref_date_bound_range':
                ref_date = self.context.get_reference_dt()
                bound_low = sm.schedule.applyBoundRangeLow
                bound_low_unit_code = sm.schedule.apply_bound_range_low_unit.code
                bound_high = sm.schedule.applyBoundRangeHigh
                bound_high_unit_code = sm.schedule.apply_bound_range_high_unit.code
                start_range_dt = DateTimeUtil.add_to_date(ref_date, bound_low, bound_low_unit_code)
                end_range_dt = DateTimeUtil.add_to_date(ref_date, bound_high, bound_high_unit_code)
                time_intervals = self.context.make_bounded_time_intervals(start_range_dt, end_range_dt, sm)
            elif apply_code == 'rel_conditional_count':
                start_dt = self._get_cond_start_dt(sm)
                if start_dt:
                    time_intervals = self.context.make_counted_time_intervals(start_dt, sm)
            elif apply_code == 'rel_obj_date_no_end':
                start_dt = self.context.inspection_datetime
                time_intervals = self.context.make_infinite_time_interval(start_dt, sm)

            for beg, end in time_intervals:
                status = self.context.get_new_status(sm)  # TODO:
                em = self.create_measure(sm, beg, end, status)
                new_em_list.append(em)

        return new_em_list

    def _process_new_em_list(self, new_em_list):
        """

        :param new_em_list:
        :return:
        """
        grouped_em = self._group_by_sm(new_em_list)
        result = []
        for sm_id, em_list in grouped_em.iteritems():
            scheme_measure = em_list[0].scheme_measure
            apply_code = scheme_measure.schedule.apply_type.code
            em_to_create = []
            if apply_code == 'rel_obj_date_count':
                em_to_create = self._filter_renewed_em_in_action(em_list, scheme_measure)
            elif apply_code == 'rel_ref_date_bound_range':
                em_to_create = self._filter_renewed_em_in_range(em_list, scheme_measure)
            elif apply_code == 'rel_conditional_count':
                em_to_create = self._filter_renewed_em_in_range(em_list, scheme_measure)
            elif apply_code == 'rel_obj_date_no_end':
                em_to_create = self._filter_renewed_em_no_end(em_list, scheme_measure)
            em_to_create = self._process_past_new_em_list(em_to_create)
            result.extend(em_to_create)
        return result

    def _filter_renewed_em_in_action(self, em_list, sm):
        existing_em_list = self._filter_actual_existing_ems(self.existing_em_list.get(sm.id, []))
        grouped_em = self._group_by_sm_action(existing_em_list)
        key = (sm.id, self.source_action.id)
        # TODO: think
        if key in grouped_em:
            return self._compare_em_lists(em_list, grouped_em[key])
        else:
            return em_list

    def _filter_renewed_em_in_range(self, em_list, sm):
        existing_em_list = self._filter_actual_existing_ems(self.existing_em_list.get(sm.id, []))
        return self._compare_em_lists(em_list, existing_em_list)

    def _compare_em_lists(self, em_list, existing_em_list):
        def is_same(em1, em2):
            return (
                em1.event_id == em2.event_id and
                em1.begDateTime == em2.begDateTime and
                em1.endDateTime == em2.endDateTime
            )

        existing_len = len(existing_em_list)
        new_len = len(em_list)
        idx = 0
        while idx < existing_len:
            exist_em = existing_em_list[idx]
            if new_len <= idx:
                break
            new_em = em_list[idx]
            if not is_same(exist_em, new_em):
                break
            idx += 1
        for em in existing_em_list[idx:]:
            em = self.cancel_or_deactualize_em(em, MeasureStatus.cancelled_changed_data[0])
            if em is not None:
                self.aux_changed_em_list.append(em)
        em_to_create = []
        for em in em_list[idx:]:
            em_to_create.append(em)
        return em_to_create

    def _filter_renewed_em_no_end(self, em_list, sm):
        existing_em_list = self._filter_actual_existing_ems(self.existing_em_list.get(sm.id, []))
        em_to_create = []
        if not existing_em_list:
            em_to_create.extend(em_list)
        return em_to_create

    def _process_past_new_em_list(self, em_to_create):
        """Пометить EM в списке создаваемых, которые заканчиваются ранее даты текущего
        осмотра, как недействительные."""
        current_dt_point = DateTimeInterval(self.context.inspection_datetime, None)
        for em in em_to_create:
            intersect = get_intersection_type(
                DateTimeInterval(em.begDateTime, em.endDateTime),
                current_dt_point
            )
            if intersect == IntersectionType.none_left:
                em.status = MeasureStatus.cancelled_invalid[0]
        return em_to_create

    def _filter_em_duplicates_by_measure(self, em_list):
        # assuming there are not duplicates by scheme_measures
        # but still can be event measure duplicates by measure from different schemes
        # ignoring for now
        return em_list

    def _update_expired_event_measures(self, new_em_list):
        """Перевести просроченные мероприятия в соответствующий статус.
        Проверяются существующий список мероприятий и новый (пере)создаваемый.
        """
        def process_expired(em):
            if em.endDateTime and em.endDateTime < exp_dt:
                em = self.set_event_measure_overdue(em)
                if em is not None:
                    result.append(em)

        exp_dt = max(datetime.datetime.now(), self.context.inspection_datetime)
        result = []
        for sm_id, em_list in self.existing_em_list.iteritems():
            for em in em_list:
                process_expired(em)

        for em in new_em_list:
            process_expired(em)

        return result

    def create_measure(self, scheme_measure, beg_dt, end_dt, status, action=None):
        em = EventMeasure()
        em.scheme_measure = scheme_measure
        em.schemeMeasure_id = scheme_measure.id
        em.begDateTime = beg_dt
        em.endDateTime = end_dt
        em.status = status
        source_action = action if action is not None else self.source_action
        em.source_action = source_action
        em.event = source_action.event
        em.event_id = source_action.event.id
        return em

    def cancel_or_deactualize_em(self, em, status):
        """Отменить EM, если это возможно, в частности с ним не работал пользователь;
        иначе - отметить его как неактуальное.
        """
        if is_em_touched(em) or is_em_in_final_status(em):
            return self.set_event_measure_actuality(em, EventMeasureActuality.not_actual[0])
        else:
            return self.cancel_event_measure(em, status)

    def cancel_event_measure(self, em, status=MeasureStatus.cancelled[0]):
        if is_em_cancellable(em):
            em.status = status
            return em
        return None

    def set_event_measure_actuality(self, em, actuality):
        if em.is_actual != actuality:
            em.is_actual = actuality
            return em
        return None

    def set_event_measure_overdue(self, em):
        if em.status not in em_final_status_list and em.status != MeasureStatus.upon_med_indications[0]:
            em.status = MeasureStatus.overdue[0]
            return em
        return None

    def save_event_measures(self, *event_measures):
        db.session.add_all(event_measures)
        db.session.commit()


class MeasureGeneratorRisarContext(object):

    def __init__(self, action):
        self.inspection_date = None
        self.inspection_datetime = None
        self.is_first_inspection = None
        self.is_late_first_visit = None
        self.pregnancy_start_date = None
        self.source_action = action
        self.all_existing_mkb = set()
        self.actual_existing_mkb = set()
        self.actual_action_mkb = set()

        self.next_inspection_date = None
        self.next_inspection_datetime = None
        self.pregnancy_week = None
        self.load()

    def load(self):
        self.inspection_date = safe_date(self.source_action.begDate)
        self.inspection_datetime = safe_datetime(self.source_action.begDate)
        self.is_first_inspection = self.source_action.actionType.flatCode == first_inspection_code
        self.is_late_first_visit = is_event_late_first_visit(self.source_action.event)
        self.pregnancy_start_date = get_pregnancy_start_date(self.source_action.event)
        assert isinstance(self.pregnancy_start_date, datetime.date), 'No pregnancy start date in event'
        self._load_mkb_lists()

        # unused
        self.next_inspection_date = safe_date(self.source_action.propsByCode['next_date'].value)
        self.next_inspection_datetime = safe_datetime(self.next_inspection_date)
        self.pregnancy_week = safe_int(self.source_action.propsByCode['pregnancy_week'].value)

    def _load_mkb_lists(self):
        diagnostics = get_client_diagnostics(self.source_action.event.client, self.source_action.begDate, self.source_action.endDate, True)

        # Все возможные диагнозы, действовашие на период действия, в том числе закрытые, но не созданные в нём
        self.all_existing_mkb = set(
            d.MKB
            for d in diagnostics
            if not (d.action == self.source_action and d == d.diagnosis.diagnostics[0])
        )

        # Все незакрытые диагнозы, действовавшие на период действия, кроме созданных в нём
        self.actual_existing_mkb = set(
            d.MKB
            for d in diagnostics
            if not (d.action == self.source_action and d == d.diagnosis.diagnostics[0]) and d.endDate is None
        )

        # Все диагнозы, созданные в этом действии
        self.actual_action_mkb = set(
            d.MKB
            for d in diagnostics
            if (d.action == self.source_action and d == d.diagnosis.diagnostics[0]) and d.endDate is None
        )

    def is_sm_apply_event_after_each_visit(self, sm):
        return any(sched_type.code == 'after_each_visit' for sched_type in sm.schedule.schedule_types)

    def is_scheme_measure_acceptable(self, sm, mkb_code, existing_em_by_sm):
        apply_code = sm.schedule.apply_type.code
        created_earlier = bool(existing_em_by_sm)
        depends_on_created_earlier = apply_code in ('rel_ref_date_bound_range', 'rel_ref_date_bound_range',
                                                    'rel_obj_date_no_end')
        acceptable = True
        for sched_type in sm.schedule.schedule_types:
            st_code = sched_type.code
            if st_code == 'after_first_visit':
                acceptable = self._check_st_afv(sm, mkb_code) or (
                    created_earlier if depends_on_created_earlier else False
                )
            elif st_code == 'upon_diag_set':
                acceptable = self._check_st_uds(sm, mkb_code) or (
                    created_earlier if depends_on_created_earlier else False
                )
            elif st_code == 'late_first_visit':
                acceptable = self._check_st_lfv(sm, mkb_code)
            elif st_code == 'in_presence_diag':
                acceptable = self._check_st_ipd(sm, mkb_code)
            elif st_code in ('in_presence_diag', 'text', 'recommended'):
                acceptable = True
            if not acceptable:
                return False
        return acceptable

    def _check_st_afv(self, sm, mkb_code):
        return self.is_first_inspection

    def _check_st_lfv(self, sm, mkb_code):
        return self.is_late_first_visit

    def _check_st_uds(self, sm, mkb_code):
        return mkb_code in self.actual_action_mkb and mkb_code not in self.actual_existing_mkb

    def _check_st_ipd(self, sm, mkb_code):
        diag_list = self.actual_existing_mkb.union(self.actual_action_mkb)
        return all(mkb.DiagID in diag_list for mkb in sm.schedule.additional_mkbs)

    def _make_intervals_in_range(self, start, end, frequency):
        result = []
        total_range_len = (end - start).total_seconds()
        assert total_range_len >= frequency, u'частота повторения больше периода применения в минимальных ед. измерения'
        step_seconds = total_range_len / frequency
        while start < end:
            result.append(
                (start + datetime.timedelta(days=0),
                 DateTimeUtil.add_to_date(start, step_seconds, DateTimeUtil.sec))
            )
            start = DateTimeUtil.add_to_date(start, step_seconds, DateTimeUtil.sec)
        return result

    def make_counted_time_intervals(self, start_dt, sm):
        result = []
        count = sm.schedule.count
        frequency = sm.schedule.frequency
        period = sm.schedule.period
        period_unit_code = sm.schedule.period_unit.code

        for i in xrange(1, count + 1):
            range_start = start_dt + datetime.timedelta(days=0)
            range_end = DateTimeUtil.add_to_date(range_start, period, period_unit_code)
            result.extend(self._make_intervals_in_range(range_start, range_end, frequency))

            start_dt = DateTimeUtil.add_to_date(start_dt, period, period_unit_code)
        return result

    def make_bounded_time_intervals(self, start_range_dt, end_range_dt, sm):
        result = []
        frequency = sm.schedule.frequency
        period = sm.schedule.period
        period_unit_code = sm.schedule.period_unit.code

        while start_range_dt < end_range_dt:
            range_start = start_range_dt + datetime.timedelta(days=0)
            range_end = min(DateTimeUtil.add_to_date(range_start, period, period_unit_code),
                            end_range_dt)
            result.extend(self._make_intervals_in_range(range_start, range_end, frequency))

            start_range_dt = DateTimeUtil.add_to_date(start_range_dt, period, period_unit_code)
        return result

    def make_infinite_time_interval(self, start_dt, sm):
        return [
            (start_dt, None)
        ]

    def get_new_status(self, scheme_measure):
        st_list = scheme_measure.schedule.schedule_types
        if any(1 for st in st_list if st.code == 'upon_med_indication'):
            status = MeasureStatus.upon_med_indications[0]
        else:
            status = MeasureStatus.created[0]
        return status

    def get_reference_dt(self):
        return safe_datetime(self.pregnancy_start_date)

    # unused
    def get_current_preg_weeks_interval(self):
        """Вернуть интервал в неделях беременности от текущего осмотра до следующего"""
        cur_w = self.pregnancy_week
        next_w = cur_w + (self.next_inspection_date - self.inspection_date).days / 7  # TODO: check this, +1?
        return DateTimeInterval(cur_w, next_w)

    # unused
    def get_current_datetime_interval(self):
        """Вернуть интервал дат-времени от текущего осмотра до следующего"""
        return DateTimeInterval(self.inspection_datetime, self.next_inspection_datetime)


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