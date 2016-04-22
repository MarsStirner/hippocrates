#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.app import module
from blueprints.risar.views.api.integration.routing.xform import \
    RoutingXForm
from blueprints.risar.views.api.integration.logformat import hook
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint


@module.route('/api/integration/<int:api_version>/routing/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_routing_schema(api_version):
    return RoutingXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/routing/', methods=["GET"])
@api_method(hook=hook)
def api_routing_get(api_version, card_id):
    xform = RoutingXForm(api_version)
    xform.check_params(card_id)
    return xform.as_json()
