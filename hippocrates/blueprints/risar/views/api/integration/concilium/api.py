# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from .....app import module

from ..logformat import hook
from .xform import ConciliumXForm


@module.route('/api/integration/<int:api_version>/concilium/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_concilium_schema(api_version):
    return ConciliumXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/concilium/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/concilium/<int:concilium_id>', methods=['PUT'])
@api_method(hook=hook)
def api_concilium_save(api_version, card_id, concilium_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = ConciliumXForm(api_version, create)
    xform.validate(data)
    xform.check_params(concilium_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/concilium/<int:concilium_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_concilium_delete(api_version, card_id, concilium_id):
    xform = ConciliumXForm(api_version)
    xform.check_params(concilium_id, card_id)
    xform.delete_target_obj()
    xform.store()