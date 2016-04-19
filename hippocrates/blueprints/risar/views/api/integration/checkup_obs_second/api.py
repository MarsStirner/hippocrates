#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.checkup_obs_second.xform import \
    CheckupObsSecondXForm
from blueprints.risar.views.api.integration.logformat import hook
from flask import request
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db


@module.route('/api/integration/<int:api_version>/checkup/obs/second/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_checkup_obs_second_schema(api_version):
    return CheckupObsSecondXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/second/<int:exam_obs_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/second/', methods=['POST'])
@api_method(hook=hook)
def api_checkup_obs_second_save(api_version, card_id, exam_obs_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = CheckupObsSecondXForm(api_version, create)
    xform.validate(data)
    xform.check_params(exam_obs_id, card_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    xform.reevaluate_data()
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/obs/second/<int:exam_obs_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_checkup_obs_second_delete(api_version, card_id, exam_obs_id):
    xform = CheckupObsSecondXForm(api_version)
    xform.check_params(exam_obs_id, card_id)
    xform.delete_target_obj()
    xform.reevaluate_data()
    db.session.commit()
