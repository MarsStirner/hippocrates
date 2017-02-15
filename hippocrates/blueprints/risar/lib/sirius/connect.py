# coding: utf-8
from time import sleep

import logging
import requests

from contextlib import contextmanager

from nemesis.app import app
from requests import ConnectionError

logger = logging.getLogger('simple')


config = app.config
hippo_url = config.get('HIPPOCRATE_URL', 'http://127.0.0.1:6600/').rstrip('/')
sirius_url = config.get('SIRIUS_URL', 'http://127.0.0.1:8600/').rstrip('/')
coldstar_url = config.get('COLDSTAR_URL', 'http://127.0.0.1:6605/').rstrip('/')
login = config.get('SIRIUS_API_LOGIN', u'ВнешСис')
password = config.get('SIRIUS_API_PASSWORD', '0909')
authent_token_name = config.get('CASTIEL_AUTH_TOKEN', 'CastielAuthToken')
authoriz_token_name = config.get('HIPPOCRATE_SESSION_KEY', 'hippocrates.session.id')
session = None


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
    # пока роль не запрашиваем
    return 'role-token'
    # url = u'%s/chose_role/' % sirius_url
    url = u'%s/chose_role/' % hippo_url
    if role_code:
        url += role_code
    result = requests.post(
        url,
        cookies={authent_token_name: token}
    )
    j = result.json()
    if not result.status_code == 200:
        raise ConnectError('Ошибка авторизации')
    return result.cookies[authoriz_token_name]


def make_login():
    token = get_token(login, password)
    print ' > auth token: ', token
    # session_token = get_role(token)
    # print ' > session token: ', session_token
    session = token, None

    return session


def reconnect(func):
    begin_sleep_timeout = 1  # sec
    max_retry = 16

    def wrap(*a, **kw):
        res = None
        retry = True
        retry_count = 0
        sleep_timeout = begin_sleep_timeout
        while retry:
            retry = False
            retry_count += 1
            try:
                res = func(*a, **kw)
            except ConnectionError as exc:
                try:
                    exc_txt = str(exc)
                except (IndexError, UnicodeError):
                    exc_txt = exc.__name__
                logger.error(exc_txt)
                if retry_count >= max_retry:
                    logger.info('Retry count = %s. Stop retrying' % (retry_count,))
                else:
                    retry = True
                    logger.info('Retry count = %s. Wait for %s seconds and then try again' % (retry_count, sleep_timeout))
                    sleep(sleep_timeout)
                    if sleep_timeout < 10 * 60:  # min
                        sleep_timeout += 2
            except Exception as exc:
                try:
                    exc_txt = str(exc)
                except (IndexError, UnicodeError):
                    exc_txt = exc.__name__
                logger.error(exc_txt)
        return res
    return wrap


@reconnect
def make_api_request(method, url, json_data=None, url_args=None, resend=False):
    global session
    if not session:
        session = make_login()
    token, session_token = session
    result = getattr(requests, method)(
        sirius_url + url,
        json=json_data,
        params=url_args,
        cookies={
            authent_token_name: token,
            # authoriz_token_name: session_token
        }
    )
    if result.status_code != 200:
        if result.status_code == 401 and not resend:
            # один раз пробуем взять другой токен
            session = None
            res_json = make_api_request(method, url, json_data=json_data,
                                        url_args=url_args, resend=True)
            return res_json
        try:
            j = result.json()
            message = u'stream_id: %s %s: %s' % (
                j['meta']['stream_id'], j['meta']['code'], j['meta']['name'],
            )
        except Exception, e:
            # raise e
            message = u'Unknown ({0})({1})({2})'.format(unicode(result), unicode(result.text)[:300], unicode(e))
        raise Exception(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))

    return result.json()


def test_auth(login, password):
    print 'Coldstar: ', coldstar_url, ', Risar: ', sirius_url
    token = get_token(login, password)
    print ' > auth token: ', token
    # session_token = get_role(token)
    # print ' > session token: ', session_token
