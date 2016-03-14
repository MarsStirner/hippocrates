# -*- coding: utf-8 -*-

from flask import request, render_template, abort
from ..app import module
from nemesis.lib.utils import safe_int
from nemesis.lib.action.utils import check_action_service_requirements


__author__ = 'viruzzz-kun'


@module.route('/action.html')
def html_action():
    if 'action_id' not in request.args:
        action_type_id = safe_int(request.args.get('action_type_id'))
        if not action_type_id:
            raise abort(400, '`action_type_id` required')
        price_list_item_id = safe_int(request.args.get('price_list_item_id'))
        service_check = check_action_service_requirements(action_type_id, price_list_item_id)
        if not service_check['result']:
            raise abort(400, service_check['message'])

    return render_template('actions/action.html')