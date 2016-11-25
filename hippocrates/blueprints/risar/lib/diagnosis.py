# -*- coding: utf-8 -*-

import logging
import datetime

from collections import defaultdict
from sqlalchemy.orm import contains_eager
from sqlalchemy import or_, and_, func

from hippocrates.blueprints.risar.lib.card import AbstractCard
from hippocrates.blueprints.risar.lib.datetime_interval import DateTimeInterval, IntersectionType, get_intersection_type

from nemesis.models.actions import Action, ActionType
from nemesis.models.diagnosis import rbDiagnosisKind, Diagnosis, Diagnostic, Action_Diagnosis
from nemesis.models.expert_protocol import EventMeasure
from nemesis.models.enums import ActionStatus
from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_datetime, safe_traverse, safe_date


logger = logging.getLogger('simple')


def validate_diagnoses(diagnoses):
    if not diagnoses:
        return

    mkbs = defaultdict(int)
    kinds = []
    for diag in diagnoses:
        if diag.get('endDate') is None:
            kinds.append(safe_traverse(diag, 'diagnosis_types', 'final', 'code'))
            diagnostic = diag.get('diagnostic')
            mkb_code = safe_traverse(diag, 'diagnostic', 'mkb', 'code')
            if mkb_code:
                # rimis1311
                if mkbs[mkb_code]:
                    raise ApiException(409, u'У пациента уже есть диагноз с таким кодом МКБ')
                else:
                    mkbs[mkb_code] += 1
    # rimis1310
    if 'main' not in kinds:
        raise ApiException(409, u'Не выбран основной диагноз!')


def get_inspection_primary_diag_mkb(inspection):
    main_kind = rbDiagnosisKind.query.filter(rbDiagnosisKind.code == 'main').first()
    card = AbstractCard.get_for_event(inspection.event)
    diags = card.get_event_diagnostics(inspection.begDate, inspection.endDate, (main_kind.id,))
    if len(diags) > 1:
        logger.warning(u'К осмотру с id={0} относится более одного основного диагноза')
    return diags[0].mkb if diags else None


def get_diagnostics_history(event, beg_date, end_date=None, including_closed=False):
    """
    :type beg_date: datetime.date
    :type end_date: datetime.date | NoneType
    :type including_closed: bool
    :param beg_date:
    :param end_date:
    :param including_closed:
    :return:
    """
    if not beg_date and not end_date:
        return []
    client = event.client
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
    query = query.order_by(
        Diagnostic.setDate, Diagnostic.id
    ).options(contains_eager(Diagnostic.diagnosis))
    return query.all()


def get_first_diagnostics_of_diagnoses(ds_ids):
    if not ds_ids:
        return []
    ds_diagn_dates = db.session.query(func.min(Diagnostic.setDate).label('min_date')).filter(
        Diagnostic.deleted == 0,
        Diagnostic.diagnosis_id.in_(ds_ids)
    ).group_by(Diagnostic.diagnosis_id).subquery('DiagnosisLowestDiagnosticDates')
    ds_diagn_ids = db.session.query(func.min(Diagnostic.id).label('min_id')).join(
        ds_diagn_dates, Diagnostic.setDate == ds_diagn_dates.c.min_date
    ).filter(
        Diagnostic.deleted == 0,
        Diagnostic.diagnosis_id.in_(ds_ids)
    ).group_by(Diagnostic.diagnosis_id).subquery('DiagnosisLowestDiagnosticIds')
    query = db.session.query(Diagnostic).join(
        ds_diagn_ids, Diagnostic.id == ds_diagn_ids.c.min_id
    )
    return query.all()


def get_action_ds_kinds(action_ids, ds_ids):
    if not action_ids or not ds_ids:
        return []
    query = db.session.query(Action_Diagnosis).filter(
        Action_Diagnosis.deleted == 0,
        Action_Diagnosis.action_id.in_(action_ids),
        Action_Diagnosis.diagnosis_id.in_(ds_ids)
    ).order_by(Action_Diagnosis.id)
    return query.all()


def get_prev_inspection_query(action, flatcodes, create_mode=None):
    if create_mode is None:
        create_mode = action.id is None
    return db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        ActionType.flatCode.in_(flatcodes),
        or_(Action.begDate < action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id < action.id if not create_mode else True)
            ),
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1)


def get_next_inspection_query(action, flatcodes, create_mode=None):
    if create_mode is None:
        create_mode = action.id is None
    return db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        ActionType.flatCode.in_(flatcodes),
        or_(Action.begDate > action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id > action.id if not create_mode else False)
            ),
        Action.id != action.id
    ).order_by(Action.begDate).limit(1)


def get_adjacent_inspections(action, flatcodes, create_mode=None):
    left = get_prev_inspection_query(action, flatcodes, create_mode).first()
    right = get_next_inspection_query(action, flatcodes, create_mode).first()
    return left, action, right


def get_adjacent_measure_results(action):
    left = db.session.query(Action).join(ActionType).join(
        EventMeasure, EventMeasure.resultAction_id == Action.id
    ).filter(
        Action.deleted == 0,
        EventMeasure.event_id == action.event.id,
        Action.begDate < action.begDate,
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1).first()
    right = db.session.query(Action).join(ActionType).join(
        EventMeasure, EventMeasure.resultAction_id == Action.id
    ).filter(
        Action.deleted == 0,
        EventMeasure.event_id == action.event.id,
        Action.begDate > action.begDate,
        Action.id != action.id
    ).order_by(Action.begDate).limit(1).first()
    return left, right


def get_3_diagnoses(event, beg_date, end_date, left, cur, right, inter_left, inter_right):
    diagns = get_diagnostics_history(event, beg_date, end_date)
    _used_ds_ids = set()
    # make unique, save order
    ds_ids = [diagn.diagnosis_id for diagn in diagns
              if not (diagn.diagnosis_id in _used_ds_ids or _used_ds_ids.add(diagn.diagnosis_id))]
    # diagnoses' latest versions of diagnostics in each action
    ds_action_diagn_map = {}
    for diagn in diagns:
        # will update existing action_id: diagn with newer version of diagn
        # because of order in diagnostic history query
        ds_action_diagn_map.setdefault(diagn.diagnosis_id, {}).update({
            diagn.action_id: diagn
        })

    action_ids = [a.id for a in (left, cur, right) if a is not None and a.id]
    act_ds_kinds = get_action_ds_kinds(action_ids, ds_ids)
    ds_a_d_map = {}
    for a_d in act_ds_kinds:
        ds_a_d_map.setdefault((a_d.diagnosis_id, a_d.action_id), []).append(a_d)

    inspections = {
        'left_insp': left,
        'right_insp': right,
        'left_measure': inter_left,
        'right_measure': inter_right,
    }
    if inter_left:
        left = inter_left
    if inter_right:
        right = inter_right
    inspections.update({
        'cur': cur,
        'left': left,
        'right': right
    })

    mkb_inspections = {}
    inspection_diags = {}
    for ds_id in ds_ids:
        action_diagns = ds_action_diagn_map[ds_id]
        ds = action_diagns[action_diagns.keys()[0]].diagnosis
        mkb = action_diagns[action_diagns.keys()[0]].MKB
        ds_interval = DateTimeInterval(safe_datetime(ds.setDate), ds.endDate)
        if left and IntersectionType.is_intersection(
                get_intersection_type(
                    ds_interval,
                    DateTimeInterval(left.begDate, left.endDate)
                )):
            diagn = action_diagns.get(left.id)
            mkb_inspections.setdefault(mkb, set()).add('left')
            if diagn and safe_traverse(inspection_diags, 'left', mkb):
                logger.warning(u'Несколько диагнозов с одинаковым МКБ {0} '
                               u'(Diagnosis.id={1}, Diagnostic.id={2})'.format(mkb, ds.id, diagn.id))
            diag_types = {}
            for a_d in ds_a_d_map.get((ds.id, left.id), []):
                diag_types[a_d.diagnosisType.code] = a_d.diagnosisKind.code
            inspection_diags.setdefault('left', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'ds': ds,
                'diag_types': diag_types,
                'a_d_list': ds_a_d_map.get((ds.id, left.id), [])
            })
        if IntersectionType.is_intersection(
                get_intersection_type(
                    ds_interval,
                    DateTimeInterval(cur.begDate, cur.endDate)
                )):
            diagn = action_diagns.get(cur.id)
            mkb_inspections.setdefault(mkb, set()).add('cur')
            if diagn and safe_traverse(inspection_diags, 'cur', mkb):
                logger.warning(u'Несколько диагнозов с одинаковым МКБ {0} '
                               u'(Diagnosis.id={1}, Diagnostic.id={2})'.format(mkb, ds.id, diagn.id))
            diag_types = {}
            for a_d in ds_a_d_map.get((ds.id, cur.id), []):
                diag_types[a_d.diagnosisType.code] = a_d.diagnosisKind.code
            inspection_diags.setdefault('cur', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'ds': ds,
                'diag_types': diag_types,
                'a_d_list': ds_a_d_map.get((ds.id, cur.id), [])
            })
        if right and IntersectionType.is_intersection(
                get_intersection_type(
                    ds_interval,
                    DateTimeInterval(right.begDate, right.endDate)
                )):
            diagn = action_diagns.get(right.id)
            mkb_inspections.setdefault(mkb, set()).add('right')
            if diagn and safe_traverse(inspection_diags, 'right', mkb):
                logger.warning(u'Несколько диагнозов с одинаковым МКБ {0} '
                               u'(Diagnosis.id={1}, Diagnostic.id={2})'.format(mkb, ds.id, diagn.id))
            diag_types = {}
            for a_d in ds_a_d_map.get((ds.id, right.id), []):
                diag_types[a_d.diagnosisType.code] = a_d.diagnosisKind.code
            inspection_diags.setdefault('right', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'ds': ds,
                'diag_types': diag_types,
                'a_d_list': ds_a_d_map.get((ds.id, right.id), [])
            })

    return {
        'by_mkb': mkb_inspections,
        'by_inspection': inspection_diags,
        'inspections': inspections
    }


class AdjasentInspectionsState(object):

    def __init__(self, flatcodes, create_mode=False):
        self.flatcodes = flatcodes
        self.create_mode = create_mode
        self.left = self.cur = self.right = None

    def refresh(self, cur_action):
        self.left, self.cur, self.right = get_adjacent_inspections(cur_action,
            self.flatcodes, self.create_mode)

    def close_previous(self):
        if self.left:
            self.left.endDate = max(
                self.cur.begDate - datetime.timedelta(seconds=1),
                self.left.begDate
            )
            self.left.status = ActionStatus.finished[0]

    def set_cur_enddate(self):
        max_date = self.cur.begDate
        ed = self.right.begDate - datetime.timedelta(seconds=1) if self.right else None
        if max_date:
            self.cur.endDate = max(ed, max_date) if ed is not None else ed
        else:
            self.cur.endDate = ed

    def flush(self):
        db.session.flush()


class DiagnosesSystemManager(object):
    """Класс, отвечающий за обновление диагнозов в существующей
    системе диагнозов в рамках карты пациентки РИСАР.
    """
    class InspectionSource(object):
        def __init__(self, action):
            self.action = action
        def get_date(self):
            return self.action.begDate
        def get_enddate(self):
            return self.action.endDate
        def get_person(self):
            return self.action.person

    class MeasureResultSource(object):
        def __init__(self, action, measure_type):
            self.action = action
            self.measure_type = measure_type
        def get_date(self):
            return self.action.begDate
            # if self.measure_type == MeasureType.checkup[0]:
            #     return self.action['CheckupDate'].value
            # elif self.measure_type == MeasureType.hospitalization[0]:
            #     return self.action['IssueDate'].value
        def get_enddate(self):
            return self.action.endDate
        def get_person(self):
            return self.action.person
            # if self.measure_type == MeasureType.checkup[0]:
            #     return self.action['Doctor'].value
            # elif self.measure_type == MeasureType.hospitalization[0]:
            #     return self.action['Doctor'].value

    @classmethod
    def get_for_inspection(cls, action, diag_type, adj_insp_state, refresh_in_series=False):
        return cls(cls.InspectionSource(action), diag_type, adj_insp_state, refresh_in_series)

    @classmethod
    def get_for_measure_result(cls, action, diag_type, measure_type, adj_insp_state,
                               refresh_in_series=False):
        return cls(cls.MeasureResultSource(action, measure_type), diag_type,
                   adj_insp_state, refresh_in_series)

    def __init__(self, source, diag_type, adj_insp_state, refresh_in_series=False):
        self.source = source
        self.diag_type = diag_type
        self.ais = adj_insp_state
        # source action is being created
        self.create_mode = adj_insp_state.create_mode
        # source action is being deleted
        self.delete_mode = False
        # расчет диагнозов будет осуществляться по нескольким сериям данных с разными diag_type
        self.refresh_in_series = refresh_in_series
        self.existing_diags = None
        self.to_create = []
        self.to_delete = []
        self.to_create_other_action = []

        self.initialize()

    def initialize(self):
        self.existing_diags = self._get_5_inspections_diagnoses()

    def get_result(self):
        return self.to_create, self.to_delete, self.to_create_other_action

    def refresh_with(self, mkb_data_list):
        """Рассчитать изменения в системе диагнозов на основе данных сохранения
        осмотра.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        """
        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']
        action_date = self.source.get_date()
        new_person = self.source.get_person()

        for diag_data in mkb_data_list:
            new_kind = diag_data['kind']
            for mkb in diag_data['mkbs']:
                additional_info = safe_traverse(diag_data, 'additional_info', mkb)
                if mkb in by_mkb:
                    # mkb is in at least one of the inspections (previous, current, next)
                    insp_w_mkb = by_mkb[mkb]

                    # already exists in current action
                    if 'cur' in insp_w_mkb:
                        diag = by_inspection['cur'][mkb]

                        cur_diagn = diag['diagn']
                        diag_types = diag['diag_types']
                        if self.diag_type in diag_types:
                            # diag_type_exists
                            diag_kind = diag_types[self.diag_type]
                        elif len(diag_types):
                            # diag_type_not_exists
                            diag_kind = None
                        else:
                            # diag_type_exists
                            diag_kind = 'associated'
                        kind_changed = diag_kind != new_kind or self.create_mode
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = diag['ds'].endDate
                        diagnosis_id = diag['ds'].id
                        dg_person_id = diag['diagn'].modifyPerson_id if cur_diagn else None
                        dgn_bd = cur_diagn.setDate if cur_diagn else None
                        dgn_cd = cur_diagn.createDatetime if cur_diagn else None
                        diagnostic_changed = self.create_mode or dgn_bd != action_date or \
                            dgn_cd != action_date or dg_person_id != new_person.id
                        if additional_info:
                            diagnostic_changed = diagnostic_changed or \
                                diag['diagn'].traumaType_id != safe_traverse(additional_info, 'trauma', 'id') or \
                                diag['diagn'].character_id != safe_traverse(additional_info, 'character', 'id') or \
                                diag['diagn'].MKBEx != safe_traverse(additional_info, 'mkb2', 'code') or \
                                diag['diagn'].rbAcheResult_id != safe_traverse(additional_info, 'ache_result', 'id')
                        if 'left' not in insp_w_mkb:
                            # diag was created exactly in current action
                            ds_beg_date = action_date
                        if 'right' not in insp_w_mkb:
                            # close or open ds
                            ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())

                        if cur_diagn and diagnostic_changed:
                            # need to delete dgn because it can have higher date than the date of 'cur' inspection
                            cur_diagn.deleted = 1
                            self.to_delete.append(cur_diagn)

                    # not in current yet, but can be in one of adjacent:
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # diag is in the left and in the right -
                        # there are 2 different diagnoses, and left ds will be extended
                        # to include new diagn, right diagn will not be changed
                        diag_l = by_inspection['left'][mkb]
                        diagnosis_id = diag_l['ds'].id
                        ds_beg_date = diag_l['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())
                        diagnostic_changed = kind_changed = True
                    elif 'left' in insp_w_mkb:
                        # ds from previous inspection that ends by the time of right inspection or remains opened
                        diag_l = by_inspection['left'][mkb]
                        diagnosis_id = diag_l['ds'].id
                        ds_beg_date = diag_l['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())
                        diagnostic_changed = kind_changed = True
                    else:  # 'right' in insp_w_mkb:
                        # ds from next inspection now to start in current inspection
                        diag_r = by_inspection['right'][mkb]
                        diagnosis_id = diag_r['ds'].id
                        ds_beg_date = action_date
                        ds_end_date = diag_r['ds'].endDate
                        diagnostic_changed = kind_changed = True

                    dgn_beg_date = dgn_create_date = action_date
                    self._add_diag_data(diagnosis_id, mkb, new_kind, ds_beg_date, ds_end_date,
                                        dgn_beg_date, dgn_create_date, new_person, diagnostic_changed, kind_changed,
                                        additional_info=additional_info)
                else:
                    # is new mkb, not presented in any of 3 inspections
                    ds_beg_date = dgn_beg_date = dgn_create_date = action_date
                    ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())
                    self._add_diag_data(None, mkb, new_kind, ds_beg_date, ds_end_date,
                                        dgn_beg_date, dgn_create_date, new_person, True, True,
                                        additional_info=additional_info)

        # process existing diags, that were not sent from external source
        ext_mkbs = {mkb for diag_data in mkb_data_list for mkb in diag_data['mkbs']}
        self._delete_remaining(ext_mkbs)

    def refresh_with_old_state(self, mkb_data_list, future_interval):
        """Рассчитать изменения в системе диагнозов на основе старого состояния
        action с еще не измененной датой.

        Этот шаг требуется для обработки случаев, когда осмотр, который ранее являлся причиной
        появления диагноза, а теперь оказывается сменил дату с перескоком через другие осмотры,
        мог либо унести свой диагноз с собой, либо оставить его в соседних осмотрах.
        Этот шаг может быть пропущен, если дата осмотра не изменилась.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        :param fut_interval: DateTimeInterval
        """

        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']

        exist_old_interval = DateTimeInterval(self.source.get_date(), self.source.get_enddate())

        # смещения текущего интервала, не перескакивающие через соседние осмотры
        left_shift = future_interval < exist_old_interval
        right_shift = future_interval > exist_old_interval

        if not left_shift and not right_shift:
            return

        # смещения текущего интервала с перескоком через осмотр
        left_over_shift = adj_inspections['left'] and adj_inspections['left'].begDate > future_interval.beg
        right_over_shift = adj_inspections['right'] and adj_inspections['right'].begDate < future_interval.beg

        for diag_data in mkb_data_list:
            new_kind = diag_data['kind']
            for mkb in diag_data['mkbs']:
                if mkb in by_mkb:
                    # mkb is in at least one of the inspections (previous, current, next)
                    insp_w_mkb = by_mkb[mkb]

                    if 'cur' in insp_w_mkb:
                        # exists in old action
                        diag = by_inspection['cur'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = diag['ds'].endDate
                        dgn_bd = dgn_cd = None
                        diagnostic_changed = False

                        if left_over_shift or right_over_shift:
                            if 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                                if left_over_shift or right_over_shift:
                                    # # nothing changes in ds, diagn will be updated in next step
                                    pass
                            elif 'right' in insp_w_mkb:
                                # ds was in cur and in right - right is the new owner of ds
                                ds_beg_date = adj_inspections['right'].begDate
                            elif 'left' in insp_w_mkb:
                                # ds was in left and in cur - left is the end of ds
                                ds_end_date = self.get_date_before(adj_inspections['right'])
                            else:
                                # delete ds and it will be recreated in next step
                                ds = diag['ds']
                                ds.deleted = 1
                                self.to_delete.append(ds)
                        else:  # left_shift or right_shift:
                            diagnostic_changed = True
                            dgn_bd = dgn_cd = future_interval.beg
                            if 'left' not in insp_w_mkb:
                                ds_beg_date = future_interval.beg
                            if 'right' not in insp_w_mkb:
                                ds_end_date = future_interval.end

                        # delete dgn
                        if diag['diagn']:
                            diag['diagn'].deleted = 1
                            self.to_delete.append(diag['diagn'])

                        self._add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           dgn_bd, dgn_cd, None, diagnostic_changed, False)

        # process existing diags, that were not sent from external source
        ext_mkbs = {mkb for diag_data in mkb_data_list for mkb in diag_data['mkbs']}
        for mkb in by_mkb:
            if mkb not in ext_mkbs:
                insp_w_mkb = by_mkb[mkb]

                # if not shifted, then process in next step
                if 'cur' in insp_w_mkb:
                    diag = by_inspection['cur'][mkb]
                    diag_types = diag['diag_types']
                    if self.diag_type in diag_types:
                        # diag_type_exists
                        diag_kind = diag_types[self.diag_type]
                    elif len(diag_types):
                        # diag_type_not_exists
                        diag_kind = None
                    else:
                        # diag_type_exists
                        diag_kind = 'associated'

                    if diag_kind is None or (diag_kind == 'associated' and self.refresh_in_series):
                        # diag exists in current, but has different from current run diagnosis_type;
                        # don't perform anything in this case
                        continue
                    elif 'left' not in insp_w_mkb and 'right' not in insp_w_mkb:
                        # diag was created only in this inspection and can be deleted
                        ds = by_inspection['cur'][mkb]['ds']
                        ds.deleted = 1
                        self.to_delete.append(ds)
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # diag is in the left and in the right
                        # if its is the same diagnosis, it will be splitted in 2 - left will be shrinked,
                        # right will be created new;
                        # else there are 2 different diagnoses, that will have their dates changed
                        diag_l = by_inspection['left'][mkb]
                        diag_r = by_inspection['right'][mkb]
                        if left_over_shift or right_over_shift:
                            if diag_l['ds'].id == diag_r['ds'].id:
                                # # no changes because without cur inspection ds would be continuous span
                                # from left to right inspection
                                pass
                            else:
                                # left
                                ds_beg_date = diag_l['ds'].setDate
                                ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())
                                self._add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                   None, None, None, False, False)
                                # right
                                ds_beg_date = adj_inspections['right'].begDate
                                ds_end_date = diag_r['ds'].endDate
                                self._add_diag_data(diag_r['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                   None, None, None, False, False)
                        else:  # left_shift or right_shift
                            # left
                            ds_beg_date = diag_l['ds'].setDate
                            ds_end_date = self.get_date_before_interval(future_interval)
                            self._add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                None, None, None, False, False)
                            # right
                            if diag_l['ds'].id == diag_r['ds'].id:
                                ds_beg_date = dgn_beg_date = dgn_create_date = adj_inspections['right'].begDate
                                ds_end_date = diag_r['ds'].endDate
                                person = diag_r['diagn'].person if diag_r['diagn'] else None
                                self._add_diag_data(None, mkb, diag_kind, ds_beg_date, ds_end_date,
                                                    dgn_beg_date, dgn_create_date, person, True, True,
                                                    other_action=adj_inspections['right'])
                            else:
                                ds_beg_date = adj_inspections['right'].begDate
                                ds_end_date = diag_r['ds'].endDate
                                self._add_diag_data(diag_r['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                    None, None, None, False, False)
                    elif 'left' in insp_w_mkb:
                        # close diag from previous inspection
                        diag = by_inspection['left'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'], self.source.get_date())
                        self._add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)
                    elif 'right' in insp_w_mkb:
                        # move in future setDate of next inspection's diag
                        diag = by_inspection['right'][mkb]
                        ds_beg_date = adj_inspections['right'].begDate
                        ds_end_date = diag['ds'].endDate
                        self._add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                            None, None, None, False, False)

                    # delete unneeded dgn from cur
                    diagn = by_inspection['cur'][mkb]['diagn']
                    if diagn:
                        diagn.deleted = 1
                        self.to_delete.append(diagn)

    def refresh_with_deletion(self):
        """Рассчитать изменения в системе диагнозов после удаления осмотра."""
        self.delete_mode = True
        self._delete_remaining([])

    def refresh_with_measure_result(self, mkb_data_list):
        """Рассчитать изменения в системе диагнозов на основе данных сохранения
        результата мероприятия

        В список диагнозов для сохранения передаются диагнозы, поставленные
        непосредственно в результате мероприятия, а также к ним добавляются все диагнозы,
        существующие на дату результата мероприятия - т.е. те, которые относятся
        к предыдущему осмотру.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        """
        mkb_data_list = mkb_data_list[:]
        mr_mkbs = set()
        for d in mkb_data_list:
            for mkb in d['mkbs']:
                mr_mkbs.add(mkb)

        by_inspection = self.existing_diags['by_inspection']
        if 'left' in by_inspection:
            dk_mkb_map = {}
            for mkb, diag in by_inspection['left'].items():
                if mkb not in mr_mkbs:
                    if self.diag_type in diag['diag_types']:
                        dk_mkb_map.setdefault(diag['diag_types'][self.diag_type], set()).add(mkb)
                    else:
                        dk_mkb_map.setdefault('associated', set()).add(mkb)
            for dk_code, mkb_list in dk_mkb_map.items():
                mkb_data_list.append({
                    'kind': dk_code,
                    'mkbs': mkb_list
                })

        self.refresh_with(mkb_data_list)

    def refresh_with_measure_result_old_state(self, mkb_data_list, future_interval):
        """Рассчитать изменения в системе диагнозов на основе старого состояния
        action мероприятия с еще не измененной датой.

        В список диагнозов для сохранения передаются диагнозы, поставленные
        непосредственно в результате мероприятия, а также к ним добавляются все диагнозы,
        существующие на дату результата мероприятия - т.е. те, которые относятся
        к предыдущему осмотру.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        """
        mkb_data_list = mkb_data_list[:]
        mr_mkbs = set()
        for d in mkb_data_list:
            for mkb in d['mkbs']:
                mr_mkbs.add(mkb)

        by_inspection = self.existing_diags['by_inspection']
        if 'left' in by_inspection:
            dk_mkb_map = {}
            for mkb, diag in by_inspection['left'].items():
                if mkb not in mr_mkbs:
                    if self.diag_type in diag['diag_types']:
                        dk_mkb_map.setdefault(diag['diag_types'][self.diag_type], set()).add(mkb)
                    else:
                        dk_mkb_map.setdefault('associated', set()).add(mkb)
            for dk_code, mkb_list in dk_mkb_map.items():
                mkb_data_list.append({
                    'kind': dk_code,
                    'mkbs': mkb_list
                })

        self.refresh_with_old_state(mkb_data_list, future_interval)

    @staticmethod
    def get_date_before(action, max_date=None):
        b_a = action.begDate - datetime.timedelta(seconds=1) if action else None
        if max_date:
            return max(b_a, max_date) if b_a else b_a
        else:
            return b_a

    @staticmethod
    def get_date_before_interval(interval):
        return interval.beg - datetime.timedelta(seconds=1)

    def _delete_remaining(self, mkb_to_stay_list):
        """Рассчитать изменения в системе диагнозов на основе данных удаления
        всех МКБ, относящихся к текущему осмотру, кроме тех, что должны
        остаться - mkb_to_stay_list.

        :param mkb_to_stay_list: list of mkb codes
        """
        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']

        for mkb in by_mkb:
            if mkb not in mkb_to_stay_list:
                insp_w_mkb = by_mkb[mkb]
                # diags in current inspection, that should not be here according to new external data
                if 'cur' in insp_w_mkb:
                    diag = by_inspection['cur'][mkb]
                    diag_types = diag['diag_types']
                    if self.diag_type:
                        if self.diag_type in diag_types:
                            # diag_type_exists
                            diag_kind = diag_types[self.diag_type]
                        elif len(diag_types):
                            # diag_type_not_exists
                            diag_kind = None
                        else:
                            # diag_type_exists
                            diag_kind = 'associated'
                    else:
                        diag_kind = 'associated'

                    if self.diag_type is not None and (diag_kind is None or
                            (diag_kind == 'associated' and self.refresh_in_series)):
                        # diag exists in current, but has different from current run diagnosis_type;
                        # don't perform anything in this case
                        continue
                    elif 'left' not in insp_w_mkb and 'right' not in insp_w_mkb:
                        # diag was created only in this inspection and can be deleted
                        ds = by_inspection['cur'][mkb]['ds']
                        ds.deleted = 1
                        self.to_delete.append(ds)
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # diag is in the left and in the right
                        # if its is the same diagnosis, it will be splitted in 2 - left will be shrinked,
                        # right will be created new;
                        # else there are 2 different diagnoses, that will have their dates changed
                        diag_l = by_inspection['left'][mkb]
                        diag_r = by_inspection['right'][mkb]
                        if diag_l['ds'].id == diag_r['ds'].id:
                            if not self.delete_mode:
                                # left
                                ds_beg_date = diag_l['ds'].setDate
                                ds_end_date = self.get_date_before(adj_inspections['cur'])
                                self._add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                   None, None, None, False, False)
                                # right
                                ds_beg_date = dgn_beg_date = dgn_create_date = adj_inspections['right'].begDate
                                ds_end_date = diag_r['ds'].endDate
                                diag_kind = diag_l['diag_types'][self.diag_type] \
                                    if self.diag_type in diag_l['diag_types'] else diag_kind
                                person = diag_r['diagn'].person if diag_r['diagn'] else None
                                self._add_diag_data(None, mkb, diag_kind, ds_beg_date, ds_end_date,
                                                    dgn_beg_date, dgn_create_date, person, True, True,
                                                    other_action=adj_inspections['right'])
                            else:
                                ds_beg_date = adj_inspections['left'].begDate if diag_l['diagn'] else \
                                    adj_inspections['right'].begDate
                                ds_end_date = diag_l['ds'].endDate
                                self._add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                                    None, None, None, False, False)
                        else:
                            # left
                            ds_beg_date = diag_l['ds'].setDate
                            ds_end_date = self.get_date_before(adj_inspections['cur'])
                            self._add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                            # right
                            ds_beg_date = adj_inspections['right'].begDate
                            ds_end_date = diag_r['ds'].endDate
                            self._add_diag_data(diag_r['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                    elif 'left' in insp_w_mkb:
                        # in previous but now not in current
                        diag = by_inspection['left'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        if not self.delete_mode:
                            ds_end_date = self.get_date_before(adj_inspections['cur'])
                        else:
                            ds_end_date = self.get_date_before(adj_inspections['right'])
                        self._add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)
                    elif 'right' in insp_w_mkb:
                        # move in future setDate of next inspection's diag
                        diag = by_inspection['right'][mkb]
                        ds_beg_date = adj_inspections['right'].begDate
                        ds_end_date = diag['ds'].endDate
                        self._add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)

                    if not self.create_mode:
                        # delete unneeded dgn from cur
                        # dgn can be with higher date, delete just in case
                        diagn = by_inspection['cur'][mkb]['diagn']
                        if diagn:
                            diagn.deleted = 1
                            self.to_delete.append(diagn)
                # else:
                    # diags in 'left' and 'right' should be ok, no edit needed

    def _add_diag_data(self, ds_id, mkb_code, diag_kind, ds_beg_date, ds_end_date,
                      dgn_beg_date, dgn_create_date, person,
                      diagnostic_changed=False, kind_changed=False, other_action=None,
                      additional_info=None):
        diagnosis_types = {
            self.diag_type: {'code': diag_kind}
        }
        data = {
            'id': ds_id,
            'deleted': 0,
            'kind_changed': kind_changed,
            'diagnostic_changed': diagnostic_changed,
            'diagnostic': {
                'mkb': {'code': mkb_code},
                'set_date': dgn_beg_date,
                'create_datetime': dgn_create_date,
                'person': {
                    'id': person.id
                } if person else None,
            },
            'diagnosis_types': diagnosis_types,
            'person': {
                'id': person.id
            } if person else None,
            'set_date': safe_date(ds_beg_date),
            'end_date': ds_end_date,
        }
        if additional_info:
            if 'trauma' in additional_info:
                data['diagnostic']['trauma'] = additional_info['trauma']
            if 'character' in additional_info:
                data['diagnostic']['character'] = additional_info['character']
            if 'mkb2' in additional_info:
                data['diagnostic']['mkb2'] = additional_info['mkb2']
            if 'ache_result' in additional_info:
                data['diagnostic']['ache_result'] = additional_info['ache_result']

        if other_action is None:
            self.to_create.append(data)
        else:
            self.to_create_other_action.append({
                'action': other_action,
                'data': data
            })

    def _get_5_inspections_diagnoses(self):
        left, cur, right = self.ais.left, self.ais.cur, self.ais.right
        inter_left, inter_right = get_adjacent_measure_results(cur)
        if left and inter_left and inter_left.begDate < left.begDate:
            inter_left = None
        if right and inter_right and right.begDate < inter_right.begDate:
            inter_right = None

        beg_date = left.begDate if left else inter_left.begDate if inter_left else cur.begDate
        end_date = right.begDate if right else inter_right.begDate if inter_right else cur.event.execDate

        return get_3_diagnoses(cur.event, beg_date, end_date, left, cur, right, inter_left, inter_right)

