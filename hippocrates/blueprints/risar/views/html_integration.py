#! coding:utf-8
"""


@author: BARS Group
@date: 07.11.2016

"""
import datetime
from contextlib import contextmanager
from time import sleep

import os
import requests
from blueprints.risar.views.card_xform import CardXForm
from flask import url_for, redirect
from nemesis.app import app
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.lib.apiutils import RawApiResult
from flask_login import current_user

from blueprints.risar.lib import sirius
from blueprints.risar.risar_config import request_type_pregnancy
from nemesis.models.organisation import Organisation
from ..app import module
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, err_card_attrs_save_msg
)
import logging

logger = logging.getLogger('simple')


# /risar/integration/0/remote_entity/tambov/patient/6EHBT7UCLVXB5LSV/inspection.html
@module.route('/integration/<int:api_version>/remote_entity/<region>/<entity>/<remote_id>/inspection.html')
def api_card_by_remote_id(api_version, region, entity, remote_id):
    main_user = current_user.get_main_user()
    doctor_code = main_user.regionalCode
    org_code = Organisation.query.filter(
        Organisation.id == main_user.org_id
    ).value(Organisation.TFOMSCode)

    if not doctor_code or not org_code:
        raise Exception(u'Не найден Пользователь или Организация'.encode('utf-8'))

    # Добавляем/обновляем пациента по UID РМИС
    sirius.update_entity_from_mis(region, entity, remote_id)
    # безысходность по времени
    sleep(3)
    # Запрашиваем ID МР по UID РМИС
    client_id = sirius.get_risar_id_by_mis_id(region, entity, remote_id)

    # ищем первую открытую карту пациента
    cards = Event.query.join(EventType, rbRequestType).filter(
        Event.deleted == 0,
        rbRequestType.code == request_type_pregnancy,
        Event.client_id == client_id,
        Event.execDate == None,
    ).order_by(Event.createDatetime.desc()).all()
    card_id = None
    if cards:
        for card in cards:
            if not card.is_closed:  # учитывает, например, +2 дня, рез. обращения
                card_id = card.id
                break
    # если нет открытой карты для пациента
    if not card_id and client_id and doctor_code and org_code:
        # создаем в рисар новую карту
        data = {
            'client_id': client_id,
            'card_set_date': datetime.date.today().isoformat(),
            'card_doctor': doctor_code,
            'card_LPU': org_code,
        }
        card_id = card_save_or_update(data, True, api_version, card_id)

        # запись ID карты в шину
        sirius.save_card_ids_match(card_id, region, entity, remote_id)

    # переход на страницу карты пациента по ID карты
    return redirect(url_for('.html_inspection', event_id=card_id))


def card_save_or_update(data, create, api_version, card_id=None):
    if create:
        url = '/risar/api/integration/%s/card/' % api_version
    else:
        url = '/risar/api/integration/%s/card/%s' % (api_version, card_id)
    with make_login() as session:
        result = make_api_request('post' if create else 'put', url, session, data)
    return result['result']['card_id']


coldstar_url = app.config['COLDSTAR_URL'].rstrip('/')
mis_url = app.config['HIPPO_URL'].rstrip('/')
auth_token_name = app.config['CASTIEL_AUTH_TOKEN']
session_token_name = app.config['BEAKER_SESSION']['session.key']

# todo:
login = os.getenv('API_LOGIN', u'ВнешСис')
password = os.getenv('API_PASSWORD', '0909')


@contextmanager
def make_login():
    token = get_token(login, password)
    session_token = get_role(token)
    session = token, session_token

    try:
        yield session
    finally:
        release_token(token)


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
    return result.cookies[session_token_name]


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

# from blueprints.risar.views.api.integration.card.api import \
#     card_save_or_update # копипаста, т.к. ошибка объявления модулей
def card_save_or_update_old(data, create, api_version, card_id=None):
    xform = CardXForm(api_version, create)
    xform.validate(data)
    client_id = data.get('client_id')
    xform.check_params(card_id, client_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Карта сохранена, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform
