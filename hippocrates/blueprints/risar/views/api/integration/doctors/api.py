# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import DoctorXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/doctor.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_doctor_schema(api_version):
    return DoctorXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/doctor/<organization_code>/list')
@api_method(hook=hook)
def api_doctor_list_get(api_version, organization_code):
    xform = DoctorXForm(api_version)
    return xform.as_json(organization_code)


@module.route('/api/integration/<int:api_version>/doctor/<organization_code>/<doctor_code>')
@api_method(hook=hook)
def api_doctor_get(api_version, organization_code, doctor_code):
    xform = DoctorXForm(api_version)
    xform.init_and_check_params(organization_code, doctor_code)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/doctor/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/doctor/<organization_code>/<doctor_code>', methods=['PUT'])
@api_method(hook=hook)
def api_doctor_save(api_version, organization_code=None, doctor_code=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = DoctorXForm(api_version, create)
    xform.validate(data)
    xform.init_and_check_params(organization_code, doctor_code, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/doctor/<organization_code>/<doctor_code>', methods=['DELETE'])
@api_method(hook=hook)
def api_doctor_delete(api_version, organization_code=None, doctor_code=None):
    xform = DoctorXForm(api_version, False)
    xform.init_and_check_params(organization_code, doctor_code)
    xform.delete_target_obj()
    xform.store()
