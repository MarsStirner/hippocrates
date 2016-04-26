#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.errands.xform import \
    ErrandsXForm
from blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from flask import request


@module.route('/api/integration/<int:api_version>/errands/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_integr_errands_schema(api_version):
    return ErrandsXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/', methods=['GET'])
@api_method(hook=hook)
def api_integr_errands_get(api_version, card_id):
    errand_id = None
    xform = ErrandsXForm(api_version)
    xform.target_id_required = False
    xform.check_params(errand_id, card_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/<int:errand_id>/', methods=['PUT'])
@api_method(hook=hook)
def api_integr_errands_save(api_version, card_id, errand_id):
    data = request.get_json()
    xform = ErrandsXForm(api_version)
    xform.validate(data)
    xform.check_params(errand_id, card_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/errands/<int:errand_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_integr_errands_delete(api_version, card_id, errand_id):
    xform = ErrandsXForm(api_version)
    xform.check_params(errand_id, card_id)
    xform.delete_target_obj()
    db.session.commit()
