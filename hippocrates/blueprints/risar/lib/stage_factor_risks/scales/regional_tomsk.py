# -*- coding: utf-8 -*-
import logging

from collections import defaultdict
from copy import deepcopy

from hippocrates.blueprints.risar.lib.stage_factor_risks.scales_base import StageFactorRegionalRiskScale
from hippocrates.blueprints.risar.lib.stage_factor_risks.utils import count_abortion_first_trimester,\
    regional_risk_factors

from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.models.radzinsky_risks import (RisarTomskRegionalRisks_FactorsAssoc)
from hippocrates.blueprints.risar.lib.card import PrimaryInspection, RepeatedInspection
from nemesis.lib.utils import safe_dict
from nemesis.models.enums import TomskRegionalRiskStage, TomskRegionalRiskRate
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class TomskRegionalRiskScale(StageFactorRegionalRiskScale):
    """
    Шкала рисков Томской области.
    Строилась на основе шкалы Радзинского и приказа 572. Стадии и алгоритм
    расчета отличаются от эталонной шкалы Радзинского.
    """
    def _set_calc_stages(self):
        stages = self._get_current_stages()
        stage = stages[0] if stages else None
        if stage == TomskRegionalRiskStage.initial[0]:
            self._calc_stages.append(TomskRegionalRiskStage(stage))
            self._clear_stage_ids.add(TomskRegionalRiskStage.before21[0])
            self._clear_stage_ids.add(TomskRegionalRiskStage.from21to30[0])
            self._clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
        elif stage == TomskRegionalRiskStage.before21[0]:
            self._calc_stages.append(TomskRegionalRiskStage(stage))
            self._clear_stage_ids.add(TomskRegionalRiskStage.from21to30[0])
            self._clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
        elif stage == TomskRegionalRiskStage.from21to30[0]:
            self._calc_stages.append(TomskRegionalRiskStage(stage))
            self._clear_stage_ids.add(TomskRegionalRiskStage.from31to36[0])
        elif stage == TomskRegionalRiskStage.from31to36[0]:
            self._calc_stages.append(TomskRegionalRiskStage(stage))
        else:
            logger.warning(u'Невозможно определить этап для расчета регионального риска для карты с id = {0}'
                           .format(self.card.event.id))

    def _get_current_stages(self):
        latest_insp = self.card.latest_inspection
        preg_week = get_pregnancy_week(self.card.event)
        if not latest_insp or isinstance(latest_insp, PrimaryInspection):
            return [TomskRegionalRiskStage.initial[0]]
        elif isinstance(latest_insp, RepeatedInspection):
            if not preg_week or preg_week <= 20:
                return [TomskRegionalRiskStage.before21[0]]
            elif 21 <= preg_week <= 30:
                return [TomskRegionalRiskStage.from21to30[0]]
            elif 31 <= preg_week <= 36 or preg_week > 36:
                return [TomskRegionalRiskStage.from31to36[0]]

    def _process_risk_sums_and_triggers(self):
        initial_sum = before21_sum = from21_to30_sum = from31_to36_sum = None
        triggers = defaultdict(set)
        for stage in self._calc_stages:
            points, triggered_factors = self._calc_stage_factor_points(stage)
            if stage.value == TomskRegionalRiskStage.initial[0]:
                initial_sum = points
            elif stage.value == TomskRegionalRiskStage.before21[0]:
                before21_sum = points
            elif stage.value == TomskRegionalRiskStage.from21to30[0]:
                from21_to30_sum = points
            elif stage.value == TomskRegionalRiskStage.from31to36[0]:
                from31_to36_sum = points
            triggers[stage.value].update(triggered_factors)

        # суммы баллов по этапам либо устанавливаются заново рассчитанные,
        # либо обнуляются, если этап перестал быть актуальным
        if initial_sum is not None:
            self.risk.initial_points = initial_sum
        if before21_sum is not None or TomskRegionalRiskStage.before21[0] in self._clear_stage_ids:
            self.risk.before21week_points = before21_sum
        if from21_to30_sum is not None or TomskRegionalRiskStage.from21to30[0] in self._clear_stage_ids:
            self.risk.from21to30week_points = from21_to30_sum
        if from31_to36_sum is not None or TomskRegionalRiskStage.from31to36[0] in self._clear_stage_ids:
            self.risk.from31to36week_points = from31_to36_sum

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
                trig_factor = RisarTomskRegionalRisks_FactorsAssoc(
                    risk=self.risk, risk_factor_id=factor_id, stage_id=stage_id
                )
                self.risk.factors_assoc.append(trig_factor)

    def _get_factor_points_modifications(self):
        res = {
            'abortion_first_trimester': lambda points: count_abortion_first_trimester(self.card) * points
        }
        return res

    def _process_risk_rate(self):
        final_sum = self._get_final_sum()
        risk_rate = None
        if 0 <= final_sum < 10:
            risk_rate = TomskRegionalRiskRate.low[0]
        elif 10 <= final_sum <= 14:
            risk_rate = TomskRegionalRiskRate.medium[0]
        elif 15 <= final_sum:
            risk_rate = TomskRegionalRiskRate.high[0]
        self.risk_rate.risk_rate_id = risk_rate

    def _get_final_sum(self):
        stages = self._get_current_stages()
        final_sum = 0
        if TomskRegionalRiskStage.initial[0] in stages:
            final_sum = self.risk.initial_points
        elif TomskRegionalRiskStage.before21[0] in stages:
            final_sum = self.risk.before21week_points
        elif TomskRegionalRiskStage.from21to30[0] in stages:
            final_sum = self.risk.from21to30week_points
        elif TomskRegionalRiskStage.from31to36[0] in stages:
            final_sum = self.risk.from31to36week_points
        return final_sum

    def _get_stage_calculated_points(self, stage_code):
        stage_id = TomskRegionalRiskStage.getId(stage_code)
        if stage_id == TomskRegionalRiskStage.initial[0]:
            return self.risk.initial_points or 0
        elif stage_id == TomskRegionalRiskStage.before21[0]:
            return self.risk.before21week_points or 0
        elif stage_id == TomskRegionalRiskStage.from21to30[0]:
            return self.risk.from21to30week_points or 0
        elif stage_id == TomskRegionalRiskStage.from31to36[0]:
            return self.risk.from31to36week_points or 0

    def get_risks_info(self):
        event_factor_stages = {(assoc.risk_factor_id, assoc.stage_id) for assoc in self.risk.factors_assoc}
        rb_stage_factors = deepcopy(regional_risk_factors())
        stage_points = {}
        points_modifiers = self._get_factor_points_modifications()
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

        general_info = safe_dict(self.risk)
        general_info.update({
            'risk_rate_id': self.risk_rate.risk_rate_id,
            'risk_rate': self.risk_rate.risk_rate
        })
        max_points = 0
        total_sum_points = 0
        for stage_code, stage_info in stage_points.items():
            max_points += stage_info['maximum']
            stage_sum_calc = self._get_stage_calculated_points(stage_code)
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
