# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import OrgDepartmentXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/organization_department.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_org_department_schema(api_version):
    return OrgDepartmentXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/organization_department/list/')
@api_method(hook=hook)
def api_org_department_list_get(api_version):
    xform = OrgDepartmentXForm(api_version)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/organization_department/<department_id>')
@api_method(hook=hook)
def api_org_department_get(api_version, department_id):
    xform = OrgDepartmentXForm(api_version)
    xform.init_and_check_params(department_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/organization_department/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/organization_department/<department_id>', methods=['PUT'])
@api_method(hook=hook)
def api_org_department_save(api_version, department_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = OrgDepartmentXForm(api_version, create)
    xform.validate(data)
    xform.init_and_check_params(department_id, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/organization_department/<department_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_org_department_delete(api_version, department_id=None):
    xform = OrgDepartmentXForm(api_version, False)
    xform.init_and_check_params(department_id)
    xform.delete_target_obj()
    xform.store()
