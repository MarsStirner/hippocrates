# -*- coding: utf-8 -*-
import logging

from collections import defaultdict
from copy import deepcopy

from hippocrates.blueprints.risar.lib.stage_factor_risks.scales_base import StageFactorRegionalRiskScale
from hippocrates.blueprints.risar.lib.stage_factor_risks.utils import regional_risk_factors

from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.models.radzinsky_risks import (RisarSaratovRegionalRisks_FactorsAssoc)
from nemesis.lib.utils import safe_dict
from nemesis.models.enums import SaratovRegionalRiskStage, SaratovRegionalRiskRate
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class SaratovRegionalRiskScale(StageFactorRegionalRiskScale):
    """
    Шкала рисков Саратовской области.
    Практически полностью соответствует шкале Радзинского. Вносятся небольшие
    изменения по факторам и стадиям.
    """
    def _set_calc_stages(self):
        stages = self._get_current_stages()
        if SaratovRegionalRiskStage.anamnestic[0] in stages:
            self._calc_stages.append(SaratovRegionalRiskStage(SaratovRegionalRiskStage.anamnestic[0]))
        if SaratovRegionalRiskStage.before35[0] in stages:
            self._calc_stages.append(SaratovRegionalRiskStage(SaratovRegionalRiskStage.before35[0]))
            self._clear_stage_ids.add(SaratovRegionalRiskStage.after36[0])
        elif SaratovRegionalRiskStage.after36[0] in stages:
            self._calc_stages.append(SaratovRegionalRiskStage(SaratovRegionalRiskStage.after36[0]))
        if SaratovRegionalRiskStage.intranatal[0] in stages:
            self._calc_stages.append(SaratovRegionalRiskStage(SaratovRegionalRiskStage.intranatal[0]))
        else:
            self._clear_stage_ids.add(SaratovRegionalRiskStage.intranatal[0])

    def _get_current_stages(self):
        res = [SaratovRegionalRiskStage.anamnestic[0]]
        preg_week = get_pregnancy_week(self.card.event)
        if preg_week <= 35:
            res.append(SaratovRegionalRiskStage.before35[0])
        elif preg_week >= 36:
            res.append(SaratovRegionalRiskStage.after36[0])
        if self.card.epicrisis.action.id:
            res.append(SaratovRegionalRiskStage.intranatal[0])
        return res

    def _process_risk_sums_and_triggers(self):
        anamnestic_sum = before35week_sum = after36week_sum = intranatal_sum = before35week_totalsum = \
            after36week_totalsum = intranatal_totalsum = intranatal_growth = None
        triggers = defaultdict(set)
        for stage in self._calc_stages:
            points, triggered_factors = self._calc_stage_factor_points(stage)
            if stage.value == SaratovRegionalRiskStage.anamnestic[0]:
                anamnestic_sum = points
            elif stage.value == SaratovRegionalRiskStage.before35[0]:
                before35week_sum = points
            elif stage.value == SaratovRegionalRiskStage.after36[0]:
                after36week_sum = points
            elif stage.value == SaratovRegionalRiskStage.intranatal[0]:
                intranatal_sum = points
            triggers[stage.value].update(triggered_factors)

        if before35week_sum is not None:
            before35week_totalsum = anamnestic_sum + before35week_sum
        if after36week_sum is not None:
            after36week_totalsum = anamnestic_sum + after36week_sum
        if intranatal_sum is not None and (after36week_sum is not None or before35week_sum is not None):
            stage_sum = after36week_totalsum if after36week_sum is not None else before35week_totalsum
            intranatal_totalsum = intranatal_sum + stage_sum
            intranatal_growth = round(float(intranatal_sum) / stage_sum * 100, 2) if stage_sum else 0

        # анамнестические пересчитываются всегда
        self.risk.anamnestic_points = anamnestic_sum
        # факторы до 35 пересчитываются до 36 недели беременности, также меняется общая сумма до 35
        if before35week_sum is not None:
            self.risk.before35week_points = before35week_sum
            self.risk.before35week_totalpoints = before35week_totalsum
        else:
            # а еще общая сумма может пересчитываться и после 35 недели,
            # если изменились анамнестические факторы
            self.risk.before35week_totalpoints = anamnestic_sum + (self.risk.before35week_points or 0)
        # факторы после 36 пересчитываются с 36 недели беременности, также меняется общая сумма после 36;
        # кроме того эти суммы очищаются, если неделя беременности до 36
        if after36week_sum is not None or SaratovRegionalRiskStage.after36[0] in self._clear_stage_ids:
            self.risk.after36week_points = after36week_sum
            self.risk.after36week_totalpoints = after36week_totalsum
        # интранатальные пересчитываются при наличии эпикриза, также меняется общая сумма интранатальных
        # и прирост; кроме того эти суммы очищаются, если эпикриза нет
        if intranatal_sum is not None and intranatal_growth is not None or \
                SaratovRegionalRiskStage.intranatal[0] in self._clear_stage_ids:
            self.risk.intranatal_points = intranatal_sum
            self.risk.intranatal_totalpoints = intranatal_totalsum
            self.risk.intranatal_growth = intranatal_growth

        cur_factors = self.risk.factors_assoc
        for cur_factor in cur_factors:
            stage_id = cur_factor.stage_id
            if stage_id in self._clear_stage_ids:
                db.session.delete(cur_factor)
            elif stage_id in triggers:
                if cur_factor.risk_factor_id in triggers[stage_id]:
                    triggers[cur_factor.stage_id].remove(cur_factor.risk_factor_id)
                else:
                    db.session.delete(cur_factor)
        for stage_id, factor_list in triggers.iteritems():
            for factor_id in factor_list:
                trig_factor = RisarSaratovRegionalRisks_FactorsAssoc(
                    risk=self.risk, risk_factor_id=factor_id, stage_id=stage_id
                )
                self.risk.factors_assoc.append(trig_factor)

    def _process_risk_rate(self):
        final_sum = self._get_final_sum()
        risk_rate = None
        if 0 <= final_sum <= 10:
            risk_rate = SaratovRegionalRiskRate.low[0]
        elif 11 <= final_sum <= 15:
            risk_rate = SaratovRegionalRiskRate.medium[0]
        elif 16 <= final_sum:
            risk_rate = SaratovRegionalRiskRate.high[0]
        self.risk.risk_rate_id = risk_rate

    def _get_final_sum(self):
        stages = self._get_current_stages()
        final_sum = 0
        if SaratovRegionalRiskStage.intranatal[0] in stages:
            final_sum = self.risk.intranatal_totalpoints or 0
        elif SaratovRegionalRiskStage.before35[0] in stages:
            final_sum = self.risk.before35week_totalpoints or 0
        elif SaratovRegionalRiskStage.after36[0] in stages:
            final_sum = self.risk.after36week_totalpoints or 0
        return final_sum

    def _get_stage_calculated_points(self, stage_code):
        stage_id = SaratovRegionalRiskStage.getId(stage_code)
        if stage_id == SaratovRegionalRiskStage.anamnestic[0]:
            return self.risk.anamnestic_points or 0
        elif stage_id == SaratovRegionalRiskStage.before35[0]:
            return self.risk.before35week_points or 0
        elif stage_id == SaratovRegionalRiskStage.after36[0]:
            return self.risk.after36week_points or 0
        elif stage_id == SaratovRegionalRiskStage.intranatal[0]:
            return self.risk.intranatal_points or 0

    def get_risks_info(self):
        event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in self.risk.factors_assoc}
        rb_stage_factors = deepcopy(regional_risk_factors())
        stage_points = {}
        for stage_code, groups in rb_stage_factors.iteritems():
            stage_sum = stage_maximum = 0
            for group_code, factors in groups.iteritems():
                for factor in factors:
                    k = (factor['id'], SaratovRegionalRiskStage.getId(stage_code))
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

        general_info = safe_dict(self.risk)
        max_points = 0
        total_sum_points = 0
        for stage_code, stage_info in stage_points.items():
            max_points += stage_info['maximum']
            stage_sum_rb = stage_info['sum']
            stage_sum_calc = self._get_stage_calculated_points(stage_code)
            if stage_sum_calc != stage_sum_rb:
                logger.warning((u'В карте {0} рассчитанное значение суммы баллов по стадии {1} '
                                u'отличается от справочного'.format(self.risk.event_id, stage_code)))
            stage_info['sum'] = stage_sum_calc
            total_sum_points += stage_sum_calc
        general_info['maximum_points'] = max_points
        general_info['total_sum_points'] = total_sum_points
        general_info['final_sum_points'] = self._get_final_sum()
        return {
            'general_info': general_info,
            'stage_factors': rb_stage_factors,
            'stage_points': stage_points
        }
