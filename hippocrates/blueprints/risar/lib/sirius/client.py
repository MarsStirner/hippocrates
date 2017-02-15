#! coding:utf-8
"""


@author: BARS Group
@date: 27.10.2016

"""
from hashlib import md5
from uuid import uuid1

from flask import url_for
from nemesis.app import app
from .request import request_local, request_remote, \
    request_client_local_id_by_remote_id, request_register_card_idents, \
    send_event_remote, request_events_map
import logging

logger = logging.getLogger('simple')

events_binds_map = None


def binded_event(event_code, entity_code):
    global events_binds_map
    if not events_binds_map:
        result = request_events_map()
        code = result['meta']['code']
        if code != 200:
            raise Exception('Sirius binded event request error')
        events_binds_map = result['result']
    event_res = event_code in events_binds_map
    entity_res = not events_binds_map[event_code] or entity_code in events_binds_map[event_code]
    return event_res and entity_res


def get_stream_id():
    return 'stream_' + md5(uuid1().get_hex()).hexdigest()[:10]


def send_to_mis(event_code, entity_code, operation_code,
                service_method, obj, params, is_create):
    if not app.config.get('SIRIUS_ENABLED'):
        return
    if not binded_event(event_code, entity_code):
        return
    stream_id = get_stream_id()
    logger.debug('%s send_to_mis %s %s' % (stream_id, event_code, entity_code))
    obj_name, obj_id = obj
    url_params = params.copy()
    url_params.update((obj,))
    data = {
        'event': event_code,
        'entity_code': entity_code,
        'operation_code': operation_code,
        'service_method': service_method,
        'request_url': url_for(service_method, api_version=0, **url_params),
        'request_method': 'get',
        'request_params': params,
        'main_id': obj_id,
        'main_param_name': obj_name,
        'method': 'post' if is_create else 'put',
        'stream_id': stream_id,
    }
    return request_local(data)


def update_entity_from_mis(region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not app.config.get('SIRIUS_ENABLED'):
        return True
    if not binded_event(event_code, entity):
        return
    stream_id = get_stream_id()
    request = {
        'event': event_code,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
        'stream_id': stream_id,
    }
    result = request_remote(request)
    code = result['meta']['code']
    return code


def check_mis_schedule_ticket(
    client_id, ticket_id, is_delete, person,
    date, beg_time, end_time, schedule_id, curr_person
):
    from hippocrates.blueprints.risar.lib.sirius import OperationCode, \
        RisarEntityCode
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    # нет информации по методу мис
    event_code = RisarEvents.MAKE_APPOINTMENT
    entity_code = RisarEntityCode.SCHEDULE_TICKET
    if not app.config.get('SIRIUS_ENABLED'):
        return True
    if not binded_event(event_code, entity_code):
        return True
    stream_id = get_stream_id()
    data = {
        'event': event_code,
        'entity_code': entity_code,
        'operation_code': OperationCode.DELETE if is_delete else OperationCode.CHANGE,
        'method': 'post',
        "request_params": {
            'doctor': person.regionalCode,
            'patient': client_id,
        },
        "main_id": ticket_id,
        "main_param_name": 'schedule_ticket_id',
        "data": {
            "schedule_ticket_id": ticket_id,
            "schedule_id": schedule_id,
            "schedule_ticket_type": '0' if beg_time else '1',
            "date": date.isoformat(),
            "time_begin": beg_time and beg_time.isoformat()[:5],
            "time_end": end_time and end_time.isoformat()[:5],
            "current_person": curr_person.regionalCode,
        },
        'stream_id': stream_id,
    }
    result = send_event_remote(data)
    code = result['meta']['code']
    reject = result['meta'].get('reject')
    return code == 200 and reject != 1


def get_risar_id_by_mis_id(region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not binded_event(event_code, entity):
        return
    stream_id = get_stream_id()
    request = {
        'event': event_code,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
        'stream_id': stream_id,
    }
    result = request_client_local_id_by_remote_id(request)
    code = result['meta']['code']
    client_id = result['result']
    return client_id


def save_card_ids_match(local_id, region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not binded_event(event_code, entity):
        return
    stream_id = get_stream_id()
    request = {
        'event': event_code,
        "local_main_id": local_id,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
        'stream_id': stream_id,
    }
    result = request_register_card_idents(request)
    code = result['meta']['code']
    return code
