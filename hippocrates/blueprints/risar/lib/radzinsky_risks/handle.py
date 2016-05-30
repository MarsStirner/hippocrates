# -*- coding: utf-8 -*-

import logging
import handlers


logger = logging.getLogger('simple')


def get_handler(risk_factor_code):
    handler, points = _handlers_map.get(risk_factor_code, (None, 0))
    if not handler:
        logger.critical((u'Не найдена функция для проверки фактора риска '
                         u'с кодом `{0}` по шкале Радзинского').format(risk_factor_code))
        raise Exception(u'Ошибка пересчета рисков')
    return handler, points


# factor_code: check function, points
_handlers_map = {
    # anamnestic
    'mother_younger_18': (handlers.mother_younger_18, 2),
    'mother_older_40': (handlers.mother_older_40, 4),
    'father_older_40': (handlers.father_older_40, 2)
}