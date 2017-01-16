# -*- coding: utf-8 -*-
import blinker
from flask import request

from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_bool, safe_int, safe_date, parse_json
from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
from nemesis.lib.mq_integration.invoice import MQOpsInvoice, notify_invoice_changed
from hippocrates.blueprints.accounting.lib.represent import InvoiceRepr


@module.route('/api/0/invoice/')
@module.route('/api/0/invoice/<int:invoice_id>')
@api_method
def api_0_invoice_get(invoice_id=None):
    args = request.args.to_dict()
    if 'service_list' in args:
        args['service_list'] = request.args.getlist('service_list')
    if request.json:
        args.update(request.json)
    get_new = safe_bool(args.get('new', False))
    repr_type = args.get('repr_type')

    invoice_ctrl = InvoiceController()
    with invoice_ctrl.session.no_autoflush:
        if get_new:
            invoice = invoice_ctrl.get_new_invoice(args)
        elif invoice_id:
            invoice = invoice_ctrl.get_invoice(invoice_id)
        else:
            raise ApiException(404, u'`invoice_id` required')
        if repr_type == 'for_payment':
            return InvoiceRepr().represent_invoice_for_payment(invoice)
        else:
            return InvoiceRepr().represent_invoice_full(invoice)


@module.route('/api/0/invoice/', methods=['POST'])
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
            notify_invoice_changed(MQOpsInvoice.create, invoice)
        elif invoice_id:
            invoice = invoice_ctrl.get_invoice(invoice_id)
            if not invoice:
                raise ApiException(404, u'Не найден Invoice с id = {0}'.format(invoice_id))
            invoice = invoice_ctrl.update_invoice(invoice, json_data)
            invoice_ctrl.store(invoice)
            notify_invoice_changed(MQOpsInvoice.update, invoice)
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
    notify_invoice_changed(MQOpsInvoice.delete, invoice)
    return True


def on_event_deleted(sender, event_id, deleted_data=None):
    invoice_ctrl = InvoiceController()
    if deleted_data is not None:
        invoice_ids = deleted_data.get('invoices', [])
        invoice_list = invoice_ctrl.get_listed_data({'id_list': invoice_ids})
    else:
        invoice_list = []

    for invoice in invoice_list:
        notify_invoice_changed(MQOpsInvoice.delete, invoice)


blinker.signal('Event-deleted').connect(on_event_deleted)


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
