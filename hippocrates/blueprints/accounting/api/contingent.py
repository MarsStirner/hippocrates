# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int
from nemesis.lib.data_ctrl.accounting.contract import ContingentController
from blueprints.accounting.lib.represent import ContingentRepr


@module.route('/api/0/contract/contingent')
@module.route('/api/0/contract/contingent/<int:contingent_id>')
@api_method
def api_0_contingent_get(contingent_id=None):
    args = request.args.to_dict()
    get_new = safe_bool(args.get('new', False))

    con_ctrl = ContingentController()
    if get_new:
        contingent = con_ctrl.get_new_contingent(args)
    elif contingent_id:
        raise NotImplementedError()
    else:
        raise ApiException(404, u'`contingent_id` required')
    return ContingentRepr().represent_contingent(contingent)
