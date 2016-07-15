# -*- coding: utf-8 -*-
import logging
from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from hippocrates.blueprints.risar.views.api.integration.const import (
    card_attrs_save_error_code, err_card_attrs_save_msg
)
from nemesis.lib.apiutils import api_method, RawApiResult
from .....app import module

from ..logformat import hook
from .xform import AnamnesisMotherXForm, AnamnesisFatherXForm, AnamnesisPrevPregXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/anamnesis/mother/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_mother_schema(api_version):
    return AnamnesisMotherXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_mother_save(api_version, card_id):
    anamnesis_id = None
    data = request.get_json()
    create = request.method == 'POST'
    xform = AnamnesisMotherXForm(api_version, create)
    xform.validate(data)
    xform.check_params(anamnesis_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Анамнез сохранён, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/mother/', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_mother_delete(api_version, card_id):
    anamnesis_id = None
    xform = AnamnesisMotherXForm(api_version)
    xform.check_params(anamnesis_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            None,
            card_attrs_save_error_code,
            u'Анамнез удалён, но произошла ошибка при пересчёте атрибутов карты'
        )


@module.route('/api/integration/<int:api_version>/anamnesis/father/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_father_schema(api_version):
    return AnamnesisFatherXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_father_save(api_version, card_id):
    anamnesis_id = None
    data = request.get_json()
    create = request.method == 'POST'
    xform = AnamnesisFatherXForm(api_version, create)
    xform.validate(data)
    xform.check_params(anamnesis_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Анамнез сохранён, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/father/', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_father_delete(api_version, card_id):
    anamnesis_id = None
    xform = AnamnesisFatherXForm(api_version)
    xform.check_params(anamnesis_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            None,
            card_attrs_save_error_code,
            u'Анамнез удалён, но произошла ошибка при пересчёте атрибутов карты'
        )


@module.route('/api/integration/<int:api_version>/anamnesis/prevpregnancy/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_anamnesis_prevpregnancy_schema(api_version):
    return AnamnesisPrevPregXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/<prevpregnancy_id>', methods=['PUT'])
@api_method(hook=hook)
def api_anamnesis_prevpregnancy_save(api_version, card_id, prevpregnancy_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = AnamnesisPrevPregXForm(api_version, create)
    xform.validate(data)
    xform.check_params(prevpregnancy_id, card_id, data)
    xform.update_target_obj(data)
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            xform.as_json(),
            card_attrs_save_error_code,
            u'Анамнез сохранён, но произошла ошибка при пересчёте атрибутов карты'
        )
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<int:card_id>/anamnesis/prevpregnancy/<prevpregnancy_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_anamnesis_prevpregnancy_delete(api_version, card_id, prevpregnancy_id):
    xform = AnamnesisPrevPregXForm(api_version)
    xform.check_params(prevpregnancy_id, card_id)
    xform.delete_target_obj()
    xform.store()

    try:
        xform.update_card_attrs()
        xform.store()
    except Exception, e:
        logger.error(err_card_attrs_save_msg.format(card_id), exc_info=True)
        return RawApiResult(
            None,
            card_attrs_save_error_code,
            u'Анамнез удалён, но произошла ошибка при пересчёте атрибутов карты'
        )