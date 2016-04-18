# coding: utf-8

import requests

from contextlib import contextmanager

from nemesis.app import app

from test_data import test_client_data


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


def release_token(token):
    url = u'%s/cas/api/release' % coldstar_url
    result = requests.post(
        url,
        {
            'token': token,
        }
    )
    j = result.json()
    if not j['success']:
        print j
        raise Exception(j['exception'])


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


@contextmanager
def make_login():
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
    session = token, session_token

    try:
        yield session
    finally:
        release_token(token)


def make_api_request(method, url, session, json_data=None):
    token, session_token = session
    result = getattr(requests, method)(
        mis_url + url,
        json=json_data,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    if result.status_code != 200:
        try:
            j = result.json()
            message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
        except Exception, e:
            raise e
            message = u'Unknown'
        raise Exception(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
    return result.json()


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


if __name__ == '__main__':
    # token = get_token(login, password)
    # print ' > auth token: ', token
    # session_token = get_role(token)
    # print ' > session token: ', session_token

    # ========================================================================
    # result = make_client_save(token, session_token)
    # print u'new client data: {0}'.format(repr(result).decode("unicode-escape"))
    #

    with app.app_context():
        from blueprints.risar.views.api.integration.card.test import (test_register_edit_delete_card,
            get_new_card_id_for_test, delete_test_card_id)
        from blueprints.risar.views.api.integration.anamnesis.test import (test_register_edit_delete_mother_anamnesis,
            test_register_edit_delete_father_anamnesis, test_register_edit_delete_prevpregnancies_anamnesis)

        client_id = '17700'
        # test_register_edit_delete_card(client_id)

        test_card_id = get_new_card_id_for_test(client_id)
        # test_card_id = '197'

        test_register_edit_delete_mother_anamnesis(test_card_id)
        test_register_edit_delete_father_anamnesis(test_card_id)
        test_register_edit_delete_prevpregnancies_anamnesis(test_card_id)

        delete_test_card_id(test_card_id)

        # from blueprints.risar.views.api.integration.expert_data.test import \
        #     test_get_expert_data
        # card_id = '121'
        # test_get_expert_data(card_id)

        # from blueprints.risar.views.api.integration.routing.test import \
        #     test_get_routing
        # card_id = '1'
        # test_get_routing(card_id)
