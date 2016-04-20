# coding: utf-8

import os
import requests

from contextlib import contextmanager

from nemesis.app import app


coldstar_url = os.getenv('TEST_COLDSTAR_URL', 'http://127.0.0.1:6098')
mis_url = os.getenv('TEST_MIS_URL', 'http://127.0.0.1:6600')
auth_token_name = 'CastielAuthToken'
session_token_name = 'hippocrates.session.id'

login = os.getenv('TEST_LOGIN', u'ВнешСис')
password = os.getenv('TEST_PASSWORD', '')


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


def make_api_request(method, url, session, json_data=None, url_args=None):
    token, session_token = session
    result = getattr(requests, method)(
        mis_url + url,
        json=json_data,
        params=url_args,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
    )
    if result.status_code != 200:
        try:
            j = result.json()
            message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
        except Exception, e:
            # raise e
            message = u'Unknown ({0})'.format(unicode(result))
        raise Exception(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
    return result.json()


def test_auth(login, password):
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token


if __name__ == '__main__':
    with app.app_context():
        from blueprints.risar.views.api.integration.client.test import test_register_edit_client
        from blueprints.risar.views.api.integration.card.test import (
            test_register_edit_delete_card,
            get_new_card_id_for_test, delete_test_card_id
        )
        from blueprints.risar.views.api.integration.anamnesis.test import (
            test_register_edit_delete_mother_anamnesis,
            test_register_edit_delete_father_anamnesis,
            test_register_edit_delete_prevpregnancies_anamnesis
        )
        from blueprints.risar.views.api.integration.measure.test import test_get_card_measures
        from blueprints.risar.views.api.integration.expert_data.test import \
            test_get_expert_data

        test_auth(login, password)

        # test_register_edit_client()

        # client_id = '17700'
        # # test_register_edit_delete_card(client_id)

        # test_card_id = get_new_card_id_for_test(client_id)
        # # test_card_id = '197'

        # test_register_edit_delete_mother_anamnesis(test_card_id)
        # test_register_edit_delete_father_anamnesis(test_card_id)
        # test_register_edit_delete_prevpregnancies_anamnesis(test_card_id)

        # delete_test_card_id(test_card_id)

        # client_id = '17700'
        # test_register_edit_delete_card(client_id)

        # test_card_id = get_new_card_id_for_test(client_id)
        # test_card_id = '7'

        # test_register_edit_delete_mother_anamnesis(test_card_id)
        # test_register_edit_delete_father_anamnesis(test_card_id)
        # test_register_edit_delete_prevpregnancies_anamnesis(test_card_id)

        # delete_test_card_id(test_card_id)

        # from blueprints.risar.views.api.integration.expert_data.test import \
        #     test_get_expert_data
        # client_id = '121'
        # test_get_expert_data(client_id)

        #     client_id = '1'
        #     test_register_edit_delete_card(client_id)
        #
        #     test_card_id = get_new_card_id_for_test(client_id)
        #     # test_card_id = '197'

        #     test_register_edit_delete_mother_anamnesis(test_card_id)
        #     test_register_edit_delete_father_anamnesis(test_card_id)
        #     test_register_edit_delete_prevpregnancies_anamnesis(test_card_id)

        #     delete_test_card_id(test_card_id)

        # card_id = '214'
        # test_get_card_measures(card_id)
