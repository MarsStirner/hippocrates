# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from sqlalchemy import or_, and_

from hippocrates.blueprints.risar.lib.card import AbstractCard
from nemesis.lib.utils import safe_traverse
from nemesis.models.actions import Action, ActionType
from nemesis.models.diagnosis import rbDiagnosisKind
from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException


logger = logging.getLogger('simple')


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
