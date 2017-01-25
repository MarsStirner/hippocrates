#! coding:utf-8
"""


@author: BARS Group
@date: 07.11.2016

"""
import datetime

import flask
from flask import url_for, redirect
from hippocrates.blueprints.risar.views.api.integration.card.api import \
    card_save_or_update
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.systemwide import db
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
    try:
        main_user = current_user.get_main_user()
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
            # здесь для нас появляется новый пациент
            db.session.commit()
            card_id = card_save_or_update_get_id(data, True, api_version)

            # запись ID карты в шину
            sirius.save_card_ids_match(card_id, region, entity, remote_id)
    except Exception as exc:
        text = exc.message
        return flask.Response(text)

    # переход на страницу осмотра пациента по ID карты
    return redirect(url_for('.html_inspection', event_id=card_id))


def card_save_or_update_get_id(data, create, api_version, card_id=None):
    xform = card_save_or_update(data, create, api_version, card_id)
    return xform.target_obj.id
