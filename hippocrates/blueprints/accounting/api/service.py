# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from blueprints.accounting.lib.represent import ServiceRepr
from nemesis.lib.utils import safe_int, format_money


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
    # to enable orm.reconstruct in Service
    service_ctrl.session.close()

    grouped = service_ctrl.get_grouped_services_by_event(event_id)
    service_repr = ServiceRepr()
    return service_repr.represent_grouped_event_services(grouped)


@module.route('/api/0/service/list/grouped/')
@module.route('/api/0/service/list/grouped/<int:event_id>')
@api_method
def api_0_service_list_grouped(event_id=None):
    if not event_id:
        raise ApiException(404, u'`event_id` required')
    service_ctrl = ServiceController()
    grouped = service_ctrl.get_grouped_services_by_event(event_id)
    service_repr = ServiceRepr()
    return service_repr.represent_grouped_event_services(grouped)


@module.route('/api/0/service/calc_sum/', methods=['POST'])
@api_method
def api_0_service_calc_sum():
    # not used
    json_data = request.get_json()
    service_id = safe_int(json_data.get('service_id'))

    service_ctrl = ServiceController()
    if service_id:
        service = service_ctrl.get_service(service_id)
    else:
        service = service_ctrl.get_new_service(json_data)
    new_sum = service_ctrl.calc_service_sum(service, json_data)
    return format_money(new_sum)


@module.route('/api/0/service/', methods=['DELETE'])
@module.route('/api/0/service/<int:service_id>', methods=['DELETE'])
@api_method
def api_0_service_delete(service_id=None):
    if not service_id:
        raise ApiException(404, u'`contract_id` required')
    service_ctrl = ServiceController()
    service = service_ctrl.get_service(service_id)
    service_ctrl.delete_service(service)
    service_ctrl.store(service)
    return True
