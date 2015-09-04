# -*- coding: utf-8 -*-
from flask import request
from ..app import module
from nemesis.lib.apiutils import api_method
from nemesis.lib.subscriptions import subscribe_user
from nemesis.lib.subscriptions import unsubscribe_user
from nemesis.models.useraccount import UserSubscriptions
from nemesis.models.utils import safe_current_user_id

__author__ = 'viruzzz-kun'


@module.route('/api/subscription/', methods=['PUT', 'DELETE', 'GET'])
@module.route('/api/subscription/<object_id>', methods=['PUT', 'DELETE', 'GET'])
@api_method
def api_subscription(object_id):
    person_id = safe_current_user_id()
    if request.method == 'PUT':
        subscribe_user(person_id, object_id)
        return True
    elif request.method == 'DELETE':
        unsubscribe_user(person_id, object_id)
        return False
    else:
        return object_id in UserSubscriptions.list_subscriptions(person_id)


