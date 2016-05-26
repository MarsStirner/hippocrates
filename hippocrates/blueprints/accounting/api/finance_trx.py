# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int, safe_date
from nemesis.lib.data_ctrl.accounting.finance_trx import FinanceTrxController
from nemesis.lib.data_ctrl.accounting.utils import get_finance_trx_type
from hippocrates.blueprints.accounting.lib.represent import FinanceTrxRepr, ContragentRepr, InvoiceRepr


@module.route('/api/0/finance_transaction/')
@api_method
def api_0_finance_transaction_get():
    args = request.args.to_dict()
    get_new = safe_bool(args.get('new', False))

    trx_ctrl = FinanceTrxController()
    if not get_new:
        raise NotImplementedError()
    trx = trx_ctrl.get_new_trx(args)
    return FinanceTrxRepr.represent_finance_trx(trx)


@module.route('/api/0/finance_transaction/invoice/')
@api_method
def api_0_finance_transaction_invoice_get():
    args = request.args.to_dict()
    get_new = safe_bool(args.get('new', False))

    trx_ctrl = FinanceTrxController()
    if not get_new:
        raise NotImplementedError()
    trxes = trx_ctrl.get_new_invoice_trxes(args)
    return FinanceTrxRepr.represent_finance_trx_invoice(trxes)


@module.route('/api/0/finance_transaction/make/', methods=['POST'])
@module.route('/api/0/finance_transaction/make/<trx_type_code>/', methods=['POST'])
@api_method
def api_0_finance_transaction_make(trx_type_code=None):
    trx_type = get_finance_trx_type(trx_type_code)
    if trx_type is None:
        raise ApiException(404, u'Unknown `trx_type_code`')
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    trx_ctrl = FinanceTrxController()
    trx = trx_ctrl.make_trx(trx_type, args)
    trx_ctrl.store(trx)
    payer = trx.contragent
    return ContragentRepr().represent_contragent_payer(payer)


@module.route('/api/0/finance_transaction/invoice/make/', methods=['POST'])
@module.route('/api/0/finance_transaction/invoice/make/<trx_type_code>/', methods=['POST'])
@api_method
def api_0_finance_transaction_invoice_make(trx_type_code=None):
    trx_type = get_finance_trx_type(trx_type_code)
    if trx_type is None:
        raise ApiException(404, u'Unknown `trx_type_code`')
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    trx_ctrl = FinanceTrxController()
    trx_list = trx_ctrl.make_invoice_trxes(trx_type, args)
    trx_ctrl.store(*trx_list)
    invoice = trx_list[-1]
    return InvoiceRepr().represent_invoice_for_payment(invoice)