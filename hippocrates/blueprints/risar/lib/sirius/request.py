# coding: utf-8
from .connect import make_api_request


def request_remote(data):
    url = u'/risar/api/request/remote/'
    result = make_api_request('post', url, data)
    return result


def request_local(data):
    url = u'/risar/api/request/local/'
    result = make_api_request('post', url, data)
    return result


def send_event_remote(data):
    url = u'/risar/api/send/event/remote/'
    result = make_api_request('post', url, data)
    return result


# def get_card_local_id():
#     url = u'/risar/api/card/local_id/'
#     result = make_api_request('get', url)
#     return result


def request_client_local_id_by_remote_id(data):
    url = u'/risar/api/client/local_id/'
    result = make_api_request('get', url, data)
    return result


def request_register_card_idents(data):
    url = u'/risar/api/card/register/'
    result = make_api_request('post', url, data)
    return result


def request_events_map():
    url = u'/risar/api/events/binded/'
    result = make_api_request('get', url)
    return result
