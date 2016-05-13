# -*- coding: utf-8 -*-
import datetime

from flask import request
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.accounting import Invoice, FinanceTransaction, rbFinanceTransactionType, rbFinanceOperationType, \
    rbPayType
from nemesis.systemwide import db
from ..app import module
from ..lib.represent import InvoiceRepr

__author__ = 'viruzzz-kun'


def bail_out(exc):
    raise exc


__no_coordinated_exception = ApiException(404, u'Invoice has no coordinated refund requests')
__no_invoice_exception = ApiException(404, u'Invoice not found')


def find_invoice(invoice):
    """
    @type invoice: Invoice|int
    @type silently: bool
    @param invoice:
    @param silently:
    @return:
    @rtype: Invoice
    """
    if isinstance(invoice, int):
        invoice = Invoice.query.get(invoice)
    return invoice


@module.route('/api/0/invoice/<int:invoice_id>/refund', methods=['GET'])
@api_method
def api_0_invoice_refund_get(invoice_id):
    """
    Получение согласования на возврат по счёту
    @type invoice_id: int
    @param invoice_id: Invoice.id
    @return:
    """
    invoice = find_invoice(invoice_id) or bail_out(__no_invoice_exception)
    refund = invoice.coordinated_refund or bail_out(__no_coordinated_exception)
    return InvoiceRepr().represent_refund(refund)


@module.route('/api/0/invoice/<int:invoice_id>/refund', methods=['POST', 'PUT'])
@api_method
def api_0_invoice_refund_save(invoice_id):
    """
    Создание нового или редактирование имеющегося согласования на возврат по счёту

    Ожидает JSON с полем 'item_list', в котором будет список обычных пунктов счёта (нужны только id)

    @type invoice_id: int
    @param invoice_id: Invoice.id
    @return:
    """
    data = request.get_json()
    invoice = find_invoice(invoice_id) or bail_out(__no_invoice_exception)
    refund = invoice.coordinated_refund
    item_map = {
        item.id: item
        for item in invoice.item_list
    }
    item_id_list = [item['id'] for item in data['item_list']]
    if not refund:
        refund = Invoice()
        db.session.add(refund)
        refund.parent = invoice
        refund.contract = invoice.contract
        refund.setDate = datetime.date.today()
    else:
        for item in invoice.item_list:
            if item.refund == refund and item.id not in item_id_list:
                item.set_refund(None)

    for item_id in item_id_list:
        item = item_map[item_id]
        item.set_refund(refund)
    db.session.commit()
    return InvoiceRepr().represent_refund(refund)


@module.route('/api/0/invoice/<int:invoice_id>/refund', methods=['DELETE'])
@api_method
def api_0_invoice_refund_delete(invoice_id):
    """
    Отмена согласования на возврат по счёту
    @type invoice_id: int
    @param invoice_id: Invoice.id
    @return:
    """
    invoice = find_invoice(invoice_id) or bail_out(__no_invoice_exception)
    refund = invoice.coordinated_refund or bail_out(__no_coordinated_exception)
    refund.deleted = 1
    for item in refund.refund_items:
        item.set_refund(None, recursive=True)
    db.session.commit()


@module.route('/api/0/invoice/<int:invoice_id>/refund/process', methods=['POST'])
@api_method
def api_0_invoice_refund_process(invoice_id):
    """
    Процессинг возврата по счёту

    Ожидает JSON с полем 'pay_type', в котором будет запись из справочника rbPayType - как вернуть бабки клиенту

    @type invoice_id: int
    @param invoice_id: Invoice.id
    @return:
    """
    data = request.get_json()
    with db.session.no_autocommit:
        invoice = find_invoice(invoice_id) or bail_out(__no_invoice_exception)
        refund = invoice.coordinated_refund or bail_out(__no_coordinated_exception)

        trx_1 = FinanceTransaction()
        trx_2 = FinanceTransaction()
        db.session.add(trx_1)
        db.session.add(trx_2)

        # Кидаем со счёта на баланс
        trx_1.invoice = refund
        trx_1.contragent = invoice.contract.payer
        trx_1.trx_type = rbFinanceTransactionType.cache().by_code()['invoice']
        trx_1.operation_type = rbFinanceOperationType.cache().by_code()['invoice_cancel']
        trx_1.trxDatetime = datetime.datetime.now()
        trx_1.sum = refund.refund_sum

        # Вертаем с баланса клиенту
        trx_2.invoice = refund
        trx_2.contragent = invoice.contract.payer
        trx_2.trx_type = rbFinanceTransactionType.cache().by_code()['balance']
        trx_2.operation_type = rbFinanceOperationType.cache().by_code()['payer_balance_out']
        trx_2.pay_type = rbPayType.cache().by_code()[data['pay_type']['code']]
        trx_2.trxDatetime = datetime.datetime.now()
        trx_2.sum = refund.refund_sum

        refund.settleDate = datetime.date.today()

    db.session.commit()

