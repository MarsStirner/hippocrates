# coding: utf-8

import requests

from test_data import test_client_data, test_event_data, test_event_data2


coldstar_url = 'http://127.0.0.1:6098'
mis_url = 'http://127.0.0.1:6600'
auth_token_name = 'CastielAuthToken'
session_token_name = 'hippocrates.session.id'

login = u'ВнешСис'
password = ''


def get_token(login, password):
    url = u'%s/cas/api/acquire' % coldstar_url
    result = requests.post(
        url,
        {
            'login': login,
            'password': password
        }
    )
    j = result.json()
    if not j['success']:
        print j
        raise Exception(j['exception'])
    return j['token']


def get_role(token, role_code=''):
    url = u'%s/chose_role/' % mis_url
    if role_code:
        url += role_code
    result = requests.post(
        url,
        cookies={auth_token_name: token}
    )
    j = result.json()
    if not result.status_code == 200:
        raise Exception('Ошибка авторизации')
    return result.cookies['hippocrates.session.id']


def make_client_save(token, session_token):
    url = u'%s/risar/api/integration/0/client/' % mis_url
    result = requests.post(
        url,
        json=test_client_data,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


def register_card(token, session_token):
    url = u'%s/risar/api/integration/0/card/' % mis_url
    result = requests.post(
        url,
        json=test_event_data,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


def change_card(token, session_token, event_id):
    url = u'%s/risar/api/integration/0/card/%s' % (mis_url, event_id)
    result = requests.put(
        url,
        json=test_event_data2,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


def delete_card(token, session_token, event_id):
    url = u'%s/risar/api/integration/0/card/%s' % (mis_url, event_id)
    result = requests.delete(
        url,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


if __name__ == '__main__':
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token

    # ========================================================================
    # result = make_client_save(token, session_token)
    # print u'new client data: {0}'.format(repr(result).decode("unicode-escape"))
    #
    # client_id = '17700'
    # test_event_data['client_id'] = client_id
    # result = register_card(token, session_token)
    # print u'new event data: {0}'.format(repr(result).decode("unicode-escape"))

    client_id = '17700'
    event_id = '160'
    test_event_data2['client_id'] = client_id
    result = change_card(token, session_token, event_id)
    print u'new event data: {0}'.format(repr(result).decode("unicode-escape"))

    # event_id = '160'
    # result = delete_card(token, session_token, event_id)
    # print u'deleted event data: {0}'.format(repr(result).decode("unicode-escape"))