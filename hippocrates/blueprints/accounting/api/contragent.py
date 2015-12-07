# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.contract import ContragentController
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


@module.route('/api/0/contragent/search/payer/', methods=['GET', 'POST'])
@api_method
def api_0_contragent_search_payer():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    ca_ctrl = ContragentController()
    data = ca_ctrl.search_payers(args)
    return ContragentRepr().represent_listed_contragents_payers(data)


@module.route('/api/0/contragent/payer/')
@module.route('/api/0/contragent/payer/<int:payer_id>')
@api_method
def api_0_contragent_payer_get(payer_id=None):
    if not payer_id:
        raise ApiException(404, u'`payer_id` required')

    ca_ctrl = ContragentController()
    payer = ca_ctrl.get_payer(payer_id)
    return ContragentRepr().represent_contragent_payer_full(payer)