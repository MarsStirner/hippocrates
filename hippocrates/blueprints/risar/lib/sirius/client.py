#! coding:utf-8
"""


@author: BARS Group
@date: 27.10.2016

"""
from flask import url_for
from nemesis.app import app
from .request import request_local, request_remote, \
    request_client_local_id_by_remote_id, request_register_card_idents


def send_to_mis(service_method, obj, params, is_create):
    if not app.config.get('SIRIUS_ENABLED'):
        return
    obj_id, obj_name = obj
    url_params = params.copy()
    url_params.update((obj,))
    data = {
        'service_method': service_method,
        'request_url': url_for(service_method, api_version=0, **url_params),
        'request_method': 'get',
        'request_params': params,
        'main_id': obj_id,
        'main_param_name': obj_name,
        'method': 'post' if is_create else 'put',
    }
    return request_local(data)


def update_entity_from_mis(region, entity, remote_id):
    request = {
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_remote(request)
    code = result['meta']['code']
    return code


def get_risar_id_by_mis_id(region, entity, remote_id):
    request = {
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_client_local_id_by_remote_id(request)
    code = result['meta']['code']
    client_id = result['result']
    return client_id


def save_card_ids_match(local_id, region, entity, remote_id):
    request = {
        "local_main_id": local_id,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_register_card_idents(request)
    code = result['meta']['code']
    return code
