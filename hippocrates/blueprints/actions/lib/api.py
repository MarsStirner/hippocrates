# -*- coding: utf-8 -*-
from nemesis.lib.utils import transfer_fields

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
        action.setPropValue(k, v.value)


