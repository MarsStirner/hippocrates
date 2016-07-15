#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""
from hippocrates.blueprints.risar.views.api.integration.specialists_checkup.test_data import \
    test_specialists_checkup_data
from ..test import make_api_request, make_login


def request_post_specialists_checkup(session, card_id):
    url = u'/risar/api/integration/0/card/%s/measures/specialists_checkup' % card_id
    result = make_api_request('post', url, session, test_specialists_checkup_data)
    return result


def test_post_specialists_checkup(card_id):
    with make_login() as session:
        result = request_post_specialists_checkup(session, card_id)
        print u'post specialists_checkup: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_specialists_checkup(session, card_id, result_action_id):
    url = u'/risar/api/integration/0/card/%s/measures/specialists_checkup/%s/' % (card_id, result_action_id)
    result = make_api_request('put', url, session, test_specialists_checkup_data)
    return result


def test_put_specialists_checkup(card_id, result_action_id):
    with make_login() as session:
        result = request_put_specialists_checkup(session, card_id, result_action_id)
        print u'put specialists_checkup: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_specialists_checkup(session, card_id, result_action_id):
    url = u'/risar/api/integration/0/card/%s/measures/specialists_checkup/%s/' % (card_id, result_action_id)
    result = make_api_request('delete', url, session)
    return result


def test_delete_specialists_checkup(card_id, result_action_id):
    with make_login() as session:
        result = request_delete_specialists_checkup(session, card_id, result_action_id)
        print u'delete specialists_checkup: {0}'.format(repr(result).decode("unicode-escape"))
