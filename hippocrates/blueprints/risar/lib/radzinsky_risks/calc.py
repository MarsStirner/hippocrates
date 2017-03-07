# -*- coding: utf-8 -*-
import datetime
import logging

from collections import defaultdict
from sqlalchemy.orm import contains_eager

from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.models.radzinsky_risks import (RisarRadzinskyRisks, RisarRadzinskyRisks_FactorsAssoc)
from hippocrates.blueprints.risar.lib.chart import get_latest_pregnancy_event
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from nemesis.lib.utils import safe_dict, safe_date
from nemesis.models.enums import RadzinskyStage, RadzinskyRiskRate
from nemesis.models.risar import (rbRadzRiskFactor, rbRadzStage, rbRadzRiskFactor_StageAssoc,
    rbRadzRiskFactorGroup)
from nemesis.systemwide import db, cache
from nemesis.signals import patient_saved
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
    final_sum = _get_final_sum(card, radz_risk)
    risk_rate = None

    if 0 <= final_sum <= 14:
        risk_rate = RadzinskyRiskRate.low[0]
    elif 15 <= final_sum <= 24:
        risk_rate = RadzinskyRiskRate.medium[0]
    elif 25 <= final_sum:
        risk_rate = RadzinskyRiskRate.high[0]
    radz_risk.risk_rate_id = risk_rate


def reevaluate_radzinsky_risks(card):
    calc_stages = [RadzinskyStage(RadzinskyStage.anamnestic[0]), ]
    clear_stage_ids = set()
    preg_week = get_pregnancy_week(card.event)
    if preg_week <= 32:
        calc_stages.append(RadzinskyStage(RadzinskyStage.before32[0]))
        clear_stage_ids.add(RadzinskyStage.after33[0])
    elif preg_week >= 33:
        calc_stages.append(RadzinskyStage(RadzinskyStage.after33[0]))
    if card.epicrisis.action.id:
        calc_stages.append(RadzinskyStage(RadzinskyStage.intranatal[0]))
    else:
        clear_stage_ids.add(RadzinskyStage.intranatal[0])

    anamnestic_sum = before32week_sum = after33week_sum = intranatal_sum = before32week_totalsum = \
        after33week_totalsum = intranatal_totalsum = intranatal_growth = None
    triggers = defaultdict(set)
    for stage in calc_stages:
        points, triggered_factors = calc_factor_points(card, stage)
        if stage.value == RadzinskyStage.anamnestic[0]:
            anamnestic_sum = points
        elif stage.value == RadzinskyStage.before32[0]:
            before32week_sum = points
        elif stage.value == RadzinskyStage.after33[0]:
            after33week_sum = points
        elif stage.value == RadzinskyStage.intranatal[0]:
            intranatal_sum = points
        triggers[stage.value].update(triggered_factors)

    if before32week_sum is not None:
        before32week_totalsum = anamnestic_sum + before32week_sum
    if after33week_sum is not None:
        after33week_totalsum = anamnestic_sum + after33week_sum
    if intranatal_sum is not None and (after33week_sum is not None or before32week_sum is not None):
        stage_sum = after33week_totalsum if after33week_sum is not None else before32week_totalsum
        intranatal_totalsum = intranatal_sum + stage_sum
        intranatal_growth = round(float(intranatal_sum) / stage_sum * 100, 2) if stage_sum else 0

    radz_risk = card.radz_risk
    # анамнестические пересчитываются всегда
    radz_risk.anamnestic_points = anamnestic_sum
    # факторы до 32 пересчитываются до 33 недели беременности, также меняется общая сумма до 32
    if before32week_sum is not None:
        radz_risk.before32week_points = before32week_sum
        radz_risk.before32week_totalpoints = before32week_totalsum
    else:
        # а еще общая сумма может пересчитываться и после 32 недели,
        # если изменились анамнестические факторы
        radz_risk.before32week_totalpoints = anamnestic_sum + (radz_risk.before32week_points or 0)
    # факторы после 33 пересчитываются с 33 недели беременности, также меняется общая сумма после 33;
    # кроме того эти суммы очищаются, если неделя беременности до 33
    if after33week_sum is not None or RadzinskyStage.after33[0] in clear_stage_ids:
        radz_risk.after33week_points = after33week_sum
        radz_risk.after33week_totalpoints = after33week_totalsum
    # интранатальные пересчитываются при наличии эпикриза, также меняется общая сумма интранатальных
    # и прирост; кроме того эти суммы очищаются, если эпикриза нет
    if intranatal_sum is not None and intranatal_growth is not None or \
            RadzinskyStage.intranatal[0] in clear_stage_ids:
        radz_risk.intranatal_points = intranatal_sum
        radz_risk.intranatal_totalpoints = intranatal_totalsum
        radz_risk.intranatal_growth = intranatal_growth

    cur_factors = radz_risk.factors_assoc
    for cur_factor in cur_factors:
        stage_id = cur_factor.stage_id
        if stage_id in clear_stage_ids:
            db.session.delete(cur_factor)
        elif stage_id in triggers:
            if cur_factor.risk_factor_id in triggers[stage_id]:
                triggers[cur_factor.stage_id].remove(cur_factor.risk_factor_id)
            else:
                db.session.delete(cur_factor)
    for stage_id, factor_list in triggers.iteritems():
        for factor_id in factor_list:
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
            triggered_factors.append(factor['id'])
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


def get_event_radzinsky_risks_info(card):
    radz_risk = card.radz_risk
    event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in radz_risk.factors_assoc}
    rb_stage_factors = radzinsky_risk_factors()
    stage_points = {}
    for stage_code, groups in rb_stage_factors.iteritems():
        stage_sum = stage_maximum = 0
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
    general_info['final_sum_points'] = _get_final_sum(card, radz_risk)
    return {
        'general_info': general_info,
        'stage_factors': rb_stage_factors,
        'stage_points': stage_points
    }


def _get_final_sum(card, radz_risk):
    final_sum = 0
    preg_week = get_pregnancy_week(card.event)
    if card.epicrisis.action.id:
        final_sum = radz_risk.intranatal_totalpoints or 0
    elif preg_week <= 32:
        final_sum = radz_risk.before32week_totalpoints or 0
    elif preg_week >= 33:
        final_sum = radz_risk.after33week_totalpoints or 0
    return final_sum


def _get_stage_calculated_points(radz_risk, stage_code):
    stage_id = RadzinskyStage.getId(stage_code)
    if stage_id == RadzinskyStage.anamnestic[0]:
        return radz_risk.anamnestic_points or 0
    elif stage_id == RadzinskyStage.before32[0]:
        return radz_risk.before32week_points or 0
    elif stage_id == RadzinskyStage.after33[0]:
        return radz_risk.after33week_points or 0
    elif stage_id == RadzinskyStage.intranatal[0]:
        return radz_risk.intranatal_points or 0


@cache.memoize()
def radzinsky_risk_factors():
    query = db.session.query(rbRadzStage).join(
        rbRadzRiskFactor_StageAssoc, rbRadzRiskFactor
    ).join(
        rbRadzRiskFactorGroup, rbRadzRiskFactorGroup.id == rbRadzRiskFactor.group_id
    ).options(
        contains_eager(rbRadzStage.stage_factor_assoc).
        contains_eager(rbRadzRiskFactor_StageAssoc.factor).
        contains_eager(rbRadzRiskFactor.group)
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


def on_patient_info_saved(sender, client_id, **extra):
    event = get_latest_pregnancy_event(client_id)
    if event:
        card = PregnancyCard.get_for_event(event)
        if card.attrs:
            reevaluate_radzinsky_risks(card)
            db.session.commit()


patient_saved.connect(on_patient_info_saved)
