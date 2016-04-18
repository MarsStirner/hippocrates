# coding: utf-8

from ..test import make_login, make_api_request
from .test_data import query_m1, query_m2


def get_card_measure_list(session, card_id, params=None):
    url = u'/risar/api/integration/0/card/%s/measures/list/' % card_id
    result = make_api_request('get', url, session, url_args=params)
    return result


def test_get_card_measures(card_id):
    with make_login() as session:
        result = get_card_measure_list(session, card_id)
        mesaure_list = result['result']
        print u'card measures data: {0}'.format(repr(mesaure_list).decode("unicode-escape"))

        result = get_card_measure_list(session, card_id, query_m1)
        mesaure_list = result['result']
        print u'card measures data: {0}'.format(repr(mesaure_list).decode("unicode-escape"))

        result = get_card_measure_list(session, card_id, query_m2)
        mesaure_list = result['result']
        print u'card measures data: {0}'.format(repr(mesaure_list).decode("unicode-escape"))
