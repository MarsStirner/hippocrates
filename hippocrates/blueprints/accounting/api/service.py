# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from blueprints.accounting.lib.service import ServiceController
from blueprints.accounting.lib.represent import PriceListRepr


@module.route('/api/0/service/search/mis_action_kind/', methods=['GET', 'POST'])
@api_method
def api_0_service_search():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    service_ctrl = ServiceController()
    data = service_ctrl.search_mis_action_services(args)
    return data
    # return PriceListRepr().represent_listed_pricelists(data)
