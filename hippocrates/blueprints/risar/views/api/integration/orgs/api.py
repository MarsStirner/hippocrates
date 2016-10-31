# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import OrganizationXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/organization.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_organization_schema(api_version):
    return OrganizationXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/organization/<organization_code>')
@api_method(hook=hook)
def api_organization_get(api_version, organization_code):
    xform = OrganizationXForm(api_version)
    xform.init_and_check_params(organization_code)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/organization/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/organization/<organization_code>', methods=['PUT'])
@api_method(hook=hook)
def api_organization_save(api_version, organization_code=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = OrganizationXForm(api_version, create)
    xform.validate(data)
    xform.init_and_check_params(organization_code, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()
