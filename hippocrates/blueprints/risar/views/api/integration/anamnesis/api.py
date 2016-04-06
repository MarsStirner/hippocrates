# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from .....app import module

from ..logformat import hook
from .xform import AnamnesisMotherXForm, AnamnesisFatherXForm


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
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/<anamnesis_id>', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_mother_save(api_version, card_id, anamnesis_id=None):
    data = request.get_json()
    xform = AnamnesisMotherXForm()
    xform.set_version(api_version)
    xform.validate(data)
    xform.find_anamnesis(card_id, anamnesis_id, data)
    xform.update_anamnesis(data)
    db.session.add(xform.anamnesis)
    db.session.commit()

    xform.update_card_attrs()
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/<anamnesis_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_mother_delete(api_version, card_id, anamnesis_id):
    xform = AnamnesisMotherXForm()
    xform.set_version(api_version)
    xform.find_anamnesis(card_id, anamnesis_id)
    xform.delete_anamnesis()
    db.session.add(xform.anamnesis)
    db.session.commit()

    xform.update_card_attrs()
    db.session.commit()
    return xform.as_json()


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
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/<anamnesis_id>', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_father_save(api_version, card_id, anamnesis_id=None):
    data = request.get_json()
    xform = AnamnesisFatherXForm()
    xform.set_version(api_version)
    xform.validate(data)
    xform.find_anamnesis(card_id, anamnesis_id, data)
    xform.update_anamnesis(data)
    db.session.add(xform.anamnesis)
    db.session.commit()

    xform.update_card_attrs()
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/<anamnesis_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_father_delete(api_version, card_id, anamnesis_id):
    xform = AnamnesisFatherXForm()
    xform.set_version(api_version)
    xform.find_anamnesis(card_id, anamnesis_id)
    xform.delete_anamnesis()
    db.session.add(xform.anamnesis)
    db.session.commit()

    xform.update_card_attrs()
    db.session.commit()
    return xform.as_json()