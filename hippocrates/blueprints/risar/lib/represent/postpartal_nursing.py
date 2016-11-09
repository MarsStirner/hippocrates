# -*- coding: utf-8 -*-

from blueprints.risar.lib.utils import action_as_dict_with_id
from blueprints.risar.risar_config import postpartal_nursing


def represent_postpartal_nursing(action):
    dc = action_as_dict_with_id(action, postpartal_nursing)
    dc['end_date'] = action.endDate
    return dc


def represent_postpartal_nursing_list(card):
    return map(represent_postpartal_nursing, card.postpartal_nursing)

