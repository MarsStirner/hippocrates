# -*- coding: utf-8 -*-

import datetime

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int, safe_date
from blueprints.accounting.lib.contract import ContractController
from blueprints.accounting.lib.represent import ContractRepr


@module.route('/api/0/contract/')
@module.route('/api/0/contract/<int:contract_id>')
@api_method
def api_0_contract_get(contract_id=None):
    args = request.args.to_dict()
    get_new = safe_bool(args.get('new', False))

    con_ctrl = ContractController()
    if get_new:
        contract = con_ctrl.get_new_contract(args)
    elif contract_id:
        contract = con_ctrl.get_contract(contract_id)
    else:
        raise ApiException(404, u'`contract_id` required')
    return ContractRepr().represent_contract_full(contract)


@module.route('/api/0/contract/', methods=['PUT'])
@module.route('/api/0/contract/<int:contract_id>', methods=['POST'])
@api_method
def api_0_contract_save(contract_id=None):
    json_data = request.get_json()

    con_ctrl = ContractController()
    if not contract_id:
        contract = con_ctrl.get_new_contract()
        contract = con_ctrl.update_contract(contract, json_data)
        con_ctrl.store(contract)
    elif contract_id:
        contract = con_ctrl.get_contract(contract_id)
        if not contract:
            raise ApiException(404, u'Не найден Contract с id = '.format(contract_id))
        contract = con_ctrl.update_contract(contract, json_data)
        con_ctrl.store(contract)
    else:
        raise ApiException(404, u'`contract_id` required')
    return ContractRepr().represent_contract_full(contract)


@module.route('/api/0/contract/list/', methods=['GET', 'POST'])
@api_method
def api_0_contract_list():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    paginate = safe_bool(args.get('paginate', True))
    con_ctrl = ContractController()
    if paginate:
        data = con_ctrl.get_paginated_data(args)
        return ContractRepr().represent_paginated_contracts(data)
    else:
        data = con_ctrl.get_listed_data(args)
        return ContractRepr().represent_listed_contracts(data)


@module.route('/api/0/contract/', methods=['DELETE'])
@module.route('/api/0/contract/<int:contract_id>', methods=['DELETE'])
@api_method
def api_0_contract_delete(contract_id=None):
    if not contract_id:
        raise ApiException(404, u'`contract_id` required')
    con_ctrl = ContractController()
    contract = con_ctrl.get_contract(contract_id)
    con_ctrl.delete_contract(contract)
    con_ctrl.store(contract)
    return True


@module.route('/api/0/contract/list/available')
@api_method
def api_0_contract_get_available():
    client_id = safe_int(request.args.get('client_id'))
    if not client_id:
        raise ApiException(400, '`client_id` argument required')
    finance_id = safe_int(request.args.get('finance_id'))
    if not finance_id:
        raise ApiException(400, '`finance_id` argument required')
    set_date = safe_date(request.args.get('event_set_date')) or datetime.date.today()
    con_ctrl = ContractController()
    data = con_ctrl.get_avalable_contracts(client_id, finance_id, set_date)
    return ContractRepr().represent_listed_contracts(data)
