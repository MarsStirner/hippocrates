# -*- coding: utf-8 -*-
import os

# Определяем название модуля по имени директории
MODULE_NAME = os.path.basename(os.path.dirname(__file__))

# Русское название модуля для отображения в главном меню
RUS_NAME = u'Подсистема печати'


LPU_DB_HOST = '192.168.1.100:3306'
LPU_DB_USER = 'tmis'
LPU_DB_PASSWORD = 'q1w2e3r4t5'
LPU_DB_NAME = 'pnz_det_filatova_ntk'

try:
    from .config_local import *
except ImportError:
    # no local config found
    pass

LPU_DB_CONNECT_STRING = 'mysql://{}:{}@{}/{}?charset=utf8'.format(
    LPU_DB_USER, LPU_DB_PASSWORD, LPU_DB_HOST, LPU_DB_NAME)

KLADR_DB_CONNECT_STRING = 'mysql://{}:{}@{}/{}?charset=utf8'.format(
    LPU_DB_USER, LPU_DB_PASSWORD, LPU_DB_HOST, 'kladr')