# -*- coding: utf-8 -*-
import datetime
import logging

from collections import defaultdict
from sqlalchemy.orm import joinedload

from blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from blueprints.risar.models.radzinsky_risks import (RisarRadzinskyRisks, RisarRadzinskyRisks_FactorsAssoc)
from nemesis.lib.utils import safe_dict, safe_date
from nemesis.models.enums import RadzinskyStage, RadzinskyRiskRate
from nemesis.models.risar import (rbRadzRiskFactor, rbRadzStage, rbRadzRiskFactor_StageAssoc,
    rbRadzRiskFactorGroup)
from nemesis.systemwide import db, cache
from .handle import get_handler


logger = logging.getLogger('simple')


def get_radz_risk(event, create=False):
    radz_risk = db.session.query(RisarRadzinskyRisks).filter(
        RisarRadzinskyRisks.event_id == event.id
    ).first()
    if radz_risk is None and create:
        radz_risk = RisarRadzinskyRisks(event=event, event_id=event.id)
        db.session.add(radz_risk)
    return radz_risk


def get_radz_risk_rate(radz_risk):
    return RadzinskyRiskRate(radz_risk.risk_rate_id) if radz_risk.risk_rate_id else None


def reevaluate_radzinsly_risk_rate(card, radz_risk):
    final_sum = 0
    risk_rate = None
    preg_week = get_pregnancy_week(card.event)
    if card.epicrisis:
        final_sum = radz_risk.intranatal_totalpoints or 0
    elif preg_week <= 32:
        final_sum = radz_risk.before32week_totalpoints or 0
    elif preg_week >= 32:
        final_sum = radz_risk.after33week_totalpoints or 0

    if 0 <= final_sum <= 14:
        risk_rate = RadzinskyRiskRate.low[0]
    elif 15 <= final_sum <= 24:
        risk_rate = RadzinskyRiskRate.medium[0]
    elif 25 <= final_sum:
        risk_rate = RadzinskyRiskRate.high[0]
    radz_risk.risk_rate_id = risk_rate


def reevaluate_radzinsky_risks(card):
    stages = [RadzinskyStage(RadzinskyStage.anamnestic[0]), ]
    preg_week = get_pregnancy_week(card.event)
    if preg_week <= 32:
        stages.append(RadzinskyStage(RadzinskyStage.before32[0]))
    elif preg_week >= 32:
        stages.append(RadzinskyStage(RadzinskyStage.after33[0]))
    if card.epicrisis:
        stages.append(RadzinskyStage(RadzinskyStage.intranatal[0]))

    anamnestic_sum = before32week_sum = after33week_sum = intranatal_sum = before32week_totalsum = \
        after33week_totalsum = intranatal_totalsum = intranatal_growth = None
    triggers = []
    for stage in stages:
        points, triggered_factors = calc_factor_points(card, stage)
        if stage.value == RadzinskyStage.anamnestic[0]:
            anamnestic_sum = points
        elif stage.value == RadzinskyStage.before32[0]:
            before32week_sum = points
        elif stage.value == RadzinskyStage.after33[0]:
            after33week_sum = points
        elif stage.value == RadzinskyStage.intranatal[0]:
            intranatal_sum = points
        triggers.extend(triggered_factors)

    if before32week_sum is not None:
        before32week_totalsum = anamnestic_sum + before32week_sum
    if after33week_sum is not None:
        after33week_totalsum = anamnestic_sum + after33week_sum
    if intranatal_sum is not None and after33week_sum is not None:
        intranatal_totalsum = intranatal_sum + after33week_sum
        intranatal_growth = float(intranatal_sum) / after33week_sum * 100

    radz_risk = card.radz_risk
    radz_risk.anamnestic_points = anamnestic_sum
    if before32week_sum is not None:
        radz_risk.before32week_points = before32week_sum
        radz_risk.before32week_totalpoints = before32week_totalsum
    if after33week_sum is not None:
        radz_risk.after33week_points = after33week_sum
        radz_risk.after33week_totalpoints = after33week_totalsum
    if intranatal_sum is not None and after33week_sum is not None:
        radz_risk.intranatal_points = intranatal_sum
        radz_risk.intranatal_totalpoints = intranatal_totalsum
        radz_risk.intranatal_growth = intranatal_growth

    # TODO: check
    cur_factors = radz_risk.factors_assoc
    triggers = set(triggers)
    for cur_factor in cur_factors:
        k = (cur_factor.risk_factor_id, cur_factor.stage_id)
        if k not in triggers:
            db.session.delete(cur_factor)
        else:
            triggers.remove(k)
    for factor_id, stage_id in triggers:
        trig_factor = RisarRadzinskyRisks_FactorsAssoc(
            radz_risk=radz_risk, risk_factor_id=factor_id, stage_id=stage_id
        )
        radz_risk.factors_assoc.append(trig_factor)

    reevaluate_radzinsly_risk_rate(card, radz_risk)


def calc_factor_points(card, factor_stage):
    points_sum = 0
    triggered_factors = []
    rb_slice = get_filtered_risk_factors(factor_stage.code)
    for factor in rb_slice:
        points = factor['points']
        handler = get_handler(factor['code'])
        if handler(card):
            points_sum += points
            triggered_factors.append((factor['id'], factor_stage.value))
    return points_sum, triggered_factors


def get_filtered_risk_factors(stage_codes=None, group_codes=None):
    if stage_codes is not None and not isinstance(stage_codes, (tuple, list)):
        stage_codes = (stage_codes, )
    if group_codes is not None and not isinstance(group_codes, (tuple, list)):
        group_codes = (group_codes, )

    rb = radzinsky_risk_factors()

    filtered = []
    for stage_code, group in rb.iteritems():
        if stage_codes is not None and stage_code in stage_codes or stage_codes is None:
            for group_code, factors in group.iteritems():
                if group_codes is not None and group_code in group_codes or group_codes is None:
                    filtered.extend(factors)
    return filtered


def get_event_radzinsky_risks_info(radz_risk):
    event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in radz_risk.factors_assoc}
    rb_stage_factors = radzinsky_risk_factors()
    stage_points = {}
    stage_sum = stage_maximum = 0
    for stage_code, groups in rb_stage_factors.iteritems():
        for group_code, factors in groups.iteritems():
            for factor in factors:
                k = (factor['id'], RadzinskyStage.getId(stage_code))
                if k in event_factor_stages:
                    factor['triggered'] = True
                    stage_sum += factor['points']
                else:
                    factor['triggered'] = False
                stage_maximum += factor['points']
        stage_points[stage_code] = {
            'maximum': stage_maximum,
            'sum': stage_sum
        }

    general_info = safe_dict(radz_risk)
    max_points = 0
    total_sum_points = 0
    for stage_code, stage_info in stage_points.items():
        max_points += stage_info['maximum']
        stage_sum_rb = stage_info['sum']
        stage_sum_calc = _get_stage_calculated_points(radz_risk, stage_code)
        if stage_sum_calc != stage_sum_rb:
            logger.warning((u'В карте {0} рассчитанное значение суммы баллов по стадии {1} '
                            u'отличается от справочного'.format(radz_risk.event_id, stage_code)))
        stage_info['sum'] = stage_sum_calc
        total_sum_points += stage_sum_calc
    general_info['maximum_points'] = max_points
    general_info['total_sum_points'] = total_sum_points
    return {
        'general_info': general_info,
        'stage_factors': rb_stage_factors,
        'stage_points': stage_points
    }


def _get_stage_calculated_points(radz_risk, stage_code):
    stage_id = RadzinskyStage.getId(stage_code)
    if stage_id == RadzinskyStage.anamnestic[0]:
        return radz_risk.anamnestic_points
    elif stage_id == RadzinskyStage.before32[0]:
        return radz_risk.before32week_points
    elif stage_id == RadzinskyStage.after33[0]:
        return radz_risk.after33week_points
    elif stage_id == RadzinskyStage.intranatal[0]:
        return radz_risk.intranatal_points


# @cache.memoize()
def radzinsky_risk_factors():
    query = db.session.query(rbRadzStage).join(
        rbRadzRiskFactor_StageAssoc, rbRadzRiskFactor, rbRadzRiskFactorGroup
    ).options(
        # TODO: worth it?
        joinedload(rbRadzStage.stage_factor_assoc).
        joinedload(rbRadzRiskFactor_StageAssoc.factor).
        joinedload(rbRadzRiskFactor.group)
    )

    grouped = defaultdict(dict)
    for stage in query:
        for factor_stage in stage.stage_factor_assoc:
            factor_info = safe_dict(factor_stage.factor)
            factor_info.update(points=factor_stage.points)
            grouped[stage.code].setdefault(
                factor_stage.factor.group.code, []
            ).append(factor_info)

    return grouped