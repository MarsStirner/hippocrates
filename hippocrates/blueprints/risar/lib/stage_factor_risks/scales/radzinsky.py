# -*- coding: utf-8 -*-
import logging

from collections import defaultdict
from copy import deepcopy

from hippocrates.blueprints.risar.lib.stage_factor_risks.scales_base import StageFactorRiskScale
from hippocrates.blueprints.risar.lib.stage_factor_risks.utils import get_filtered_radzinsky_risk_factors,\
    radzinsky_risk_factors

from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.models.radzinsky_risks import RisarRadzinskyRisks_FactorsAssoc
from nemesis.lib.utils import safe_dict
from nemesis.models.enums import RadzinskyStage, RadzinskyRiskRate
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class RadzinksyRiskScale(StageFactorRiskScale):
    """
    Шкала рисков Радзинского.
    Является эталонной реализацией, на которую обычно опираются региональные шкалы.
    """
    def _set_calc_stages(self):
        stages = self._get_current_stages()
        if RadzinskyStage.anamnestic[0] in stages:
            self._calc_stages.append(RadzinskyStage(RadzinskyStage.anamnestic[0]))
        if RadzinskyStage.before32[0] in stages:
            self._calc_stages.append(RadzinskyStage(RadzinskyStage.before32[0]))
            self._clear_stage_ids.add(RadzinskyStage.after33[0])
        elif RadzinskyStage.after33[0] in stages:
            self._calc_stages.append(RadzinskyStage(RadzinskyStage.after33[0]))
        if RadzinskyStage.intranatal[0] in stages:
            self._calc_stages.append(RadzinskyStage(RadzinskyStage.intranatal[0]))
        else:
            self._clear_stage_ids.add(RadzinskyStage.intranatal[0])

    def _get_current_stages(self):
        res = [RadzinskyStage.anamnestic[0]]
        preg_week = get_pregnancy_week(self.card.event)
        if preg_week <= 32:
            res.append(RadzinskyStage.before32[0])
        elif preg_week >= 33:
            res.append(RadzinskyStage.after33[0])
        if self.card.epicrisis.action.id:
            res.append(RadzinskyStage.intranatal[0])
        return res

    def _process_risk_sums_and_triggers(self):
        anamnestic_sum = before32week_sum = after33week_sum = intranatal_sum = before32week_totalsum = \
            after33week_totalsum = intranatal_totalsum = intranatal_growth = None
        triggers = defaultdict(set)
        for stage in self._calc_stages:
            points, triggered_factors = self._calc_stage_factor_points(stage)
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

        # анамнестические пересчитываются всегда
        self.risk.anamnestic_points = anamnestic_sum
        # факторы до 32 пересчитываются до 33 недели беременности, также меняется общая сумма до 32
        if before32week_sum is not None:
            self.risk.before32week_points = before32week_sum
            self.risk.before32week_totalpoints = before32week_totalsum
        else:
            # а еще общая сумма может пересчитываться и после 32 недели,
            # если изменились анамнестические факторы
            self.risk.before32week_totalpoints = anamnestic_sum + (self.risk.before32week_points or 0)
        # факторы после 33 пересчитываются с 33 недели беременности, также меняется общая сумма после 33;
        # кроме того эти суммы очищаются, если неделя беременности до 33
        if after33week_sum is not None or RadzinskyStage.after33[0] in self._clear_stage_ids:
            self.risk.after33week_points = after33week_sum
            self.risk.after33week_totalpoints = after33week_totalsum
        # интранатальные пересчитываются при наличии эпикриза, также меняется общая сумма интранатальных
        # и прирост; кроме того эти суммы очищаются, если эпикриза нет
        if intranatal_sum is not None and intranatal_growth is not None or \
                RadzinskyStage.intranatal[0] in self._clear_stage_ids:
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
                trig_factor = RisarRadzinskyRisks_FactorsAssoc(
                    radz_risk=self.risk, risk_factor_id=factor_id, stage_id=stage_id
                )
                self.risk.factors_assoc.append(trig_factor)

    def _get_factors_by_stage(self, stage_code):
        return get_filtered_radzinsky_risk_factors(stage_code)

    def _process_risk_rate(self):
        final_sum = self._get_final_sum()
        risk_rate = None
        if 0 <= final_sum <= 14:
            risk_rate = RadzinskyRiskRate.low[0]
        elif 15 <= final_sum <= 24:
            risk_rate = RadzinskyRiskRate.medium[0]
        elif 25 <= final_sum:
            risk_rate = RadzinskyRiskRate.high[0]
        self.risk.risk_rate_id = risk_rate

    def _get_final_sum(self):
        stages = self._get_current_stages()
        final_sum = 0
        if RadzinskyStage.intranatal[0] in stages:
            final_sum = self.risk.intranatal_totalpoints or 0
        elif RadzinskyStage.before32[0] in stages:
            final_sum = self.risk.before32week_totalpoints or 0
        elif RadzinskyStage.after33[0] in stages:
            final_sum = self.risk.after33week_totalpoints or 0
        return final_sum

    def _get_stage_calculated_points(self, stage_code):
        stage_id = RadzinskyStage.getId(stage_code)
        if stage_id == RadzinskyStage.anamnestic[0]:
            return self.risk.anamnestic_points or 0
        elif stage_id == RadzinskyStage.before32[0]:
            return self.risk.before32week_points or 0
        elif stage_id == RadzinskyStage.after33[0]:
            return self.risk.after33week_points or 0
        elif stage_id == RadzinskyStage.intranatal[0]:
            return self.risk.intranatal_points or 0

    def get_risks_info(self):
        event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in self.risk.factors_assoc}
        rb_stage_factors = deepcopy(radzinsky_risk_factors())
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
