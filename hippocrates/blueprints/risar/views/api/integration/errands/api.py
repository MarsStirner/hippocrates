#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.errands.xform import \
    ErrandXForm, ErrandListXForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint


@module.route('/api/integration/<int:api_version>/errands/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_integr_errands_schema(api_version):
    return ErrandXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/errands/list/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_integr_errands_list_schema(api_version):
    return ErrandListXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/', methods=['GET'])
@api_method(hook=hook)
def api_integr_errands_get(api_version, card_id):
    xform = ErrandListXForm(api_version)
    xform.check_params(None, card_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/<int:errand_id>/', methods=['PUT'])
@api_method(hook=hook)
def api_integr_errands_save(api_version, card_id, errand_id):
    data = request.get_json()
    xform = ErrandXForm(api_version)
    xform.validate(data)
    xform.check_params(errand_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/<int:errand_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_integr_errands_delete(api_version, card_id, errand_id):
    xform = ErrandXForm(api_version)
    xform.check_params(errand_id, card_id)
    xform.delete_target_obj_data()
    xform.store()
