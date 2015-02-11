# -*- coding: utf-8 -*-
import os

# Определяем название модуля по имени директории
MODULE_NAME = os.path.basename(os.path.dirname(__file__))

# Русское название модуля для отображения в главном меню
RUS_NAME = u'Отчёты'


LPU_DB_HOST = '10.1.2.11:3306'
LPU_DB_USER = 'tmis'
LPU_DB_PASSWORD = 'q1w2e3r4t5'
LPU_DB_NAME = 'hospital1'

try:
    from .config_local import *
except ImportError:
    # no local config found
    pass

LPU_DB_CONNECT_STRING = 'mysql://{0}:{1}@{2}/{3}?charset=utf8'.format(
    LPU_DB_USER, LPU_DB_PASSWORD, LPU_DB_HOST, LPU_DB_NAME)