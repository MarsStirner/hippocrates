# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.pricelist import PriceListController
from blueprints.accounting.lib.represent import PriceListRepr


@module.route('/api/0/pricelist/list/', methods=['GET', 'POST'])
@api_method
def api_0_pricelist_list():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    ca_ctrl = PriceListController()
    data = ca_ctrl.get_listed_data(args)
    return PriceListRepr().represent_listed_pricelists(data)
