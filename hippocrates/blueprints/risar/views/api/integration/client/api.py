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
    try:
        return ClientXForm.schema[api_version]
    except IndexError:
        raise ApiException(404, u'Api version %i is not supported. Maximum is %i' % (api_version, len(ClientXForm.schema) - 1))


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['GET'])
@api_method(hook=hook)
def api_client_get(api_version, client_id):
    xform = ClientXForm()
    xform.set_version(api_version)
    xform.find_client(client_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/client/', methods=['POST'])
@api_method(hook=hook)
def api_client_save(api_version, client_id=None):
    data = request.get_json()
    xform = ClientXForm()
    xform.set_version(api_version)
    xform.validate(data)
    xform.find_client(client_id, data)
    xform.update_client(data)
    db.session.add(xform.client)
    db.session.commit()
    return xform.as_json()
