# -*- coding: utf-8 -*-
from nemesis.lib.utils import transfer_fields
from nemesis.models.actions import Action

__author__ = 'viruzzz-kun'


def update_template_action(action, action_id):
    src_action = Action.query.get(action_id)
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
        'office'
    ])
    for k, v in src_action.propsByTypeId.iteritems():
        action.setPropValue(k, v.value)


