# -*- coding: utf-8 -*-

from flask import request
from nemesis.models.client import Client

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data_ctrl.accounting.contract import ContragentController
from nemesis.lib.data_ctrl.accounting.represent import ContragentRepr


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


@module.route('/api/0/client/')
@module.route('/api/0/client/<int:client_id>')
@api_method
def api_0_contragent_client_get(client_id=None):
    client = Client.query.get(client_id)
    if not client:
        raise ApiException(404, u'Client not found')
    return ContragentRepr().represent_ca_client(client)


@module.route('/api/0/contragent/check_duplicate', methods=['POST'])
@api_method
def api_0_contragent_check_duplicate():
    data = request.get_json()
    if not data:
        raise ApiException(400, 'no request data')
    ca_ctrl = ContragentController()
    res = ca_ctrl.check_duplicate(data)
    res['existing'] = ContragentRepr().represent_contragent(res['existing'])
    return res
