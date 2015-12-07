# -*- coding: utf-8 -*-

from nemesis.models.enums import Gender, ContragentType
from nemesis.lib.utils import format_date, safe_double, safe_decimal, format_money
from nemesis.lib.data_ctrl.accounting.utils import get_contragent_type, check_invoice_closed
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from nemesis.lib.data_ctrl.accounting.contract import ContragentController


class ContractRepr(object):

    def __init__(self):
        self.ca_repr = ContragentRepr()
        self.contingent_repr = ContingentRepr()
        self.pricelist_repr = PriceListRepr()

    def represent_contract_full(self, contract):
        if not contract:
            return None
        data = self.represent_contract(contract)
        data.update({
            'recipient': self.ca_repr.represent_contragent(contract.recipient),
            'payer': self.ca_repr.represent_contragent(contract.payer),
            'contingent_list': [
                self.contingent_repr.represent_contingent(cont)
                for cont in contract.contingent_list if cont.deleted == 0  # TODO: think about selection
            ],
            'pricelist_list': [
                self.pricelist_repr.represent_pricelist_short(pl)
                for pl in contract.pricelist_list if pl.deleted == 0  # TODO: think about selection
            ],
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            }
        })
        return data

    def represent_contract(self, contract):
        return {
            'id': contract.id,
            'number': contract.number,
            'date': contract.date,
            'beg_date': contract.begDate,
            'end_date': contract.endDate,
            'finance': contract.finance,
            'contract_type': contract.contract_type,
            'resolution': contract.resolution,
            'deleted': contract.deleted,
            'draft': contract.draft,
        }

    def represent_contract_for_payer(self, contract):
        if not contract:
            return None
        data = self.represent_contract(contract)
        data.update({
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            }
        })
        return data

    def represent_contract_for_invoice(self, contract):
        data = self.represent_contract(contract)
        data.update({
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            },
            'payer': self.ca_repr.represent_contragent(contract.payer),
        })
        return data

    def make_full_description(self, contract):
        return u'''\
№{0} от {1}. {2}. с {3} по {4}'''.format(
            contract.number, format_date(contract.date), contract.resolution or '', format_date(contract.begDate),
            format_date(contract.endDate)
        )

    def make_short_description(self, contract):
        return u'№{0} от {1}. {2}'.format(contract.number, format_date(contract.date), contract.resolution or '')

    def represent_paginated_contracts(self, paginated_data):
        return {
            'count': paginated_data.total,
            'total_pages': paginated_data.pages,
            'contract_list': [
                self.represent_contract_full(contract) for contract in paginated_data.items
            ]
        }

    def represent_listed_contracts(self, contract_list):
        return [
            self.represent_contract_full(contract) for contract in contract_list
        ]


class ContragentRepr(object):

    def __init__(self):
        self.ca_ctrl = ContragentController()

    def represent_contragent(self, contragent):
        if not contragent:
            return None
        ca_type = get_contragent_type(contragent)
        return {
            'id': contragent.id,
            'client': self.represent_ca_client(contragent.client),
            'org': self.represent_ca_org(contragent.org),
            'ca_type': ca_type,
            'ca_type_code': unicode(ca_type),
            'short_descr': self.make_ca_short_descr(contragent),
            'full_descr': self.make_ca_full_descr(contragent)
        }

    def represent_contragent_payer(self, contragent):
        if not contragent:
            return None
        data = self.represent_contragent(contragent)
        contract_repr = ContractRepr()
        data['contract_list'] = [
            contract_repr.represent_contract_for_payer(contract)
            for contract in contragent.payer_contract_list
        ]
        return data

    def represent_contragent_payer_full(self, contragent):
        data = self.represent_contragent(contragent)
        data['balance'] = format_money(self.ca_ctrl.get_payer_balance(contragent))
        return data

    def make_ca_short_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.shortName
        elif ca_type.value == ContragentType.individual[0]:
            return contragent.client.nameText

    def make_ca_full_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.fullName
        elif ca_type.value == ContragentType.individual[0]:
            return u'{0}, {1}, {2}'.format(
                contragent.client.nameText,
                Gender.getName(contragent.client.sex),
                format_date(contragent.client.birthDate)
            )

    def represent_ca_client(self, client):
        if client is None:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }

    def represent_ca_org(self, org):
        if org is None:
            return None
        return {
            'id': org.id,
            'short_name': org.shortName,
            'full_name': org.fullName
        }

    def represent_listed_contragents(self, ca_list):
        return [
            self.represent_contragent(contragent) for contragent in ca_list
        ]

    def represent_listed_contragents_payers(self, ca_list):
        return [
            self.represent_contragent_payer(contragent) for contragent in ca_list
        ]


class ContingentRepr(object):

    def represent_contingent(self, contingent):
        return {
            'id': contingent.id,
            'contract_id': contingent.contract_id,
            'client': self.represent_client(contingent.client),
            'deleted': contingent.deleted
        }

    def represent_client(self, client):
        if not client:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }


class PriceListRepr(object):

    def represent_pricelist(self, pl):
        return {
            'id': pl.id,
            'code': pl.code,
            'name': pl.name,
            'deleted': pl.deleted,
            'finance': pl.finance,
            'beg_date': pl.begDate,
            'end_date': pl.endDate
        }

    def represent_pricelist_short(self, pl):
        data = self.represent_pricelist(pl)
        data['description'] = {
            'short': self.make_short_description(pl),
        }
        return data

    def make_short_description(self, pl):
        return u'{0} ({1}), с {1} по {2}'.format(pl.name, pl.finance.name,
                                                 format_date(pl.begDate), format_date(pl.endDate))

    def represent_listed_pricelists(self, pl_list):
        return [
            self.represent_pricelist_short(pl) for pl in pl_list
        ]


class ServiceRepr(object):

    def __init__(self):
        self.service_ctrl = ServiceController()

    def represent_mis_action_service_search_result(self, service_data):
        return {
            'service': {
                'price_list_item_id': service_data['price_list_item_id'],
                'service_id': service_data['service_id'],
                'service_code': service_data['service_code'],
                'service_name': service_data['service_name'],
                'price': format_money(service_data['price'], scale=0),
                'amount': service_data['amount'],
                'sum': format_money(service_data['sum'], scale=0),
            },
            'action': {
                'action_type_id': service_data['action_type_id'],
                'at_code': service_data['at_code'],
                'at_name': service_data['at_name'],
            }
        }

    def represent_search_result_mis_action_services(self, service_list):
        return [
            self.represent_mis_action_service_search_result(service) for service in service_list
        ]

    def represent_service(self, service):
        return {
            'id': service.id,
            'price_list_item_id': service.priceListItem_id,
            'amount': service.amount,
            'price': service.price_list_item.price,
            'service_id': service.price_list_item.service_id,
            'deleted': service.deleted,
            'sum': format_money(service.price_list_item.price * safe_decimal(service.amount)),
            'service_code': service.price_list_item.serviceCodeOW,
            'service_name': service.price_list_item.serviceNameOW,
            'in_invoice': self.service_ctrl.check_service_in_invoice(service)
        }

    def represent_service_action(self, action):
        return {
            'id': action.id,
            'action_type_id': action.actionType_id,
            'at_code': action.actionType.code,
            'at_name': action.actionType.name,
        }

    def represent_grouped_event_services(self, data):
        for service_group in data['grouped']:
            for idx, service in enumerate(service_group['sg_list']):
                service_group['sg_list'][idx] = {
                    'service': self.represent_service(service['service']),
                    'action': self.represent_service_action(service['action'])
                }
        return data


class InvoiceRepr(object):

    def __init__(self):
        self.service_repr = ServiceRepr()

    def represent_invoice_full(self, invoice):
        if not invoice:
            return None
        data = self.represent_invoice(invoice)
        data.update({
            'total_sum': format_money(invoice.total_sum),
            'item_list': [
                self.represent_invoice_item(item)
                for item in invoice.item_list
            ],
            'description': {
                'full': self.make_full_description(invoice),
            },
            'closed': check_invoice_closed(invoice)
        })
        return data

    def represent_invoice_for_payment(self, invoice):
        data = self.represent_invoice(invoice)
        cont_repr = ContractRepr()
        data.update({
            'total_sum': format_money(invoice.total_sum),
            'contract': cont_repr.represent_contract_for_invoice(invoice.contract),
            'description': {
                'full': self.make_full_description(invoice),
            },
            'closed': check_invoice_closed(invoice)
        })
        return data

    def represent_invoice(self, invoice):
        return {
            'id': invoice.id,
            'contract_id': invoice.contract_id,
            'set_date': invoice.setDate,
            'settle_date': invoice.settleDate,
            'number': invoice.number,
            'deed_number': invoice.deedNumber,
            'deleted': invoice.deleted,
            'note': invoice.note,
            'draft': invoice.draft,
        }

    def make_full_description(self, invoice):
        return u'''\
№{0} от {1}.{2} Позиций: {3} шт.'''.format(
            invoice.number or '',
            format_date(invoice.setDate),
            u' Дата погашения {0}.'.format(format_date(invoice.settleDate)) if invoice.settleDate else u'',
            len(invoice.item_list)
        )

    def represent_invoice_item(self, item):
        return {
            'id': item.id,
            'invoice_id': item.invoice_id,
            'service_id': item.concreteService_id,
            'service': self.service_repr.represent_service(item.service),
            'price': format_money(item.price, scale=0),
            'amount': item.amount,
            'sum': format_money(item.sum),
            'deleted': item.deleted
        }

    def represent_listed_invoices(self, invoice_list):
        return [
            self.represent_invoice_full(invoice) for invoice in invoice_list
        ]

    def represent_listed_invoices_for_payment(self, invoice_list):
        return [
            self.represent_invoice_for_payment(invoice) for invoice in invoice_list
        ]


class FinanceTrxRepr(object):

    @staticmethod
    def represent_finance_trx(trx):
        return {
            'id': trx.id,
            'trx_datetime': trx.trxDatetime,
            'trx_type': trx.trx_type,
            'contragent_id': trx.contragent_id,
            'invoice_id': trx.invoice_id,
            'pay_type': trx.pay_type,
            'sum': trx.sum
        }

    @staticmethod
    def represent_finance_trx_invoice(trxes):
        return {
            'payer_balance_trx': FinanceTrxRepr.represent_finance_trx(trxes['payer_balance_trx']),
            'invoice_trx': FinanceTrxRepr.represent_finance_trx(trxes['invoice_trx'])
        }