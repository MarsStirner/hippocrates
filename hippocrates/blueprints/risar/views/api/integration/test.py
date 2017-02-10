# coding: utf-8

import os
import requests

from contextlib import contextmanager


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
    print 'Coldstar: ', coldstar_url, ', Risar: ', mis_url
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token


if __name__ == '__main__':
    from nemesis.app import app

    with app.app_context():
        import nemesis.models
        from hippocrates.blueprints.risar.views.api.integration.client.test import test_register_edit_client

        from hippocrates.blueprints.risar.views.api.integration.card.test import (
            test_register_edit_delete_card,
            get_new_card_id_for_test, delete_test_card_id
        )
        from hippocrates.blueprints.risar.views.api.integration.anamnesis.test import (
            test_register_edit_delete_mother_anamnesis,
            test_register_edit_delete_father_anamnesis,
            test_register_edit_delete_prevpregnancies_anamnesis
        )
        from hippocrates.blueprints.risar.views.api.integration.measure.test import test_get_card_measures
        from hippocrates.blueprints.risar.views.api.integration.expert_data.test import \
            test_get_expert_data
        from hippocrates.blueprints.risar.views.api.integration.concilium.test import \
            test_register_edit_delete_concilium

        test_auth(login, password)

        # test_register_edit_client()

        # client_id = '17711'
        # test_register_edit_delete_card(client_id)

        # test_card_id = get_new_card_id_for_test(client_id)
        # test_card_id = '214'
        # test_register_edit_delete_mother_anamnesis(test_card_id)
        # test_register_edit_delete_father_anamnesis(test_card_id)
        # test_register_edit_delete_prevpregnancies_anamnesis(test_card_id)

        # delete_test_card_id(test_card_id)

        # from hippocrates.blueprints.risar.views.api.integration.checkup_obs_first.test import \
        #     test_register_edit_delete_first_checkup
        # card_id = '278'
        # test_register_edit_delete_first_checkup(card_id)

        from hippocrates.blueprints.risar.views.api.integration.checkup_obs_second.test import \
            test_register_edit_delete_second_checkup, test_edit_ticket25
        # card_id = '72'
        # test_register_edit_delete_second_checkup(card_id)
        # test_edit_ticket25(377, 8303)

        # from hippocrates.blueprints.risar.views.api.integration.checkup_pc.test import \
        #     test_register_edit_delete_pc_checkup
        # card_id = '214'
        # test_register_edit_delete_pc_checkup(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.checkup_puerpera.test import \
        #     test_register_edit_delete_puerpera_checkup
        # card_id = '214'
        # test_register_edit_delete_puerpera_checkup(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.expert_data.test import \
        #     test_get_expert_data
        # card_id = '214'
        # test_get_expert_data(card_id)

        # card_id = '214'
        # test_get_card_measures(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.childbirth.test import \
        #     test_put_childbirth, test_delete_childbirth, test_post_childbirth
        # card_id = '1'
        # test_post_childbirth(card_id)
        # test_put_childbirth(card_id)
        # test_delete_childbirth(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.hospitalization.test import \
        #     test_put_hospitalization, test_delete_hospitalization, test_post_hospitalization
        # from hippocrates.blueprints.risar.views.api.integration.hospitalization.test_data import \
        #     test_hospitalization_data
        # card_id = '1'
        # event_measure_id = '76'
        # hospitalization_id = '68'
        # test_hospitalization_data['measure_id'] = event_measure_id
        # test_delete_hospitalization(card_id, hospitalization_id)
        # test_post_hospitalization(card_id)
        # test_put_hospitalization(card_id, hospitalization_id)

        # from hippocrates.blueprints.risar.views.api.integration.routing.test import \
        #     test_get_routing
        # card_id = '1'
        # test_get_routing(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.errands.test import \
        #     test_get_errands, test_put_errands, test_delete_errands
        # card_id = '214'
        # errand_id = '21'
        # test_get_errands(card_id)
        # test_put_errands(card_id, errand_id)
        # test_delete_errands(card_id, errand_id)
        # test_get_errands(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.epicrisis.test import \
        #     test_post_epicrisis, test_put_epicrisis, test_delete_epicrisis
        # card_id = '1'
        # test_post_epicrisis(card_id)
        # test_put_epicrisis(card_id)
        # test_delete_epicrisis(card_id)

        # card_id = '214'
        # test_register_edit_delete_concilium(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.specialists_checkup.test import \
        #     test_put_specialists_checkup, test_delete_specialists_checkup, test_post_specialists_checkup
        # from hippocrates.blueprints.risar.views.api.integration.specialists_checkup.test_data import \
        #     test_specialists_checkup_data
        # card_id = '1'
        # event_measure_id = '3230'
        # result_action_id = '892'
        # measure_type_code = '0003'
        # test_specialists_checkup_data['measure_type_code'] = measure_type_code
        # test_delete_specialists_checkup(card_id, result_action_id)
        # test_post_specialists_checkup(card_id)
        # test_specialists_checkup_data['measure_id'] = event_measure_id
        # test_put_specialists_checkup(card_id, result_action_id)

        # from hippocrates.blueprints.risar.views.api.integration.research.test import \
        #     test_put_research, test_delete_research, test_post_research
        # from hippocrates.blueprints.risar.views.api.integration.research.test_data import \
        #     test_research_data
        # card_id = '278'
        # event_measure_id = '3234'
        #
        # result_action_id = '895'
        # measure_type_code = '0022'
        # test_research_data['measure_type_code'] = measure_type_code
        # test_delete_research(card_id, result_action_id)
        # test_post_research(card_id)
        # test_research_data['measure_id'] = event_measure_id
        # test_put_research(card_id, result_action_id)

        # from hippocrates.blueprints.risar.views.api.integration.schedule.test import \
        #     test_create_schedules
        # test_create_schedules()

        # from hippocrates.blueprints.risar.views.api.integration.doctors.test import \
        #     test_create_update_doctor
        # test_create_update_doctor()

        # from hippocrates.blueprints.risar.views.api.integration.checkup_gyn.test import \
        #     test_register_edit_delete_gyn_checkup
        # card_id = '354'
        # test_register_edit_delete_gyn_checkup(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.anamnesis_gyn.test import \
        #     test_register_edit_delete_gyn_anamnesis
        # card_id = '354'
        # test_register_edit_delete_gyn_anamnesis(card_id)

        # from hippocrates.blueprints.risar.views.api.integration.orgs.test import \
        #     test_create_update_organization
        # test_create_update_organization()

        # from hippocrates.blueprints.risar.views.api.integration.schedule_tickets.test import \
        #     test_create_update_delete_schedule_tickets
        # test_create_update_delete_schedule_tickets()

        # from hippocrates.blueprints.risar.views.api.integration.schedule.test import \
        #     test_create_update_delete_schedule_full
        # test_create_update_delete_schedule_full()
