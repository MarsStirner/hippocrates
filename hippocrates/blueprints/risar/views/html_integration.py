#! coding:utf-8
"""


@author: BARS Group
@date: 07.11.2016

"""
import datetime

from blueprints.risar.views.card_xform import CardXForm
from flask import url_for, redirect
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.lib.apiutils import RawApiResult

from blueprints.risar.lib import sirius
from blueprints.risar.risar_config import request_type_pregnancy
from ..app import module
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, err_card_attrs_save_msg
)
import logging

logger = logging.getLogger('simple')


# /risar/integration/0/remote_entity/tambov/patient/6EHBT7UCLVXB5LSV/inspection.html
@module.route('/integration/<int:api_version>/remote_entity/<region>/<entity>/<remote_id>/inspection.html')
def api_card_by_remote_id(api_version, region, entity, remote_id):

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
    if not card_id:
        # создаем в рисар новую карту
        data = {
            'client_id': client_id,
            'card_set_date': datetime.date.today().isoformat(),
            'card_doctor': '995',  # todo: здесь данные пользователя МИС
            'card_LPU': '1246'  # todo: здесь данные пользователя МИС
        }
        xform = card_save_or_update(data, True, api_version)
        card_id = xform.target_obj.id

        # запись ID карты в шину
        sirius.save_card_ids_match(card_id, region, entity, remote_id)

    # переход на страницу карты пациента по ID карты
    return redirect(url_for('.html_inspection', event_id=card_id))


# from blueprints.risar.views.api.integration.card.api import \
#     card_save_or_update # копипаста, т.к. ошибка объявления модулей
def card_save_or_update(data, create, api_version, card_id=None):
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
