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
    'father_older_40': (handlers.father_older_40, 2),
    'mother_professional_properties': (handlers.mother_professional_properties, 3),
    'father_professional_properties': (handlers.father_professional_properties, 3),
    'mother_smoking': (handlers.mother_smoking, 2),
    'mother_alcohol': (handlers.mother_alcohol, 4),
    'father_alcohol': (handlers.father_alcohol, 2),
    'emotional_stress': (handlers.emotional_stress, 1),
    'height_less_150': (handlers.height_less_150, 2),
    'overweight': (handlers.overweight, 2),
    'not_married': (handlers.not_married, 1),
}