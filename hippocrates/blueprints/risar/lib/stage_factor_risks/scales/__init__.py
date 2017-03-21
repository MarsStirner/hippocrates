# coding: utf-8
"""
Реализации разных шкал рисков по факторам и стадиям
"""
from .radzinsky import RadzinksyRiskScale
from .regional_tomsk import TomskRegionalRiskScale
from .regional_saratov import SaratovRegionalRiskScale


__all__ = ['RadzinksyRiskScale', 'TomskRegionalRiskScale', 'SaratovRegionalRiskScale']
