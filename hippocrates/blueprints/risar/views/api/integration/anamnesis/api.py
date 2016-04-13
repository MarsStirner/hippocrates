# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from .....app import module

from ..logformat import hook
from .xform import AnamnesisMotherXForm, AnamnesisFatherXForm, AnamnesisPrevPregXForm


@module.route('/api/integration/<int:api_version>/anamnesis/mother/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_mother_schema(api_version):
    try:
        return AnamnesisMotherXForm.schema[api_version]
    except IndexError:
        raise ApiException(
            404,
            u'Api version {0} is not supported. Maximum is {0}'.format(api_version, len(AnamnesisMotherXForm.schema) - 1)
        )


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_mother_save(api_version, card_id):
    data = request.get_json()
    xform = AnamnesisMotherXForm(api_version)
    xform.validate(data)
    create = request.method == 'POST'
    xform.check_target_obj_single(card_id, data, create)
    xform.update_target_obj(data)
    xform.store()

    xform.update_card_attrs()
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_mother_delete(api_version, card_id):
    xform = AnamnesisMotherXForm(api_version)
    xform.check_target_obj_single(card_id)
    xform.delete_target_obj()
    xform.store()

    xform.update_card_attrs()
    xform.store()


@module.route('/api/integration/<int:api_version>/anamnesis/father/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_father_schema(api_version):
    try:
        return AnamnesisFatherXForm.schema[api_version]
    except IndexError:
        raise ApiException(
            404,
            u'Api version {0} is not supported. Maximum is {0}'.format(api_version, len(AnamnesisFatherXForm.schema) - 1)
        )


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_father_save(api_version, card_id):
    data = request.get_json()
    xform = AnamnesisFatherXForm(api_version)
    xform.validate(data)
    create = request.method == 'POST'
    xform.check_target_obj_single(card_id, data, create)
    xform.update_target_obj(data)
    xform.store()

    xform.update_card_attrs()
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_father_delete(api_version, card_id):
    xform = AnamnesisFatherXForm(api_version)
    xform.check_target_obj_single(card_id)
    xform.delete_target_obj()
    xform.store()

    xform.update_card_attrs()
    xform.store()


@module.route('/api/integration/<int:api_version>/anamnesis/prevpregnancy/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_prevpregnancy_schema(api_version):
    try:
        return AnamnesisPrevPregXForm.schema[api_version]
    except IndexError:
        raise ApiException(
            404,
            u'Api version {0} is not supported. Maximum is {0}'.format(api_version, len(AnamnesisPrevPregXForm.schema) - 1)
        )


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/<prevpregnancy_id>', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_prevpregnancy_save(api_version, card_id, prevpregnancy_id=None):
    data = request.get_json()
    xform = AnamnesisPrevPregXForm(api_version)
    xform.validate(data)
    xform.check_target_obj(card_id, prevpregnancy_id, data)
    xform.update_target_obj(data)
    xform.store()

    xform.update_card_attrs()
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/<prevpregnancy_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_prevpregnancy_delete(api_version, card_id, prevpregnancy_id):
    xform = AnamnesisPrevPregXForm(api_version)
    xform.check_target_obj(card_id, prevpregnancy_id)
    xform.delete_target_obj()
    xform.store()

    xform.update_card_attrs()
    xform.store()