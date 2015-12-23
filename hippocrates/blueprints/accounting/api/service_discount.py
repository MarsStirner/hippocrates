# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.service_discount import ServiceDiscountController
from blueprints.accounting.lib.represent import ServiceDiscountRepr


@module.route('/api/0/service_discount/list/', methods=['GET', 'POST'])
@api_method
def api_0_service_discount_list():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    sd_ctrl = ServiceDiscountController()
    data = sd_ctrl.get_listed_data(args)
    return ServiceDiscountRepr.represent_listed_discounts(data)
