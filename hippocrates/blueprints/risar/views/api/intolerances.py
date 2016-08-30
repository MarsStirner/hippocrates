# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent.common import represent_intolerance
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_traverse
from nemesis.models.client import ClientAllergy, ClientIntoleranceMedicament
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


# Аллергии и медикаментозные непереносимости


def intolerance_class_from_type(i_type):
    if i_type == 'allergy':
        return ClientAllergy
    elif i_type == 'medicine':
        return ClientIntoleranceMedicament


@module.route('/api/0/anamnesis/intolerances/')
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['GET'])
@api_method
def api_0_intolerances_get(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, u'Тип непереносимости не найден')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, u'Объект непереносимости не найден')
    return dict(
        represent_intolerance(obj),
        id=object_id
    )


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['DELETE'])
@api_method
def api_0_intolerances_delete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, u'Неперносимость не найдена')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, u'Аллергия не найдена')
    if obj.deleted:
        raise ApiException(400, u'Аллергия уже была удалена')
    obj.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>/undelete', methods=['POST'])
@api_method
def api_0_intolerances_undelete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, u'Тип непереносимости не найден')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, u'Аллергия не найдена')
    if not obj.deleted:
        raise ApiException(400, u'Аллергия уже была удалена')
    obj.deleted = 0
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/intolerances/<i_type>/', methods=['POST'])
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['POST'])
@api_method
def api_0_intolerances_post(i_type, object_id=None):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, u'Тип непереносимости не найден')
    client_id = request.args.get('client_id', None)
    if object_id is None:
        if client_id is None:
            raise ApiException(400, u'Client не определен')
        obj = c()
    else:
        obj = c.query.get(object_id)
        if obj is None:
            raise ApiException(404, u'Action не найден')
    json = request.get_json()
    obj.name = json.get('name')
    obj.client_id = client_id
    obj.power = safe_traverse(json, 'power', 'id')
    obj.createDate = json.get('date')
    obj.notes = json.get('note')
    db.session.add(obj)
    db.session.commit()
    return represent_intolerance(obj)