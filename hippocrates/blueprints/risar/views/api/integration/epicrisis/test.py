#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""
from blueprints.risar.views.api.integration.epicrisis.test_data import \
    test_epicrisis_data
from ..test import make_api_request, make_login


def request_post_epicrisis(session, card_id):
    url = u'/risar/api/integration/0/card/%s/epicrisis/' % (card_id,)
    result = make_api_request('post', url, session, test_epicrisis_data)
    return result


def test_post_epicrisis(card_id):
    with make_login() as session:
        result = request_post_epicrisis(session, card_id)
        print u'post epicrisis: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_epicrisis(session, card_id):
    url = u'/risar/api/integration/0/card/%s/epicrisis/' % (card_id,)
    result = make_api_request('put', url, session, test_epicrisis_data)
    return result


def test_put_epicrisis(card_id):
    with make_login() as session:
        result = request_put_epicrisis(session, card_id)
        print u'put epicrisis: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_epicrisis(session, card_id):
    url = u'/risar/api/integration/0/card/%s/epicrisis/' % (card_id,)
    result = make_api_request('delete', url, session)
    return result


def test_delete_epicrisis(card_id):
    with make_login() as session:
        result = request_delete_epicrisis(session, card_id)
        print u'delete epicrisis: {0}'.format(repr(result).decode("unicode-escape"))
