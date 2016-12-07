# -*- coding: utf-8 -*-

import logging
from flask import request

from nemesis.lib.utils import public_endpoint
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, err_card_attrs_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from .....app import module

from ..logformat import hook
from .xform import CardXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/card/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_card_schema(api_version):
    return CardXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/list/', methods=['GET'])
@api_method(hook=hook)
def api_card_list(api_version):
    xform = CardXForm(api_version, False)
    filters = None
    data = request.get_json()
    if data:
        # карты пациентов на 32 (28 для двойняшек) неделе для создания обменных карт
        # todo: фильтр для двойняшек
        filters = data.get('filters')
    obj_list = xform.get_list(filters)
    res = []
    for obj in obj_list:
        xform.check_params(obj.id, obj.client_id)
        xform.target_obj = xform._find_target_obj_query().first()
        res.append(xform.as_json())
    return res


@module.route('/api/integration/<int:api_version>/card/<int:card_id>', methods=['GET'])
@api_method(hook=hook)
def api_card_get(api_version, card_id=None):
    xform = CardXForm(api_version, False)
    xform.check_params(card_id)
    xform.find_target()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>', methods=['PUT'])
@api_method(hook=hook)
def api_card_save(api_version, card_id=None):
    data = request.get_json()
    create = request.method == 'POST'
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
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<card_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_card_delete(api_version, card_id):
    xform = CardXForm(api_version)
    xform.check_params(card_id)
    xform.delete_target_obj()
    xform.store()