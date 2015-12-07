# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from blueprints.accounting.lib.represent import ServiceRepr
from nemesis.lib.utils import safe_int


@module.route('/api/0/service/search/mis_action_kind/', methods=['GET', 'POST'])
@api_method
def api_0_service_search():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    service_ctrl = ServiceController()
    data = service_ctrl.search_mis_action_services(args)
    return ServiceRepr().represent_search_result_mis_action_services(data)


@module.route('/api/0/service/service_list/', methods=['POST'])
@api_method
def api_0_service_list_save():
    json_data = request.get_json()
    event_id = safe_int(json_data.get('event_id'))
    if not event_id:
        raise ApiException(422, u'`event_id` required')
    grouped_service_list = json_data.get('grouped', [])

    service_ctrl = ServiceController()
    service_list = service_ctrl.save_service_list(grouped_service_list, event_id)
    service_ctrl.store(*service_list)

    grouped = service_ctrl.get_grouped_services_by_event(event_id)
    service_repr = ServiceRepr()
    return service_repr.represent_grouped_event_services(grouped)
