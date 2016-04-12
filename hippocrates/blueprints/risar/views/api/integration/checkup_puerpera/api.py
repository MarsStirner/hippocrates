#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.checkup_puerpera.xform import \
    CheckupPuerperaXForm
from blueprints.risar.views.api.integration.logformat import hook
from flask import request
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db


@module.route('/api/integration/<int:api_version>/checkup/puerpera/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_puerpera_schema(api_version):
    try:
        return CheckupPuerperaXForm.schema[api_version]
    except IndexError:
        raise ApiException(404, u'Api version %i is not supported. Maximum is %i' % (api_version, len(CheckupPuerperaXForm.schema) - 1))


# метод GET не описан
# @module.route('/api/integration/<int:api_version>/card/<int:card_id>/puerpera/', methods=['GET'])
# @api_method(hook=hook)
# def api_checkup_puerpera_get(api_version, card_id):
#     xform = CheckupPuerperaXForm(api_version)
#     xform.find_parent_obj(card_id)
#     return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/', methods=['POST'])
@api_method(hook=hook)
def api_checkup_puerpera_save(api_version, card_id, exam_puerpera_id=None):
    data = request.get_json()
    xform = CheckupPuerperaXForm(api_version)
    xform.validate(data)
    xform.check_target_obj(card_id, exam_puerpera_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    xform.reevaluate_data()
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:exam_puerpera_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_puerpera_delete(api_version, card_id, exam_puerpera_id):
    # data = request.get_json()
    xform = CheckupPuerperaXForm(api_version)
    # xform.validate(data)
    # xform.check_target_obj(card_id, exam_puerpera_id, data)
    xform.check_target_obj(card_id, exam_puerpera_id)
    xform.delete_target_obj()
    xform.reevaluate_data()
    db.session.commit()
