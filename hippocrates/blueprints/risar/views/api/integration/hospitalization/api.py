#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.hospitalization.xform import \
    HospitalizationXForm
from blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from flask import request


@module.route('/api/integration/<int:api_version>/hospitalization/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_hospitalization_schema(api_version):
    return HospitalizationXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/hospitalization', methods=['GET'])
@api_method(hook=hook)
def api_hospitalization_get(api_version, card_id):
    xform = HospitalizationXForm(api_version)
    xform.check_params(card_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/hospitalization/<int:hospitalization_id>', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/hospitalization', methods=['POST'])
@api_method(hook=hook)
def api_hospitalization_save(api_version, card_id, hospitalization_id):
    data = request.get_json()
    create = request.method == 'POST'
    xform = HospitalizationXForm(api_version, create)
    xform.validate(data)
    xform.check_params(hospitalization_id, card_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/checkup/puerpera/<int:hospitalization_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_hospitalization_delete(api_version, card_id, hospitalization_id):
    xform = HospitalizationXForm(api_version)
    xform.check_params(hospitalization_id, card_id)
    xform.delete_target_obj()
    db.session.commit()
