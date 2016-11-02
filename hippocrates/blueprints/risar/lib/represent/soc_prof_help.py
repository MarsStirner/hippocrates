# -*- coding: utf-8 -*-
from blueprints.risar.lib.utils import action_as_dict_with_id


def represent_soc_prof_item(action, fields=None):
    return action_as_dict_with_id(action, fields)


def represent_soc_prof_help(card):
    return {code + '_list': map(represent_soc_prof_item, action_list)
            for code, action_list in card.soc_prof_help.items()}
