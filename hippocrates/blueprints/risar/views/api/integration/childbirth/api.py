#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.childbirth.xform import \
    ChildbirthXForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, err_card_attrs_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from nemesis.lib.utils import public_endpoint


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/childbirth/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_childbirth_schema(api_version):
    return ChildbirthXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/childbirth/', methods=['PUT', 'POST'])
@api_method(hook=hook)
def api_childbirth_save(api_version, card_id):
    childbirth_id = None
    data = request.get_json()
    create = request.method == 'POST'
    xform = ChildbirthXForm(api_version, create)
    xform.validate(data)
    xform.check_params(childbirth_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.reevaluate_data()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Данные родоразрешения сохранены, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/childbirth/', methods=['DELETE'])
@api_method(hook=hook)
def api_childbirth_delete(api_version, card_id):
    childbirth_id = None
    xform = ChildbirthXForm(api_version)
    xform.check_params(childbirth_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.reevaluate_data()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            None,
            card_attrs_save_error_code,
            u'Данные родоразрешения удалены, но произошла ошибка при пересчёте атрибутов карты'
        )
