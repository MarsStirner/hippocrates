# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from hippocrates.blueprints.accounting.lib.represent import ServiceRepr
from nemesis.lib.utils import safe_int, format_money, safe_bool, parse_json


@module.route('/api/0/service/search/mis_action_kind/', methods=['GET', 'POST'])
@api_method
def api_0_service_search():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    service_ctrl = ServiceController()
    data = service_ctrl.search_mis_action_services(args)
    return ServiceRepr().represent_search_result_mis_action_services(data)


@module.route('/api/0/service/')
@module.route('/api/0/service/<int:service_id>')
@api_method
def api_0_service_get(service_id=None):
    args = request.args.to_dict()
    if 'serviced_entity_from_search' in args:
        args['serviced_entity_from_search'] = parse_json(args['serviced_entity_from_search'])
    if request.json:
        args.update(request.json)
    get_new = safe_bool(args.get('new', False))

    service_ctrl = ServiceController()
    with service_ctrl.session.no_autoflush:
        if get_new:
            service = service_ctrl.get_new_service(args)
        elif service_id:
            service = service_ctrl.get_service(service_id)
        else:
            raise ApiException(404, u'`service_id` required')
        return ServiceRepr().represent_service_full(service)


@module.route('/api/0/service/list/')
@module.route('/api/0/service/list/<int:event_id>')
@api_method
def api_0_service_list(event_id=None):
    if not event_id:
        raise ApiException(404, u'`event_id` required')
    service_ctrl = ServiceController()
    service_list = service_ctrl.get_services_by_event(event_id)
    service_repr = ServiceRepr()
    return service_repr.represent_listed_event_services(service_list)


@module.route('/api/0/service/service_list/', methods=['POST'])
@api_method
def api_0_service_list_save():
    json_data = request.get_json()
    event_id = safe_int(json_data.get('event_id'))
    if not event_id:
        raise ApiException(422, u'`event_id` required')
    service_list = json_data.get('service_list', [])

    service_ctrl = ServiceController()
    service_list = service_ctrl.save_service_list(service_list)
    service_ctrl.store(*service_list)
    # to launch orm.reconstruct in Service
    service_ctrl.session.close()

    service_list = service_ctrl.get_services_by_event(event_id)
    service_repr = ServiceRepr()
    return service_repr.represent_listed_event_services(service_list)


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


@module.route('/api/0/service/refresh_subservices/', methods=['POST'])
@api_method
def api_0_service_refresh_subservices():
    json_data = request.get_json()

    service_ctrl = ServiceController()
    with service_ctrl.session.no_autoflush:
        service = service_ctrl.refresh_service_subservices(json_data)
        return ServiceRepr().represent_service_full(service)


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


@module.route('/api/0/service/at_price/')
@module.route('/api/0/service/at_price/<int:contract_id>')
@api_method
def api_0_service_at_price_get(contract_id=None):
    if not contract_id:
        raise ApiException(404, '`contract_id` required')
    args = request.args.to_dict()

    service_ctrl = ServiceController()
    args.update({
        'contract_id': contract_id,
        # sphinx limits to 100 by default;
        # this also assumes that server sphinx conf has increased max_matches param
        'limit_max': 10000
    })
    at_service_data = service_ctrl.get_service_data_for_at_tree(args)

    return ServiceRepr().represent_services_by_at(at_service_data)
