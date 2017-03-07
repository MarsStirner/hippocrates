# -*- coding: utf-8 -*-
import datetime
import logging

from collections import defaultdict
from sqlalchemy.orm import contains_eager

from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.models.radzinsky_risks import (RisarTomskRegionalRisks,
    RisarTomskRegionalRisks_FactorsAssoc, RisarRegionalRiskRate)
from hippocrates.blueprints.risar.lib.chart import get_latest_pregnancy_event
from hippocrates.blueprints.risar.lib.card import PregnancyCard, PrimaryInspection, RepeatedInspection
from hippocrates.blueprints.risar.lib.specific import SpecificsManager
from nemesis.lib.utils import safe_dict, safe_date
from nemesis.models.enums import TomskRegionalRiskStage, TomskRegionalRiskRate
from nemesis.models.risar import (rbRadzRiskFactor, rbRegionalRiskStage, rbRadzRiskFactor_RegionalStageAssoc,
    rbRadzRiskFactorGroup)
from nemesis.systemwide import db, cache
from nemesis.signals import patient_saved
from .handle import get_handler


logger = logging.getLogger('simple')


def reevaluate_regional_risks(card):
    if SpecificsManager.is_region_tomsk():
        reevaluate_tomsk_regional_risks(card)


def get_regional_risk_rate(event, create=False):
    risk = db.session.query(RisarRegionalRiskRate).filter(
        RisarRegionalRiskRate.event_id == event.id
    ).first()
    if risk is None and create:
        risk = RisarRegionalRiskRate(event=event, event_id=event.id)
        db.session.add(risk)
    return risk


def get_current_region_risk_rate(regional_risk_rate):
    if not regional_risk_rate:
        return None
    if SpecificsManager.is_region_tomsk():
        return TomskRegionalRiskRate(regional_risk_rate.risk_rate_id) if regional_risk_rate.risk_rate_id else None


def get_regional_risk(event, create=False):
    if SpecificsManager.is_region_tomsk():
        return get_tomsk_regional_risk(event, create)


def get_tomsk_regional_risk(event, create=False):
    risk = db.session.query(RisarTomskRegionalRisks).filter(
        RisarTomskRegionalRisks.event_id == event.id
    ).first()
    if risk is None and create:
        risk = RisarTomskRegionalRisks(event=event, event_id=event.id)
        db.session.add(risk)
    return risk


def reevaluate_tomsk_regional_risk_rate(card, regional_risk, regional_risk_rate):
    final_sum = _get_final_sum(card, regional_risk)
    risk_rate = None

    if 0 <= final_sum < 10:
        risk_rate = TomskRegionalRiskRate.low[0]
    elif 10 <= final_sum <= 140:
        risk_rate = TomskRegionalRiskRate.medium[0]
    elif 15 <= final_sum:
        risk_rate = TomskRegionalRiskRate.high[0]
    regional_risk_rate.risk_rate_id = risk_rate


def reevaluate_tomsk_regional_risks(card):
    calc_stages = []
    clear_stage_ids = set()

    stage = get_tomsk_card_stage(card)
    if stage == TomskRegionalRiskStage.initial[0]:
        calc_stages.append(TomskRegionalRiskStage(stage))
        clear_stage_ids.add(TomskRegionalRiskStage.before21[0])
        clear_stage_ids.add(TomskRegionalRiskStage.from21to30[0])
        clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
    elif stage == TomskRegionalRiskStage.before21[0]:
        calc_stages.append(TomskRegionalRiskStage(stage))
        clear_stage_ids.add(TomskRegionalRiskStage.from21to30[0])
        clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
    elif stage == TomskRegionalRiskStage.from21to30[0]:
        calc_stages.append(TomskRegionalRiskStage(stage))
        clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
    elif stage == TomskRegionalRiskStage.from31to36[0]:
        calc_stages.append(TomskRegionalRiskStage(stage))
    else:
        logger.warning(u'Невозможно определить этап для расчета регионального риска для карты с id = {0}'
                       .format(card.event.id))
        return

    initial_sum = before21_sum = from21_to30_sum = from31_to36_sum = None
    triggers = defaultdict(set)
    for stage in calc_stages:
        points, triggered_factors = calc_regional_factor_points(card, stage)
        if stage.value == TomskRegionalRiskStage.initial[0]:
            initial_sum = points
        elif stage.value == TomskRegionalRiskStage.before21[0]:
            before21_sum = points
        elif stage.value == TomskRegionalRiskStage.from21to30[0]:
            from21_to30_sum = points
        elif stage.value == TomskRegionalRiskStage.from31to36[0]:
            from31_to36_sum = points
        triggers[stage.value].update(triggered_factors)

    regional_risk = card.regional_risk
    # суммы баллов по этапам либо устанавливаются заново рассчитанные,
    # либо обнуляются, если этап перестал быть актуальным
    if initial_sum is not None:
        regional_risk.initial_points = initial_sum
    if before21_sum is not None or TomskRegionalRiskStage.before21[0] in clear_stage_ids:
        regional_risk.before21week_points = before21_sum
    if from21_to30_sum is not None or TomskRegionalRiskStage.from21to30[0] in clear_stage_ids:
        regional_risk.from21to30week_points = from21_to30_sum
    if from31_to36_sum is not None or TomskRegionalRiskStage.from31to36[0] in clear_stage_ids:
        regional_risk.from31to36week_points = from31_to36_sum

    cur_factors = regional_risk.factors_assoc
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
            trig_factor = RisarTomskRegionalRisks_FactorsAssoc(
                risk=regional_risk, risk_factor_id=factor_id, stage_id=stage_id
            )
            regional_risk.factors_assoc.append(trig_factor)

    reevaluate_tomsk_regional_risk_rate(card, regional_risk, card.regional_risk_rate)


def get_tomsk_card_stage(card):
    latest_insp = card.latest_inspection
    preg_week = get_pregnancy_week(card.event)
    if not latest_insp or isinstance(latest_insp, PrimaryInspection):
        return TomskRegionalRiskStage.initial[0]
    elif isinstance(latest_insp, RepeatedInspection):
        if not preg_week or preg_week <= 20:
            return TomskRegionalRiskStage.before21[0]
        elif 21 <= preg_week <= 30:
            return TomskRegionalRiskStage.from21to30[0]
        elif 31 <= preg_week <= 36 or preg_week > 36:
            return TomskRegionalRiskStage.from31to36[0]


def get_regional_factor_points_modifications(card):
    res = {}
    if SpecificsManager.is_region_tomsk():
        from hippocrates.blueprints.risar.lib.radzinsky_risks.utils import count_abortion_first_trimester
        res['abortion_first_trimester'] = lambda points: count_abortion_first_trimester(card) * points
    return res


def calc_regional_factor_points(card, factor_stage):
    points_sum = 0
    triggered_factors = []
    rb_slice = get_filtered_regional_risk_factors(factor_stage.code)
    points_modifiers = get_regional_factor_points_modifications(card)
    for factor in rb_slice:
        points = factor['points']
        handler = get_handler(factor['code'])
        if handler(card):
            if factor['code'] in points_modifiers:
                points = points_modifiers[factor['code']](points)
            points_sum += points
            triggered_factors.append(factor['id'])
    return points_sum, triggered_factors


def get_filtered_regional_risk_factors(stage_codes=None, group_codes=None):
    if stage_codes is not None and not isinstance(stage_codes, (tuple, list)):
        stage_codes = (stage_codes, )
    if group_codes is not None and not isinstance(group_codes, (tuple, list)):
        group_codes = (group_codes, )

    rb = regional_risk_factors()

    filtered = []
    for stage_code, group in rb.iteritems():
        if stage_codes is not None and stage_code in stage_codes or stage_codes is None:
            for group_code, factors in group.iteritems():
                if group_codes is not None and group_code in group_codes or group_codes is None:
                    filtered.extend(factors)
    return filtered


def get_event_regional_risks_info(card):
    if SpecificsManager.is_region_tomsk():
        return get_event_tomsk_regional_risks_info(card)


def get_event_tomsk_regional_risks_info(card):
    regional_risk = card.regional_risk
    event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in regional_risk.factors_assoc}
    rb_stage_factors = regional_risk_factors()
    stage_points = {}
    points_modifiers = get_regional_factor_points_modifications(card)
    for stage_code, groups in rb_stage_factors.iteritems():
        stage_sum = stage_maximum = 0
        for group_code, factors in groups.iteritems():
            for factor in factors:
                k = (factor['id'], TomskRegionalRiskStage.getId(stage_code))
                points = factor['points']
                if factor['code'] in points_modifiers:
                    points = points_modifiers[factor['code']](points)
                    factor['modified_points'] = points
                if k in event_factor_stages:
                    factor['triggered'] = True
                    stage_sum += points
                else:
                    factor['triggered'] = False
                stage_maximum += points
        stage_points[stage_code] = {
            'maximum': stage_maximum,
            'sum': stage_sum
        }

    regional_risk_rate = card.regional_risk_rate

    general_info = safe_dict(regional_risk)
    general_info.update({
        'risk_rate_id': regional_risk_rate.risk_rate_id,
        'risk_rate': regional_risk_rate.risk_rate
    })
    max_points = 0
    total_sum_points = 0
    for stage_code, stage_info in stage_points.items():
        max_points += stage_info['maximum']
        stage_sum_calc = _get_stage_calculated_points(regional_risk, stage_code)
        stage_info['sum'] = stage_sum_calc
        total_sum_points += stage_sum_calc
    general_info['maximum_points'] = max_points
    general_info['total_sum_points'] = total_sum_points
    general_info['final_sum_points'] = _get_final_sum(card, regional_risk)
    return {
        'general_info': general_info,
        'stage_factors': rb_stage_factors,
        'stage_points': stage_points
    }


def _get_final_sum(card, regional_risk):
    final_sum = 0
    stage = get_tomsk_card_stage(card)
    if stage == TomskRegionalRiskStage.initial[0]:
        final_sum = regional_risk.initial_points
    elif stage == TomskRegionalRiskStage.before21[0]:
        final_sum = regional_risk.before21week_points
    elif stage == TomskRegionalRiskStage.from21to30[0]:
        final_sum = regional_risk.from21to30week_points
    elif stage == TomskRegionalRiskStage.from31to36[0]:
        final_sum = regional_risk.from31to36week_points
    return final_sum


def _get_stage_calculated_points(regional_risk, stage_code):
    stage_id = TomskRegionalRiskStage.getId(stage_code)
    if stage_id == TomskRegionalRiskStage.initial[0]:
        return regional_risk.initial_points or 0
    elif stage_id == TomskRegionalRiskStage.before21[0]:
        return regional_risk.before21week_points or 0
    elif stage_id == TomskRegionalRiskStage.from21to30[0]:
        return regional_risk.from21to30week_points or 0
    elif stage_id == TomskRegionalRiskStage.from31to36[0]:
        return regional_risk.from31to36week_points or 0


@cache.memoize()
def regional_risk_factors():
    query = db.session.query(rbRegionalRiskStage).join(
        rbRadzRiskFactor_RegionalStageAssoc, rbRadzRiskFactor
    ).join(
        rbRadzRiskFactorGroup, rbRadzRiskFactor.regional_group_id == rbRadzRiskFactorGroup.id
    ).options(
        contains_eager(rbRegionalRiskStage.stage_factor_assoc).
        contains_eager(rbRadzRiskFactor_RegionalStageAssoc.factor).
        contains_eager(rbRadzRiskFactor.regional_group)
    )

    grouped = defaultdict(dict)
    for stage in query:
        for factor_stage in stage.stage_factor_assoc:
            factor_info = safe_dict(factor_stage.factor)
            factor_info.update(points=factor_stage.points)
            if factor_stage.factor.regional_group:
                grouped[stage.code].setdefault(
                    factor_stage.factor.regional_group.code, []
                ).append(factor_info)

    return grouped


def on_patient_info_saved(sender, client_id, **extra):
    event = get_latest_pregnancy_event(client_id)
    if event:
        card = PregnancyCard.get_for_event(event)
        if card.attrs:
            reevaluate_regional_risks(card)
            db.session.commit()


patient_saved.connect(on_patient_info_saved)
