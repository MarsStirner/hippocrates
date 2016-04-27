#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.specialists_checkup.xform import \
    SpecialistsCheckupXForm
from blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from flask import request


@module.route('/api/integration/<int:api_version>/measures/specialists_checkup/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_specialists_checkup_schema(api_version):
    return SpecialistsCheckupXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/specialists_checkup/<int:result_action_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/specialists_checkup', methods=['POST'])
@api_method(hook=hook)
def api_specialists_checkup_save(api_version, card_id, result_action_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = SpecialistsCheckupXForm(api_version, create)
    xform.validate(data)
    xform.check_params(result_action_id, card_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/specialists_checkup/<int:result_action_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_specialists_checkup_delete(api_version, card_id, result_action_id):
    xform = SpecialistsCheckupXForm(api_version)
    xform.check_params(result_action_id, card_id)
    xform.delete_target_obj()
    db.session.commit()
