# -*- coding: utf-8 -*-
from contextlib import contextmanager

import os
import requests
from nemesis.models.actions import Action
from nemesis.models.enums import ActionStatus

coldstar_url = os.getenv('TEST_COLDSTAR_URL', 'http://127.0.0.1:6098')
mis_url = os.getenv('TEST_MIS_URL', 'http://127.0.0.1:6600')
auth_token_name = 'CastielAuthToken'
session_token_name = 'hippocrates.session.id'

login = os.getenv('TEST_LOGIN', u'ВнешСис')
password = os.getenv('TEST_PASSWORD', '')

from nemesis.systemwide import cache, db
from nemesis.app import app


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

import unittest


class CheckupTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(CheckupTestCase, self).__init__(*args, **kwargs)
        print dir(make_login())
        print self.session

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def _url_to_test(self, url, data):
        result = make_api_request('post', url, {}, {})ko
        # result = make_api_request('post', url, self.session, data)

        # with app.app_context():
        #     print db.session.query(Action).filter(
        #         # Action.event_id == event_id,
        #         Action.endDate.is_(None),
        #         Action.deleted == 0,
        #         ActionType.id == Action.actionType_id,
        #         ActionType.flatCode.in_(checkup_flat_codes)
        #     )

        return self.assertTrue(True)

