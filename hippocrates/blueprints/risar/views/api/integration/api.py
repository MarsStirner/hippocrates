# -*- coding: utf-8 -*-
from flask import request

from blueprints.risar.views.api.integration.xform import ClientXForm
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from ....app import module

__author__ = 'viruzzz-kun'


@module.route('/api/integration/<int:api_version>/client/schema.json', methods=["GET"])
@api_method
@public_endpoint
def api_client_schema(api_version):
    return ClientXForm.schema[api_version]


@module.route('/api/integration/<int:api_version>/client/<external_system_id>/<external_client_id>', methods=['GET'])
@api_method
@public_endpoint
def api_client_get(api_version, external_system_id, external_client_id):
    xform = ClientXForm()
    xform.set_version(api_version)
    xform.set_external_system(external_system_id)
    xform.find_client(external_client_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/client/<external_system_id>/<external_client_id>', methods=['PUT'])
@module.route('/api/integration/<int:api_version>/client/<external_system_id>/', methods=['POST'])
@api_method
@public_endpoint
def api_client_save(api_version, external_system_id, external_client_id=None):
    data = request.get_json()
    xform = ClientXForm()
    xform.set_version(api_version)
    xform.validate(data)
    xform.set_external_system(external_system_id)
    xform.find_client(external_client_id, data)
    xform.update_client(data)
    db.session.add(xform.client)
    db.session.commit()
    return xform.as_json()


