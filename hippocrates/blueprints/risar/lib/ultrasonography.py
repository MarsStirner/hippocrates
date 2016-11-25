# -*- coding: utf-8 -*-
import datetime
import logging

from collections import OrderedDict

logger = logging.getLogger('simple')


def emresult_realization_minus_gestation(em):
    if em:
        ra = em.result_action
        rd = ra.propsByCode['RealizationDate'].value
        ga = ra.propsByCode['gestational_age'].value
        if rd and ga:
            return rd - datetime.timedelta(weeks=ga)


def emresult_attribute(em, attrib):
    if em:
        try:
            return em.result_action.propsByCode[attrib].value
        except KeyError as e:
            pass


def get_latest_ultrasonography_measures(card):
    em_by_code = card.latest_measures_with_result
    return OrderedDict((x, em_by_code.get(x))
                       for x in [u'0028', u'0025', u'0023'])


def get_latest_ultrasonography_values_by_code(card):
    return OrderedDict((code, emresult_realization_minus_gestation(em))
                       for code, em in get_latest_ultrasonography_measures(card).items())


def get_ultrasonography_edd_latest_em_result(card):
    return dict((code, emresult_attribute(em, 'ultrasonography_edd'))
                for code, em in get_latest_ultrasonography_measures(card).items())


def reevaluate_pregnancy_start_date_by_ultrasonography(card):
    """Сначала смотрим:
        есть ли у пациентки в мероприятия случая код 0028, у которого есть действие с результатами;
        иначе код 0025, ...
        иначе код 0023, ...
        """
    for _code, value in get_latest_ultrasonography_values_by_code(card).items():
        if value:
            card.attrs['pregnancy_start_date_by_ultrasonography'].value = value
            break
