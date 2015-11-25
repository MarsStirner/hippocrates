# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from blueprints.accounting.lib.contract import ContragentController
from blueprints.accounting.lib.represent import ContragentRepr


@module.route('/api/0/contragent/list/', methods=['GET', 'POST'])
@api_method
def api_0_contragent_list():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    ca_ctrl = ContragentController()
    data = ca_ctrl.get_listed_data(args)
    return ContragentRepr().represent_listed_contragents(data)
