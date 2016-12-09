#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

from ..test import make_login, make_api_request
from test_data import (puerpera_data)


def create_checkup(session, card_id, data):
    url = u'/risar/api/integration/0/card/%s/checkup/puerpera/' % card_id
    result = make_api_request('post', url, session, data)
    return result


def edit_checkup(session, card_id, checkup_id, data):
    url = u'/risar/api/integration/0/card/%s/checkup/puerpera/%s/' % (card_id, checkup_id)
    result = make_api_request('put', url, session, data)
    return result


def delete_checkup(session, card_id, checkup_id):
    url = u'/risar/api/integration/0/card/%s/checkup/puerpera/%s/' % (card_id, checkup_id)
    result = make_api_request('delete', url, session)
    return result


def test_register_edit_delete_puerpera_checkup(card_id):
    with make_login() as session:
        result = create_checkup(session, card_id, puerpera_data)
        checkup = result['result']
        checkup_id = checkup['exam_puerpera_id']
        print u'new checkup data: {0}'.format(repr(checkup).decode("unicode-escape"))

        try:
            result = create_checkup(session, card_id, puerpera_data)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_checkup(session, card_id, checkup_id, puerpera_data)
        checkup = result['result']
        meta = result['meta']
        print u'edited checkup meta: {0}'.format(repr(meta).decode("unicode-escape"))
        print u'edited checkup data: {0}'.format(repr(checkup).decode("unicode-escape"))

        puerpera_data['external_id'] = 'x'
        try:
            result = edit_checkup(session, card_id, checkup_id, puerpera_data)
        except Exception, e:
            if '404' in e.message:
                print e.message
            else:
                raise e

        result = delete_checkup(session, card_id, checkup_id)
        print u'deleted checkup id = {0}'.format(checkup_id)