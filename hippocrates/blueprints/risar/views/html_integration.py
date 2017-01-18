#! coding:utf-8
"""


@author: BARS Group
@date: 07.11.2016

"""
import datetime
from contextlib import contextmanager

import os
import requests
from flask import url_for, redirect
from hippocrates.blueprints.risar.views.api.integration.card.api import \
    card_save_or_update
from nemesis.app import app
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from flask_login import current_user

from hippocrates.blueprints.risar.lib import sirius
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy
from nemesis.models.organisation import Organisation
from nemesis.models.person import Person
from ..app import module
import logging

logger = logging.getLogger('simple')


# /risar/integration/0/remote_entity/tambov/patient/6EHBT7UCLVXB5LSV/inspection.html
@module.route('/integration/<int:api_version>/remote_entity/<region>/<entity>/<remote_id>/inspection.html')
def api_card_by_remote_id(api_version, region, entity, remote_id):
    main_user = current_user.get_main_user()
    # doctor_code = main_user.regionalCode
    # org_code = Organisation.query.filter(
    #     Organisation.id == main_user.org_id
    # ).value(Organisation.regionalCode)
    # по разным причинам бывают в main_user не те коды, или их нет
    person = Person.query.get(main_user.id)
    doctor_code = person.regionalCode
    org_code = Organisation.query.filter(
        Organisation.id == person.org_id
    ).value(Organisation.regionalCode)

    # если глюк оказался вдруг
    # doctor_code = '58211165'  # Коняев /Тамбов
    # org_code = '1434663'  # Контрольная МО /Тамбов

    if not doctor_code or not org_code:
        err_txt = (
            u'Не найден Пользователь или Организация (id="%s" doctor_code="%s" org_code="%s")'
            % (main_user.id, doctor_code, org_code)
        )
        logger.error(err_txt)
        raise Exception(err_txt.encode('utf-8'))

    # Добавляем/обновляем пациента по UID РМИС
    sirius.update_entity_from_mis(region, entity, remote_id)
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
    if not card_id and client_id:
        # создаем в рисар новую карту
        data = {
            'client_id': client_id,
            'card_set_date': datetime.date.today().isoformat(),
            'card_doctor': doctor_code,
            'card_LPU': org_code,
        }
        # card_id = create_or_update_card(data, True, api_version, card_id)
        card_id = card_save_or_update_get_id(data, True, api_version)

        # запись ID карты в шину
        sirius.save_card_ids_match(card_id, region, entity, remote_id)

    # переход на страницу осмотра пациента по ID карты
    return redirect(url_for('.html_inspection', event_id=card_id))


def card_save_or_update_get_id(data, create, api_version, card_id=None):
    xform = card_save_or_update(data, create, api_version, card_id)
    return xform.target_obj.id


# todo удалить, если верхний вариант пройдет проверку
def create_or_update_card(data, create, api_version, card_id=None):
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