# -*- coding: utf-8 -*-
import logging

from abc import ABCMeta, abstractmethod

from hippocrates.blueprints.risar.lib.stage_factor_risks import factors as risk_factors
from hippocrates.blueprints.risar.lib.stage_factor_risks.utils import get_filtered_regional_risk_factors

from nemesis.lib.utils import safe_dict


logger = logging.getLogger('simple')


class StageFactorRiskScale(object):
    """
    Базовый класс для расчета рисков по шкалам, определяющих
    количественные показатели факторов риска по разным этапам определения
    риска в картах беременных.
    """
    __metaclass__ = ABCMeta

    def __init__(self, card, risk):
        self.card = card
        self.risk = risk

        self._calc_stages = []
        self._clear_stage_ids = set()

    def get_risks_info(self):
        """
        Получить информацию по рискам для карты
        """
        return safe_dict(self.risk)

    def reevaluate(self):
        """
        Пересчитать все параметры, относящиеся к рискам по факторам и стадиям
        """
        self._calc_stages = []
        self._clear_stage_ids = set()

        self._set_calc_stages()
        if not self._calc_stages:
            return

        self._process_risk_sums_and_triggers()

        self._process_risk_rate()

    @abstractmethod
    def _set_calc_stages(self):
        """
        Установить стадии (этапы) определения риска для последующего расчета
        """
        return []

    @abstractmethod
    def _get_current_stages(self):
        """
        Найти актуальные для текущей карты стадии (этапы) определения риска
        """
        pass

    @abstractmethod
    def _process_risk_sums_and_triggers(self):
        """
        Рассчитать и обновить параметры, относящиеся к риску:
        суммы баллов факторов и сработавшие факторы
        """
        pass

    def _calc_stage_factor_points(self, stage):
        """
        Получить расчеты по всем факторам для стадии (суммарное количество
        баллов и сработавшие факторы)
        """
        points_sum = 0
        triggered_factors = []
        rb_slice = self._get_factors_by_stage(stage.code)
        points_modifiers = self._get_factor_points_modifications()
        for factor in rb_slice:
            points = factor['points']
            factor_func = self._get_factor_func(factor['code'])
            if factor_func(self.card):
                if factor['code'] in points_modifiers:
                    points = points_modifiers[factor['code']](points)
                points_sum += points
                triggered_factors.append(factor['id'])
        return points_sum, triggered_factors

    def _get_factor_func(self, code):
        """
        Получить функцию для проверки срабатывания фактора риска
        """
        func = getattr(risk_factors, code, None)
        if not func:
            logger.critical((u'Не найдена функция для проверки фактора риска '
                             u'с кодом `{0}`').format(code))
            raise Exception(u'Ошибка пересчета рисков по шкале рисков')
        return func

    def _get_factor_points_modifications(self):
        """
        Возвращает словарь с кодами факторов, имеющих нестандартную логику
        вычисления баллов. Может быть специфично для региона.
        """
        return {}

    @abstractmethod
    def _get_factors_by_stage(self, stage_code):
        """
        Возвращает список факторов для стадии, которые относятся к
        текущей шкале рисков
        """
        return []

    @abstractmethod
    def _process_risk_rate(self):
        """
        Рассчитать и обновить степень риска
        """
        pass

    @abstractmethod
    def _get_final_sum(self):
        """
        Получить  итоговую сумму баллов для текущей стадии карты
        """
        pass

    @abstractmethod
    def _get_stage_calculated_points(self, stage_code):
        """
        Получить рассчитанное количество баллов на стадии
        """
        pass


class StageFactorRegionalRiskScale(StageFactorRiskScale):
    """
    Шкала рисков, специфичная для региона.
    Использует общие факторы, но региональные группы и стадии.
    """
    def __init__(self, card, risk, risk_rate):
        super(StageFactorRegionalRiskScale, self).__init__(card, risk)
        self.risk_rate = risk_rate

    def _get_factors_by_stage(self, stage_code):
        return get_filtered_regional_risk_factors(stage_code)
