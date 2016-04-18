#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

from ..test import make_api_request, make_login


def request_get_hospitalization(session, card_id):
    url = u'/risar/api/integration/0/card/%s/hospitalization' % card_id
    result = make_api_request('get', url, session)
    return result


def test_get_hospitalization(card_id):
    with make_login() as session:
        result = request_get_hospitalization(session, card_id)
        print u'get expert data: {0}'.format(repr(result).decode("unicode-escape"))
