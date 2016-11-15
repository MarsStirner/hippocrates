# -*- coding: utf-8 -*-

from blueprints.risar.lib.utils import action_as_dict_with_id
from blueprints.risar.risar_config import nursing
from nemesis.models.actions import ActionPropertyType


def represent_partal_nursing(action, flatcode):
    dc = action_as_dict_with_id(action, nursing.get(flatcode))
    dc['end_date'] = action.endDate
    dc['flatcode'] = flatcode
    return dc


def represent_partal_nursing_list(card, flatcode):
    return map(lambda x: represent_partal_nursing(action=x, flatcode=flatcode),
               card.get_action_list(flatcode))


def represent_apt(apt):
    return {
        'code': apt.code,
        'name': apt.name,
        'valueDomain': apt.valueDomain,
        'typeName': apt.typeName,
        'isVector': apt.isVector,
    }


def represent_action_type_for_template(at):
    return {
        'flatcode': at.flatCode,
        'properties_list': map(represent_apt,
                               at.property_types.filter(
                                   ActionPropertyType.deleted == 0
                               ).order_by(
                                   ActionPropertyType.idx
                               ))
    }
