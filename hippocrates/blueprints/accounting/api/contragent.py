# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int
from blueprints.accounting.lib.contract import ContragentController
from blueprints.accounting.lib.represent import ContragentRepr


@module.route('/api/0/contragent/')
@module.route('/api/0/contragent/<int:contragent_id>')
@api_method
def api_0_contragent_get(contragent_id=None):
    # args = request.args.to_dict()
    # get_new = safe_bool(args.get('new', False))
    #
    # con_ctrl = ContractController()
    # if get_new:
    #     contract = con_ctrl.get_new_contract(args)
    # elif contract_id:
    #     contract = con_ctrl.get_contract(contract_id)
    # else:
    #     raise ApiException(404, u'`contract_id` required')
    # return ContractRepr().represent_contract_full(contract)
    return


@module.route('/api/0/contragent/list/', methods=['GET', 'POST'])
@api_method
def api_0_contragent_list():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    ca_ctrl = ContragentController()
    data = ca_ctrl.get_listed_data(args)
    return ContragentRepr().represent_listed_contragents(data)
