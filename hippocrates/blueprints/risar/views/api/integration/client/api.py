# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint, public_api
from nemesis.systemwide import db
from .....app import module

from ..logformat import hook
from .xform import ClientXForm


__author__ = 'viruzzz-kun'


@module.route('/api/integration/<int:api_version>/client/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_client_schema(api_version):
    return ClientXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['GET'])
@api_method(hook=hook)
def api_client_get(api_version, client_id):
    xform = ClientXForm(api_version)
    xform.check_params(client_id)
    xform.load_data()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/client/', methods=['POST'])
@api_method(hook=hook)
def api_client_save(api_version, client_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = ClientXForm(api_version, create)
    xform.validate(data)
    xform.check_params(client_id, None, data)
    xform.update_client(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_client_delete(api_version, client_id=None):
    xform = ClientXForm(api_version)
    xform.check_params(client_id)
    xform.delete_target_obj_data()
    xform.store()
