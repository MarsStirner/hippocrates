# coding: utf-8

import logging

from sqlalchemy.orm import contains_eager
from sqlalchemy import or_, and_, func

from blueprints.risar.risar_config import checkup_flat_codes
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.datetime_interval import DateTimeInterval, IntersectionType, get_intersection_type

from nemesis.models.diagnosis import Diagnosis, Diagnostic, Action_Diagnosis
from nemesis.models.actions import Action, ActionType
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
    ds_diagn_dates = db.session.query(func.min(Diagnostic.setDate).label('min_date')).filter(
        Diagnostic.deleted == 0,
        Diagnostic.diagnosis_id.in_(ds_ids)
    ).group_by(Diagnostic.client_id).subquery('DiagnosisLowestDiagnosticDates')
    ds_diagn_ids = db.session.query(func.min(Diagnostic.id).label('min_id')).join(
        ds_diagn_dates, Diagnostic.setDate == ds_diagn_dates.c.min_date
    ).filter(
        Diagnostic.deleted == 0,
        Diagnostic.diagnosis_id.in_(ds_ids)
    ).group_by(Diagnostic.client_id).subquery('DiagnosisLowestDiagnosticIds')
    query = db.session.query(Diagnostic).join(
        ds_diagn_ids, Diagnostic.id == ds_diagn_ids.c.min_id
    )
    return query.all()


def get_adjacent_inspections(action):
    left = db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event.id,
        ActionType.flatCode.in_(checkup_flat_codes),
        or_(Action.begDate < action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id < action.id if action.id else True)
            ),
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1).first()
    right = db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event.id,
        ActionType.flatCode.in_(checkup_flat_codes),
        or_(Action.begDate > action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id > action.id if action.id else False)
            ),
        Action.id != action.id
    ).order_by(Action.begDate).limit(1).first()
    return left, action, right


def get_3_inspections_diagnoses(action):
    left, cur, right = get_adjacent_inspections(action)

    beg_date = left.begDate if left else cur.begDate
    end_date = right.begDate if right else cur.begDate
    diagns = get_diagnostics_history(action.event, beg_date, end_date)
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
    act_ds_query = db.session.query(Action_Diagnosis).filter(
        Action_Diagnosis.deleted == 0,
        Action_Diagnosis.action_id.in_(action_ids),
        Action_Diagnosis.diagnosis_id.in_(ds_ids)
    ).order_by(Action_Diagnosis.id)
    ds_action_map = dict(
        ((a_d.diagnosis_id, a_d.action_id), a_d) for a_d in act_ds_query
    )

    first_ds_digns = get_first_diagnostics_of_diagnoses(ds_ids)
    ds_first_diagn_map = dict((diagn.diagnosis_id, diagn) for diagn in first_ds_digns)

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
        'inspections': {
            'left': left,
            'cur': cur,
            'right': right
        }
    }
