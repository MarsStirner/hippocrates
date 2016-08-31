#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.checkup_obs_first.xform import \
    CheckupObsFirstXForm, CheckupObsFirstTicket25XForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, measures_save_error_code,
    err_card_attrs_save_msg, err_measures_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/checkup/obs/first/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_obs_first_schema(api_version):
    return CheckupObsFirstXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/<int:exam_obs_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/', methods=['POST'])
@api_method(hook=hook)
def api_checkup_obs_first_save(api_version, card_id, exam_obs_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = CheckupObsFirstXForm(api_version, create)
    xform.validate(data)
    xform.check_params(exam_obs_id, card_id, data)
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

    try:
        xform.generate_measures()
    except Exception, e:
        action_id = xform.target_obj.id
        logger.error(err_measures_save_msg.format(action_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            measures_save_error_code,
            u'Осмотр сохранён, но произошла ошибка при формировании мероприятий'
        )

    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/<int:exam_obs_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_obs_first_delete(api_version, card_id, exam_obs_id):
    xform = CheckupObsFirstXForm(api_version)
    xform.check_params(exam_obs_id, card_id)
    xform.delete_target_obj()
    xform.reevaluate_data()
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

    try:
        xform.generate_measures()
    except Exception, e:
        action_id = exam_obs_id
        logger.error(err_measures_save_msg.format(action_id), exc_info=True)
        return RawApiResult(
            None,
            measures_save_error_code,
            u'Осмотр удалён, но произошла ошибка при формировании мероприятий'
        )


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/<int:exam_obs_id>/ticket25')
@api_method(hook=hook)
def api_checkup_obs_first_ticket25_get(api_version, card_id, exam_obs_id):
    xform = CheckupObsFirstTicket25XForm(api_version)
    xform.check_params(exam_obs_id, card_id)
    xform.find_ticket25()
    return xform.as_json()
