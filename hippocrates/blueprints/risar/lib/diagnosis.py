# coding: utf-8

import logging

from sqlalchemy.orm import contains_eager
from sqlalchemy import or_, and_, func

from blueprints.risar.risar_config import checkup_flat_codes
from blueprints.risar.lib.datetime_interval import DateTimeInterval, IntersectionType, get_intersection_type

from nemesis.models.diagnosis import Diagnosis, Diagnostic, Action_Diagnosis
from nemesis.models.actions import Action, ActionType
from nemesis.models.expert_protocol import EventMeasure
from nemesis.systemwide import db
from nemesis.lib.utils import safe_datetime, safe_traverse


logger = logging.getLogger('simple')


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


def get_prev_inspection_query(action, flatcodes):
    return db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        ActionType.flatCode.in_(flatcodes),
        or_(Action.begDate < action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id < action.id if action.id else True)
            ),
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1)


def get_next_inspection_query(action, flatcodes):
    return db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        ActionType.flatCode.in_(flatcodes),
        or_(Action.begDate > action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id > action.id if action.id else False)
            ),
        Action.id != action.id
    ).order_by(Action.begDate).limit(1)


def get_adjacent_inspections(action, flatcodes):
    left = get_prev_inspection_query(action, flatcodes).first()
    right = get_next_inspection_query(action, flatcodes).first()
    return left, action, right


def get_adjacent_measure_results(inspection_action):
    left = db.session.query(Action).join(ActionType).join(
        EventMeasure, EventMeasure.resultAction_id == Action.id
    ).filter(
        Action.deleted == 0,
        EventMeasure.event_id == inspection_action.event.id,
        Action.begDate < inspection_action.begDate,
    ).order_by(Action.begDate.desc()).limit(1).first()
    right = db.session.query(Action).join(ActionType).join(
        EventMeasure, EventMeasure.resultAction_id == Action.id
    ).filter(
        Action.deleted == 0,
        EventMeasure.event_id == inspection_action.event.id,
        Action.begDate > inspection_action.begDate,
    ).order_by(Action.begDate).limit(1).first()
    return left, right


def get_5_inspections_diagnoses(action, insp_flatcodes):
    left, cur, right = get_adjacent_inspections(action, insp_flatcodes)
    inter_left, inter_right = get_adjacent_measure_results(action)
    if left and inter_left and inter_left < left:
        inter_left = None
    if right and inter_right and right < inter_right:
        inter_right = None

    beg_date = left.begDate if left else inter_left.begDate if inter_left else cur.begDate
    end_date = right.begDate if right else inter_right.begDate if inter_right else action.event.execDate

    return _get_3_diagnoses(action.event, beg_date, end_date, left, cur, right, inter_left, inter_right)


def _get_3_diagnoses(event, beg_date, end_date, left, cur, right, inter_left, inter_right):
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
    ds_action_map = dict(
        ((a_d.diagnosis_id, a_d.action_id), a_d) for a_d in act_ds_kinds
    )

    # todo: to del first diag?
    first_ds_digns = get_first_diagnostics_of_diagnoses(ds_ids)
    ds_first_diagn_map = dict((diagn.diagnosis_id, diagn) for diagn in first_ds_digns)

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
            diagn = action_diagns[left.id]
            mkb_inspections.setdefault(mkb, set()).add('left')
            if safe_traverse(inspection_diags, 'left', mkb):
                logger.warning(u'Несколько диагнозов с одинаковым МКБ {0} '
                               u'(Diagnosis.id={1}, Diagnostic.id={2})'.format(mkb, ds.id, diagn.id))
            inspection_diags.setdefault('left', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'first_diagn': ds_first_diagn_map[ds_id],
                'ds': ds,
                'a_d': ds_action_map.get((ds.id, left.id))
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
            inspection_diags.setdefault('cur', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'first_diagn': ds_first_diagn_map[ds_id],
                'ds': ds,
                'a_d': ds_action_map.get((ds.id, cur.id))
            })
        if right and IntersectionType.is_intersection(
                get_intersection_type(
                    ds_interval,
                    DateTimeInterval(right.begDate, right.endDate)
                )):
            diagn = action_diagns[right.id]
            mkb_inspections.setdefault(mkb, set()).add('right')
            if safe_traverse(inspection_diags, 'right', mkb):
                logger.warning(u'Несколько диагнозов с одинаковым МКБ {0} '
                               u'(Diagnosis.id={1}, Diagnostic.id={2})'.format(mkb, ds.id, diagn.id))
            inspection_diags.setdefault('right', {}).setdefault(
                mkb, {}
            ).update({
                'diagn': diagn,
                'first_diagn': ds_first_diagn_map[ds_id],
                'ds': ds,
                'a_d': ds_action_map.get((ds.id, right.id))
            })

    return {
        'by_mkb': mkb_inspections,
        'by_inspection': inspection_diags,
        'inspections': inspections
    }
