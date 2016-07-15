#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

# coding: utf-8
from hippocrates.blueprints.risar.views.api.integration.childbirth.test_data import \
    test_childbirth_data
from ..test import make_api_request, make_login


def request_post_childbirth(session, card_id):
    url = u'/risar/api/integration/0/card/%s/childbirth/' % card_id
    result = make_api_request('post', url, session, test_childbirth_data)
    return result


def test_post_childbirth(card_id):
    with make_login() as session:
        result = request_post_childbirth(session, card_id)
        print u'post childbirth: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_childbirth(session, card_id):
    url = u'/risar/api/integration/0/card/%s/childbirth/' % card_id
    result = make_api_request('put', url, session, test_childbirth_data)
    return result


def test_put_childbirth(card_id):
    with make_login() as session:
        result = request_put_childbirth(session, card_id)
        print u'put childbirth: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_childbirth(session, card_id):
    url = u'/risar/api/integration/0/card/%s/childbirth/' % card_id
    result = make_api_request('delete', url, session)
    return result


def test_delete_childbirth(card_id):
    with make_login() as session:
        result = request_delete_childbirth(session, card_id)
        print u'delete childbirth: {0}'.format(repr(result).decode("unicode-escape"))
