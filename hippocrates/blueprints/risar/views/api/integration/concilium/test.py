# coding: utf-8

from ..test import make_login, make_api_request
from test_data import (concilium_data_1, concilium_data_2)


def create_concilium(session, card_id, data):
    url = u'/risar/api/integration/0/card/%s/concilium/' % card_id
    result = make_api_request('post', url, session, data)
    return result


def edit_concilium(session, card_id, concilium_id, data):
    url = u'/risar/api/integration/0/card/%s/concilium/%s' % (card_id, concilium_id)
    result = make_api_request('put', url, session, data)
    return result


def delete_concilium(session, card_id, concilium_id):
    url = u'/risar/api/integration/0/card/%s/concilium/%s' % (card_id, concilium_id)
    result = make_api_request('delete', url, session)
    return result


def test_register_edit_delete_concilium(card_id):
    with make_login() as session:
        result = create_concilium(session, card_id, concilium_data_1)
        concilium = result['result']
        concilium_id = concilium['concilium_id']
        print u'new concilium data: {0}'.format(repr(concilium).decode("unicode-escape"))

        try:
            result = create_concilium(session, card_id, concilium_data_1)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_concilium(session, card_id, concilium_id, concilium_data_2)
        concilium = result['result']
        print u'edited concilium data: {0}'.format(repr(concilium).decode("unicode-escape"))

        concilium_data_2['external_id'] = 'x'
        try:
            result = edit_concilium(session, card_id, concilium_id, concilium_data_2)
        except Exception, e:
            if '404' in e.message:
                print e.message
            else:
                raise e

        result = delete_concilium(session, card_id, concilium_id)
        print u'deleted concilium id = {0}'.format(concilium_id)
