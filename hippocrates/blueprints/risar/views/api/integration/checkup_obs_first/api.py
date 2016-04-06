#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.checkup_obs_first.xform import \
    CheckupObsFirstXForm
from blueprints.risar.views.api.integration.logformat import hook
from flask import request
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db


@module.route('/api/integration/<int:api_version>/checkup/obs/first/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_obs_first_schema(api_version):
    try:
        return CheckupObsFirstXForm.schema[api_version]
    except IndexError:
        raise ApiException(404, u'Api version %i is not supported. Maximum is %i' % (api_version, len(CheckupObsFirstXForm.schema) - 1))


# если не будет полного ответа, то возвращать нечего
# @module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/', methods=['GET'])
# @api_method(hook=hook)
# @public_api
# def api_checkup_obs_first_get(api_version, card_id):
#     xform = CheckupObsFirstXForm(api_version)
#     xform.find_parent_obj(card_id)
#     return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/<int:exam_obs_id>', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/', methods=['POST'])
@api_method(hook=hook)
def api_checkup_obs_first_save(api_version, card_id, exam_obs_id=None):
    data = request.get_json()
    xform = CheckupObsFirstXForm(api_version)
    xform.validate(data)
    xform.check_target_obj(card_id, exam_obs_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/first/<int:exam_obs_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_obs_first_delete(api_version, card_id, exam_obs_id):
    xform = CheckupObsFirstXForm(api_version)
    xform.check_target_obj(card_id, exam_obs_id)
    xform.delete_target_obj()
    db.session.commit()
