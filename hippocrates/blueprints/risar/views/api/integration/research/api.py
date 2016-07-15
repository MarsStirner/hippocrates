#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.views.api.integration.research.xform import \
    ResearchXForm
from hippocrates.blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from flask import request


@module.route('/api/integration/<int:api_version>/measures/research/schema.json', methods=['GET'])
@api_method(hook=hook)
@public_endpoint
def api_research_schema(api_version):
    return ResearchXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/research/<int:result_action_id>/', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/research', methods=['POST'])
@api_method(hook=hook)
def api_research_save(api_version, card_id, result_action_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = ResearchXForm(api_version, create)
    xform.validate(data)
    xform.check_params(result_action_id, card_id, data)
    xform.update_target_obj(data)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/measures/research/<int:result_action_id>/', methods=['DELETE'])
@api_method(hook=hook)
def api_research_delete(api_version, card_id, result_action_id):
    xform = ResearchXForm(api_version)
    xform.check_params(result_action_id, card_id)
    xform.delete_target_obj()
    db.session.commit()
