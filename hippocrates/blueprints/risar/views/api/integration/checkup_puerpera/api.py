#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.checkup_puerpera.xform import \
    CheckupPuerperaXForm, CheckupPuerperaTicket25XForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from hippocrates.blueprints.risar.views.api.integration.const import (
    measures_save_error_code, err_measures_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from nemesis.lib.utils import public_endpoint


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/checkup/puerpera/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_puerpera_schema(api_version):
    return CheckupPuerperaXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['GET'])
@api_method(hook=hook)
def api_checkup_puerpera_get(api_version, card_id, exam_puerpera_id):
    xform = CheckupPuerperaXForm(api_version)
    xform.check_params(exam_puerpera_id, card_id)
    xform.find_target_obj(exam_puerpera_id)
    return xform.as_json()


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


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_puerpera_delete(api_version, card_id, exam_puerpera_id):
    xform = CheckupPuerperaXForm(api_version)
    xform.check_params(exam_puerpera_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.generate_measures()
    except Exception, e:
        action_id = exam_puerpera_id
        logger.error(err_measures_save_msg.format(action_id), exc_info=True)
        return RawApiResult(
            None,
            measures_save_error_code,
            u'Осмотр удалён, но произошла ошибка при формировании мероприятий'
        )


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/ticket25')
@api_method(hook=hook)
def api_checkup_puerpera_ticket25_get(api_version, card_id, exam_puerpera_id):
    xform = CheckupPuerperaTicket25XForm(api_version)
    xform.check_params(exam_puerpera_id, card_id)
    xform.find_ticket25()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/ticket25', methods=['PUT'])
@api_method(hook=hook)
def api_checkup_puerpera_ticket25_save(api_version, card_id, exam_puerpera_id):
    data = request.get_json()
    xform = CheckupPuerperaTicket25XForm(api_version)
    xform.check_params(exam_puerpera_id, card_id)
    xform.validate(data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()

