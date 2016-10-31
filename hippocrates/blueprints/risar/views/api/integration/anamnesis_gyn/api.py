# -*- coding: utf-8 -*-
import logging
from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import AnamnesisGynXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/anamnesis/gynecology/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_gyn_schema(api_version):
    return AnamnesisGynXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/gynecology/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/gynecology/', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_gyn_save(api_version, card_id):
    anamnesis_id = None
    data = request.get_json()
    create = request.method == 'POST'
    xform = AnamnesisGynXForm(api_version, create)
    xform.validate(data)
    xform.check_params(anamnesis_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/gynecology/', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_gyn_delete(api_version, card_id):
    anamnesis_id = None
    xform = AnamnesisGynXForm(api_version)
    xform.check_params(anamnesis_id, card_id)
    xform.delete_target_obj()
    xform.store()
