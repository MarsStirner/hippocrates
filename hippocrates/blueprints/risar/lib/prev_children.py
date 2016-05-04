# coding: utf-8

import itertools

from blueprints.risar.models.risar import RisarPreviousPregnancy_Children
from nemesis.lib.utils import safe_int, safe_bool, safe_double
from nemesis.systemwide import db


def get_previous_children(action_id):
    if not action_id:
        return []
    return db.session.query(RisarPreviousPregnancy_Children).filter(
        RisarPreviousPregnancy_Children.action_id == action_id
    ).order_by(
        RisarPreviousPregnancy_Children.id
    ).all()


def create_or_update_prev_children(action, newborn_inspections_data):
    existing_prev_children = get_previous_children(action.id)
    children = []
    deleted_children = []
    for new_data, exist_child in itertools.izip_longest(newborn_inspections_data, existing_prev_children):
        if not new_data:
            deleted_children.append(exist_child)
            continue
        if not exist_child:
            exist_child = RisarPreviousPregnancy_Children()

        exist_child.action_id = action.id
        exist_child.action = action
        exist_child.weight = safe_double(new_data.get('weight'))
        exist_child.alive = safe_int(safe_bool(new_data.get('alive')))
        exist_child.death_reason = new_data.get('death_reason')
        exist_child.died_at = new_data.get('died_at')
        exist_child.abnormal_development = safe_int(safe_bool(new_data.get('abnormal_development')))
        exist_child.neurological_disorders = safe_int(safe_bool(new_data.get('neurological_disorders')))
        children.append(exist_child)
    return children, deleted_children