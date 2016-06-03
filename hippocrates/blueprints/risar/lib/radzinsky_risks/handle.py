# -*- coding: utf-8 -*-

import logging
import handlers


logger = logging.getLogger('simple')


def get_handler(risk_factor_code):
    handler = getattr(handlers, risk_factor_code, None)
    if not handler:
        logger.critical((u'Не найдена функция для проверки фактора риска '
                         u'по шкале Радзинского с кодом `{0}`').format(risk_factor_code))
        raise Exception(u'Ошибка пересчета рисков по шкале Радзинского')
    return handler
