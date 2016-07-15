# -*- coding: utf-8 -*-

from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int, safe_date
from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
from hippocrates.blueprints.accounting.lib.represent import InvoiceRepr


@module.route('/api/0/invoice/', methods=['GET', 'POST'])
@module.route('/api/0/invoice/<int:invoice_id>')
@api_method
def api_0_invoice_get(invoice_id=None):
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)
    get_new = safe_bool(args.get('new', False))

    invoice_ctrl = InvoiceController()
    with invoice_ctrl.session.no_autoflush:
        if get_new:
            invoice = invoice_ctrl.get_new_invoice(args)
        elif invoice_id:
            invoice = invoice_ctrl.get_invoice(invoice_id)
        else:
            raise ApiException(404, u'`invoice_id` required')
        return InvoiceRepr().represent_invoice_full(invoice)


@module.route('/api/0/invoice/', methods=['PUT'])
@module.route('/api/0/invoice/<int:invoice_id>', methods=['POST'])
@api_method
def api_0_invoice_save(invoice_id=None):
    json_data = request.get_json()

    invoice_ctrl = InvoiceController()
    with invoice_ctrl.session.no_autoflush:
        if not invoice_id:
            invoice = invoice_ctrl.get_new_invoice()
            invoice = invoice_ctrl.update_invoice(invoice, json_data)
            invoice_ctrl.store(*invoice.get_all_entities())
        elif invoice_id:
            invoice = invoice_ctrl.get_invoice(invoice_id)
            if not invoice:
                raise ApiException(404, u'Не найден Invoice с id = {0}'.format(invoice_id))
            invoice = invoice_ctrl.update_invoice(invoice, json_data)
            invoice_ctrl.store(invoice)
        else:
            raise ApiException(404, u'`invoice_id` required')
        return InvoiceRepr().represent_invoice_full(invoice)


@module.route('/api/0/invoice/', methods=['DELETE'])
@module.route('/api/0/invoice/<int:invoice_id>', methods=['DELETE'])
@api_method
def api_0_invoice_delete(invoice_id=None):
    if not invoice_id:
        raise ApiException(404, u'`invoice_id` required')
    invoice_ctrl = InvoiceController()
    invoice = invoice_ctrl.get_invoice(invoice_id)
    invoice_ctrl.delete_invoice(invoice)
    invoice_ctrl.store(invoice)
    return True


@module.route('/api/0/invoice/search/', methods=['GET', 'POST'])
@api_method
def api_0_invoice_search():
    args = request.args.to_dict()
    if request.json:
        args.update(request.json)

    invoice_ctrl = InvoiceController()
    data = invoice_ctrl.search_invoices(args)
    return InvoiceRepr().represent_listed_invoices_for_payment(data)


@module.route('/api/0/invoice/calc_sum/', methods=['POST'])
@module.route('/api/0/invoice/calc_sum/<int:invoice_id>', methods=['POST'])
@api_method
def api_0_invoice_calc_sum(invoice_id=None):
    json_data = request.get_json()

    invoice_ctrl = InvoiceController()
    with invoice_ctrl.session.no_autoflush:
        if not invoice_id:
            invoice = invoice_ctrl.get_new_invoice()
            invoice = invoice_ctrl.update_invoice(invoice, json_data)
        elif invoice_id:
            invoice = invoice_ctrl.get_invoice(invoice_id)
            if not invoice:
                raise ApiException(404, u'Не найден Invoice с id = {0}'.format(invoice_id))
            invoice = invoice_ctrl.update_invoice(invoice, json_data)
        else:
            raise ApiException(404, u'`invoice_id` required')
        return InvoiceRepr().represent_invoice_full(invoice)
