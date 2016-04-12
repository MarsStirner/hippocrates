#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

# coding: utf-8

import requests

from test_data import test_obs_second_data

coldstar_url = 'http://127.0.0.1:6097'
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


def new_checkup(token, session_token, event_id):
    url = u'%s/risar/api/integration/0/card/%s/checkup/obs/second/' % (mis_url, event_id)
    result = requests.post(
        url,
        json=test_obs_second_data,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


def change_checkup(token, session_token, event_id, checkup_id):
    url = u'%s/risar/api/integration/0/card/%s/checkup/obs/second/%s/' % (mis_url, event_id, checkup_id)
    result = requests.put(
        url,
        json=test_obs_second_data,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    print result
    j = result.json()
    return j


def delete_checkup(token, session_token, event_id, checkup_id):
    url = u'%s/risar/api/integration/0/card/%s/checkup/obs/second/%s/' % (mis_url, event_id, checkup_id)
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
    # event_id = '146'
    # result = new_checkup(token, session_token, event_id)
    # print u'new event data: {0}'.format(repr(result).decode("unicode-escape"))

    event_id = '146'
    checkup_id = '564'
    result = change_checkup(token, session_token, event_id, checkup_id)
    print u'new event data: {0}'.format(repr(result).decode("unicode-escape"))

    # event_id = '146'
    # checkup_id = '653'
    # result = delete_checkup(token, session_token, event_id, checkup_id)
    # print u'deleted event data: {0}'.format(repr(result).decode("unicode-escape"))
