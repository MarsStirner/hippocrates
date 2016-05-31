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

    radz_risk = get_radz_risk(card.event, True)
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
    triggered_codes = set(triggers)
    for cur_factor in cur_factors:
        if cur_factor.risk_factor_code not in triggered_codes:
            db.session.delete(cur_factor)
        else:
            triggered_codes.remove(cur_factor.risk_factor_code)
    for code in triggered_codes:
        trig_factor = RisarRadzinskyRisks_FactorsAssoc(
            radz_risk=radz_risk, risk_factor_code=code
        )
        radz_risk.factors_assoc.append(trig_factor)

    reevaluate_radzinsly_risk_rate(card, radz_risk)


def calc_factor_points(card, factor_stage):
    points_sum = 0
    triggered_factors = []
    rb_slice = get_filtered_risk_factors(factor_stage.code)
    for factor in rb_slice:
        handler, points = get_handler(factor['code'])
        if handler(card):
            points_sum += points
            triggered_factors.append(factor['code'])
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


def get_event_radzinsky_risks_info(event):
    radz_risks = get_radz_risk(event)
    factor_codes = set([assoc.risk_factor_code for assoc in radz_risks.factors_assoc])
    rb_stage_factors = radzinsky_risk_factors()
    for stage_code, groups in rb_stage_factors.iteritems():
        for group_code, factors in groups.iteritems():
            for factor in factors:
                factor['triggered'] = factor['code'] in factor_codes
                factor['points'] = 0
    return {
        'general_info': safe_dict(radz_risks),
        'stage_factors': rb_stage_factors
    }


# @cache.memoize()
def radzinsky_risk_factors():
    query = db.session.query(rbRadzStage).join(
        rbRadzRiskFactor_StageAssoc, rbRadzRiskFactor, rbRadzRiskFactorGroup
    ).options(
        # TODO: worth it?
        joinedload(rbRadzStage.risk_factors).joinedload(rbRadzRiskFactor.group)
    )

    grouped = defaultdict(dict)
    for stage in query:
        for factor in stage.risk_factors:
            grouped[stage.code].setdefault(factor.group.code, []).append(safe_dict(factor))

    return grouped