# -*- coding: utf-8 -*-

from hippocrates.blueprints.risar.lib.ultrasonography import get_ultrasonography_edd_latest_em_result
from nemesis.lib.utils import safe_traverse_attrs


def represent_predicted_pregnancy(card):
    tm_data = get_ultrasonography_edd_latest_em_result(card)
    tm_data['pdd_mensis'] = card.attrs['pdd_mensis'].value
    tm_data['predicted_delivery_date'] = card.attrs['predicted_delivery_date'].value
    epic = safe_traverse_attrs(card, 'epicrisis', 'action')
    if epic:
        tm_data['fact_delivery_date'] = epic['delivery_date'].value
    return tm_data
