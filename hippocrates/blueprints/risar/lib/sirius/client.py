#! coding:utf-8
"""


@author: BARS Group
@date: 27.10.2016

"""
from flask import url_for
from nemesis.app import app
from .request import request_local, request_remote, \
    request_client_local_id_by_remote_id, request_register_card_idents, \
    send_event_remote, request_events_map
import logging

logger = logging.getLogger('simple')

events_list = None


def binded_event(event_code):
    global events_list
    if not events_list:
        result = request_events_map()
        code = result['meta']['code']
        if code != 200:
            raise Exception('Sirius binded event request error')
        events_list = set(result['result'])
    return event_code in events_list


def send_to_mis(event_code, entity_code, operation_code,
                service_method, obj, params, is_create):
    logger.debug('send_to_mis %s' % event_code)
    if not app.config.get('SIRIUS_ENABLED'):
        return
    if not binded_event(event_code):
        return
    logger.debug('send_to_mis passed %s' % event_code)
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
    }
    return request_local(data)


def update_entity_from_mis(region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not app.config.get('SIRIUS_ENABLED'):
        return True
    if not binded_event(event_code):
        return
    request = {
        'event': event_code,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_remote(request)
    code = result['meta']['code']
    return code


def check_mis_schedule_ticket(client_id, ticket_id, is_delete, org, person,
                              date, beg_time, end_time, schedule_id):
    from hippocrates.blueprints.risar.lib.sirius import OperationCode, \
        RisarEntityCode
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    # нет информации по методу мис
    event_code = RisarEvents.MAKE_APPOINTMENT
    if not app.config.get('SIRIUS_ENABLED'):
        return True
    if not binded_event(event_code):
        return True
    data = {
        'event': event_code,
        'entity_code': RisarEntityCode.SCHEDULE_TICKET,
        'operation_code': OperationCode.CHANGE,
        'method': 'delete' if is_delete else 'post',
        # "service_method": 'api_schedule_tickets_get',
        "request_params": {
            # 'hospital': org.regionalCode,
            'doctor': person.regionalCode,
            'patient': client_id,
        },
        "main_id": ticket_id,
        "main_param_name": 'schedule_ticket_id',
        "data": {
            "schedule_ticket_id": ticket_id,
            "schedule_id": schedule_id,
            # "hospital": org.regionalCode,
            # "doctor": person.regionalCode,
            # "patient": client_id,
            "date": date.isoformat(),
            "time_begin": beg_time.isoformat()[:5],
            "time_end": end_time.isoformat()[:5],
        }
    }
    result = send_event_remote(data)
    code = result['meta']['code']
    reject = result['meta'].get('reject')
    return code == 200 and reject != 1


def get_risar_id_by_mis_id(region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not binded_event(event_code):
        return
    request = {
        'event': event_code,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_client_local_id_by_remote_id(request)
    code = result['meta']['code']
    client_id = result['result']
    return client_id


def save_card_ids_match(local_id, region, entity, remote_id):
    from hippocrates.blueprints.risar.lib.sirius.events import RisarEvents
    event_code = RisarEvents.ENTER_MIS_EMPLOYEE
    if not binded_event(event_code):
        return
    request = {
        'event': event_code,
        "local_main_id": local_id,
        "remote_system_code": region,
        "remote_entity_code": entity,
        "remote_main_id": remote_id,
    }
    result = request_register_card_idents(request)
    code = result['meta']['code']
    return code
