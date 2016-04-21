#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""
from blueprints.risar.views.api.integration.hospitalization.test_data import \
    test_hospitalization_data
from ..test import make_api_request, make_login


def request_post_hospitalization(session, card_id):
    url = u'/risar/api/integration/0/card/%s/hospitalization/' % card_id
    result = make_api_request('post', url, session, test_hospitalization_data)
    return result


def test_post_hospitalization(card_id):
    with make_login() as session:
        result = request_post_hospitalization(session, card_id)
        print u'post hospitalization: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_hospitalization(session, card_id, hospitalization_id):
    url = u'/risar/api/integration/0/card/%s/hospitalization/%s/' % (card_id, hospitalization_id)
    result = make_api_request('put', url, session, test_hospitalization_data)
    return result


def test_put_hospitalization(card_id, hospitalization_id):
    with make_login() as session:
        result = request_put_hospitalization(session, card_id, hospitalization_id)
        print u'put hospitalization: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_hospitalization(session, card_id, hospitalization_id):
    url = u'/risar/api/integration/0/card/%s/hospitalization/%s' % (card_id, hospitalization_id)
    result = make_api_request('delete', url, session)
    return result


def test_delete_hospitalization(card_id, hospitalization_id):
    with make_login() as session:
        result = request_delete_hospitalization(session, card_id, hospitalization_id)
        print u'delete hospitalization: {0}'.format(repr(result).decode("unicode-escape"))
