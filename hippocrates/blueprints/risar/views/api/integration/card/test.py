# coding: utf-8

from ..test import make_login, make_api_request
from test_data import event_data, event_data2


def register_card(session, data):
    url = u'/risar/api/integration/0/card/'
    result = make_api_request('post', url, session, data)
    return result


def change_card(session, event_id, data):
    url = u'/risar/api/integration/0/card/%s' % event_id
    result = make_api_request('put', url, session, data)
    return result


def delete_card(session, event_id):
    url = u'/risar/api/integration/0/card/%s' % event_id
    result = make_api_request('delete', url, session)
    return result


def test_register_edit_delete_card(client_id):
    with make_login() as session:
        event_data['client_id'] = client_id
        result = register_card(session, event_data)
        card = result['result']
        card_id = card['card_id']
        print u'new card_id = {0}'.format(card_id)
        print u'new event data: {0}'.format(repr(card).decode("unicode-escape"))

        try:
            result = register_card(session, event_data)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        event_data2['client_id'] = client_id
        result = change_card(session, card_id, event_data2)
        card = result['result']
        print u'edited card_id = {0}'.format(card['card_id'])
        print u'edited event data: {0}'.format(repr(card).decode("unicode-escape"))

        result = delete_card(session, card_id)
        card = result['result']
        print u'deleted card_id = {0}'.format(card_id)


def get_new_card_id_for_test(client_id):
    with make_login() as session:
        event_data['client_id'] = client_id
        result = register_card(session, event_data)
        card = result['result']
        card_id = card['card_id']
        print u'new card_id = {0}'.format(card_id)
        print u'new event data: {0}'.format(repr(card).decode("unicode-escape"))
    return card_id


def delete_test_card_id(card_id):
    with make_login() as session:
        result = delete_card(session, card_id)
        print u'deleted card_id = {0}'.format(card_id)