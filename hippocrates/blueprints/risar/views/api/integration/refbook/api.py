# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import RefbookXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/refbook.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_refbook_schema(api_version):
    return RefbookXForm.get_schema(api_version)


# @module.route('/api/integration/<int:api_version>/reference_books/<refbook_code>/<item_code>')
# @api_method(hook=hook)
# def api_refbook_get(api_version, refbook_code):
#     xform = RefbookXForm(api_version)
#     xform.init_and_check_params(refbook_code)
#     return xform.as_json()


@module.route('/api/integration/<int:api_version>/reference_books/<refbook_code>', methods=['POST'])
@module.route('/api/integration/<int:api_version>/reference_books/<refbook_code>/<item_code>', methods=['PUT'])
@api_method(hook=hook)
def api_refbook_save(api_version, refbook_code, item_code=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = RefbookXForm(api_version, create)
    xform.validate(data)
    xform.init_and_check_params(refbook_code, item_code, data)
    xform.update_target_obj(data)
    xform.store()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/reference_books/<refbook_code>/<item_code>', methods=['DELETE'])
@api_method(hook=hook)
def api_refbook_delete(api_version, refbook_code, item_code=None):
    xform = RefbookXForm(api_version, False)
    xform.init_and_check_params(refbook_code, item_code)
    xform.delete_target_obj()
    xform.store()
