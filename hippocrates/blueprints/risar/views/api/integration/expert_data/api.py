#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.expert_data.xform import \
    ExpertDataXForm
from blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint


@module.route('/api/integration/<int:api_version>/expert_data/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_expert_data_schema(api_version):
    return ExpertDataXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/expert_data', methods=["GET"])
@api_method(hook=hook)
def api_expert_data_get(api_version, card_id):
    xform = ExpertDataXForm(api_version)
    xform.check_params(card_id)
    return xform.as_json()