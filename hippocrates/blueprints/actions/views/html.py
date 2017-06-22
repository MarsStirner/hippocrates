# -*- coding: utf-8 -*-

from flask import request, render_template
from nemesis.lib.html_utils import UIException
from ..app import module
from nemesis.lib.utils import safe_int, bail_out
from nemesis.lib.action.utils import check_action_service_requirements
from nemesis.models.client import Client


__author__ = 'viruzzz-kun'


@module.route('/action.html')
def html_action():
    if 'action_id' not in request.args:
        action_type_id = safe_int(request.args.get('action_type_id')) \
                         or bail_out(UIException(400, u'Необходимо указать id типа действия`action_type_id`'))
        safe_int(request.args.get('event_id')) \
            or bail_out(UIException(400, u'Необходимо указать id обращения `event_id`'))
        price_list_item_id = safe_int(request.args.get('price_list_item_id'))
        service_check = check_action_service_requirements(action_type_id, price_list_item_id)
        if not service_check['result']:
            raise UIException(
                400,
                u'Ошибка настроек услуг и прайс-листов: %s' % service_check['message'],
                u'Ошибка настроек услуг и прайс-листов'
            )

    return render_template('actions/action.html')


@module.route('/actions.html')
def html_search_actions():
    return render_template('actions/actions.html')


@module.route('/actions_with_values_modal/<int:client_id>')
def actions_with_values_modal(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('actions/modal_actions_with_values.html', client=client)
