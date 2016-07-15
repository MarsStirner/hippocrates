#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""
from hippocrates.blueprints.risar.views.api.integration.errands.test_data import \
    test_errands_data
from ..test import make_api_request, make_login


def request_get_errands(session, card_id):
    url = u'/risar/api/integration/0/card/%s/errands/' % card_id
    result = make_api_request('get', url, session, test_errands_data)
    return result


def test_get_errands(card_id):
    with make_login() as session:
        result = request_get_errands(session, card_id)
        print u'get errands: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_errands(session, card_id, errand_id):
    url = u'/risar/api/integration/0/card/%s/errands/%s/' % (card_id, errand_id)
    result = make_api_request('put', url, session, test_errands_data)
    return result


def test_put_errands(card_id, errand_id):
    with make_login() as session:
        result = request_put_errands(session, card_id, errand_id)
        print u'put errands: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_errands(session, card_id, errand_id):
    url = u'/risar/api/integration/0/card/%s/errands/%s/' % (card_id, errand_id)
    result = make_api_request('delete', url, session)
    return result


def test_delete_errands(card_id, errand_id):
    with make_login() as session:
        result = request_delete_errands(session, card_id, errand_id)
        print u'delete errands: {0}'.format(repr(result).decode("unicode-escape"))
