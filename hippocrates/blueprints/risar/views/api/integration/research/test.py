#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""
from blueprints.risar.views.api.integration.research.test_data import \
    test_research_data
from ..test import make_api_request, make_login


def request_post_research(session, card_id):
    url = u'/risar/api/integration/0/card/%s/measures/research' % card_id
    result = make_api_request('post', url, session, test_research_data)
    return result


def test_post_research(card_id):
    with make_login() as session:
        result = request_post_research(session, card_id)
        print u'post research: {0}'.format(repr(result).decode("unicode-escape"))


def request_put_research(session, card_id, result_action_id):
    url = u'/risar/api/integration/0/card/%s/measures/research/%s/' % (card_id, result_action_id)
    result = make_api_request('put', url, session, test_research_data)
    return result


def test_put_research(card_id, result_action_id):
    with make_login() as session:
        result = request_put_research(session, card_id, result_action_id)
        print u'put research: {0}'.format(repr(result).decode("unicode-escape"))


def request_delete_research(session, card_id, result_action_id):
    url = u'/risar/api/integration/0/card/%s/measures/research/%s/' % (card_id, result_action_id)
    result = make_api_request('delete', url, session)
    return result


def test_delete_research(card_id, result_action_id):
    with make_login() as session:
        result = request_delete_research(session, card_id, result_action_id)
        print u'delete research: {0}'.format(repr(result).decode("unicode-escape"))
