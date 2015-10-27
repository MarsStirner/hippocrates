# -*- coding: utf-8 -*-
from nemesis.lib.agesex import AgeSex
from nemesis.lib.utils import transfer_fields
from nemesis.lib.const import NOT_COPYABLE_VALUE_TYPES

__author__ = 'viruzzz-kun'


def update_template_action(action, src_action):
    transfer_fields(src_action, action, [
        'begDate',
        'endDate',
        'plannedEndDate',
        'directionDate',
        'isUrgent',
        'status',
        'setPerson',
        'person',
        'note',
        'amount',
        'account',
        'uet',
        'payStatus',
        'coordDate',
        'office',
        'actionType'
    ])

    for k, v in src_action.propsByTypeId.iteritems():
        if v.type.typeName not in NOT_COPYABLE_VALUE_TYPES:
            action.setPropValue(k, v.value)


def represent_action_template(template):
    return {
        'id': template.id,
        'gid': template.group_id,
        'name': template.name,
        'aid': template.action_id,
        'con': AgeSex(template)
    }


def is_template_action(action):
    return action.id and not action.event_id
