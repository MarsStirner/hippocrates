# -*- coding: utf-8 -*-

from hippocrates.blueprints.risar.lib.utils import action_as_dict_with_id, action_as_dict, get_apt_from_at
from hippocrates.blueprints.risar.risar_config import nursing


def represent_partal_nursing(action, flatcode):
    dc = action_as_dict_with_id(action, nursing.get(flatcode))
    dc['end_date'] = action.endDate
    dc['flatcode'] = flatcode
    return dc


def represent_partal_nursing_with_anamnesis(action, flatcode, card):
    res = {}
    res['pp_nursing'] = represent_partal_nursing(action, flatcode)
    res['mother_anamnesis'] = {}
    res['father_anamnesis'] = {}
    if card:
        mother = card.anamnesis.mother
        father = card.anamnesis.father
        res['mother_anamnesis'] = action_as_dict(mother, ['marital_status', 'professional_properties'])
        res['father_anamnesis'] = action_as_dict(father, ['name', 'age', 'professional_properties'])
    return res


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


def represent_action_type_for_template(at, fields=None):
    return {
        'flatcode': at.flatCode,
        'properties_list': map(represent_apt, get_apt_from_at(at, fields))
    }


def represent_action_type_for_nursing(at, fields=None):
    return represent_action_type_for_template(at, fields=nursing.get(at.flatCode))
