#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from flask import request

from blueprints.risar.app import module
from blueprints.risar.views.api.integration.checkup_puerpera.xform import \
    CheckupPuerperaXForm
from blueprints.risar.views.api.integration.logformat import hook
from blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, measures_save_error_code,
    err_card_attrs_save_msg, err_measures_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/checkup/puerpera/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_puerpera_schema(api_version):
    return CheckupPuerperaXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/', methods=['POST'])
@api_method(hook=hook)
def api_checkup_puerpera_save(api_version, card_id, exam_puerpera_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = CheckupPuerperaXForm(api_version, create)
    xform.validate(data)
    xform.check_params(exam_puerpera_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.reevaluate_data()
        db.session.commit()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Осмотр сохранён, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_puerpera_delete(api_version, card_id, exam_puerpera_id):
    xform = CheckupPuerperaXForm(api_version)
    xform.check_params(exam_puerpera_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.reevaluate_data()
        db.session.commit()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            None,
            card_attrs_save_error_code,
            u'Осмотр удалён, но произошла ошибка при пересчёте атрибутов карты'
        )