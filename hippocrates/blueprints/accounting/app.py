# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config, uf_placeholders
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )


from html_views import *
from api import *
from api_json import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'accounting': {
                'event_make_payment': url_for('accounting.api_event_make_payment'),
                'get_event_payments': url_for('accounting.api_get_event_payments'),
                'html_contract_list': url_for('accounting.html_contract_list'),
                'api_contragent_client_get': url_for('accounting.api_0_contragent_client_get'),
                'api_contract_get': url_for('accounting.api_0_contract_get'),
                'api_contract_list': url_for('accounting.api_0_contract_list'),
                'api_contract_save': url_for('accounting.api_0_contract_save'),
                'api_contract_delete': url_for('accounting.api_0_contract_delete'),
                'api_contract_get_available': url_for('accounting.api_0_contract_get_available'),
                'api_contragent_list': url_for('accounting.api_0_contragent_list'),
                'api_contragent_payer_get': url_for('accounting.api_0_contragent_payer_get'),
                'api_contingent_get': url_for('accounting.api_0_contingent_get'),
                'api_contragent_search_payer': url_for('accounting.api_0_contragent_search_payer'),
                'api_contragent_check_duplicate': url_for('accounting.api_0_contragent_check_duplicate'),
                'api_pricelist_list': url_for('accounting.api_0_pricelist_list'),
                'api_service_search': url_for('accounting.api_0_service_search'),
                'api_service_get': url_for('accounting.api_0_service_get'),
                'api_service_list_save': url_for('accounting.api_0_service_list_save'),
                'api_service_list': url_for('accounting.api_0_service_list'),
                'api_service_delete': url_for('accounting.api_0_service_delete'),
                'api_service_refresh_subservices': url_for('accounting.api_0_service_refresh_subservices'),
                'api_service_at_price_get': url_for('accounting.api_0_service_at_price_get'),
                'api_service_not_in_invoice_get': url_for('accounting.api_0_service_not_in_invoice_get'),
                'api_invoice_get': url_for('accounting.api_0_invoice_get'),
                'api_invoice_save': url_for('accounting.api_0_invoice_save'),
                'api_invoice_delete': url_for('accounting.api_0_invoice_delete'),
                'api_invoice_search': url_for('accounting.api_0_invoice_search'),
                'api_invoice_calc_sum': url_for('accounting.api_0_invoice_calc_sum'),
                'api_finance_transaction_get': url_for('accounting.api_0_finance_transaction_get'),
                'api_finance_transaction_make': url_for('accounting.api_0_finance_transaction_make'),
                'api_finance_transaction_invoice_get': url_for('accounting.api_0_finance_transaction_invoice_get'),
                'api_finance_transaction_invoice_make': url_for('accounting.api_0_finance_transaction_invoice_make'),
                'api_service_discount_list': url_for('accounting.api_0_service_discount_list'),
                'api_invoice_refund_get': uf_placeholders('accounting.api_0_invoice_refund_get', ['invoice_id']),
                'api_invoice_refund_save': uf_placeholders('accounting.api_0_invoice_refund_save', ['invoice_id']),
                'api_invoice_refund_delete': uf_placeholders('accounting.api_0_invoice_refund_delete', ['invoice_id']),
                'api_invoice_refund_process': uf_placeholders('accounting.api_0_invoice_refund_process', ['invoice_id']),
            },
        }
    }
