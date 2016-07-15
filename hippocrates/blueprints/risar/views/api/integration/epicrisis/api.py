#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.epicrisis.xform import \
    EpicrisisXForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from flask import request


@module.route('/api/integration/<int:api_version>/epicrisis/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_integr_epicrisis_schema(api_version):
    return EpicrisisXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/epicrisis/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/epicrisis/', methods=['PUT'])
@api_method(hook=hook)
def api_integr_epicrisis_save(api_version, card_id):
    data = request.get_json()
    xform = EpicrisisXForm(api_version)
    xform.validate(data)
    xform.check_params(card_id, data=data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/epicrisis/', methods=['DELETE'])
@api_method(hook=hook)
def api_integr_epicrisis_delete(api_version, card_id):
    xform = EpicrisisXForm(api_version)
    xform.check_params(card_id)
    xform.delete_target_obj()
    db.session.commit()
