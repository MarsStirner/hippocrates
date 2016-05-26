# -*- coding: utf-8 -*-
import os

from flask import url_for

from nemesis.app import app
from nemesis.lib.frontend import frontend_config, uf_placeholders
from hippocrates.usagicompat import HippoUsagiClient
from version import version as app_version

__author__ = 'viruzzz-kun'

usagi = HippoUsagiClient(app.wsgi_app, os.getenv('TSUKINO_USAGI_URL', 'http://127.0.0.1:5900'), 'hippo')
app.wsgi_app = usagi.app
usagi()


@app.context_processor
def general_menu():
    from nemesis.lib.user import UserProfileManager
    menu_items = [dict(
        link='index',
        title=u'Главная страница',
        homepage=True,
        visible=(UserProfileManager.has_ui_doctor() or UserProfileManager.has_ui_registrator()),
        icon='glyphicon glyphicon-home'
    ), dict(
        link='patients.index',
        title=u'Обслуживание пациентов',
        visible=(UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_registrator_cut()),
        icon='fa fa-users'
    ), dict(
        link='schedule.person_schedule_monthview',
        title=u'Формирование графика',
        visible=(UserProfileManager.has_ui_registrator()),
        icon='fa fa-user-md'
    ), dict(
        link='schedule.index',
        title=u'График работы',
        visible=(UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_doctor()),
        icon='fa fa-calendar'
    ), dict(
        link='schedule.doctor_schedule_day',
        title=u'Приём пациентов',
        visible=(UserProfileManager.has_ui_doctor()),
        icon='fa fa-stethoscope'
    ), dict(
        link='patients.search',
        title=u'Поиск пациентов',
        visible=(UserProfileManager.has_ui_doctor()),
        icon='fa fa-search'
    ), dict(
        link='event.get_events',
        title=u'Обращения',
        visible=(UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_doctor()),
        icon='fa fa-medkit'
    ), dict(
        link='accounting.cashbook_html',
        title=u'Приём платежей',
        visible=UserProfileManager.has_ui_cashier(),
        icon='fa fa-calculator'
    ), dict(
        link='anareports.index_html',
        title=u'Аналитические отчёты',
        visible=True,
        icon='fa fa-bar-chart'
    ), dict(
        link='biomaterials.index_html',
        title=u'Биоматериалы',
        visible=UserProfileManager.has_ui_nurse(),
        icon='fa fa-eyedropper'
    )]
    return dict(main_menu=menu_items)


@app.context_processor
def app_enum():
    return {
        'app_version': app_version,
    }


@frontend_config
def fc_urls():
    """
    Специфическая конфигурация фронтенда Hippocrates
    :return: configuration dict
    """
    return {
        'url': {
            'doctor_to_assist': url_for("doctor_to_assist"),
            'api_person_get': url_for("schedule.api_person_get"),
            'api_patient_file_attach': url_for("patients.api_patient_file_attach"),
            'api_patient_file_attach_save': url_for("patients.api_patient_file_attach_save"),
            'api_patient_file_attach_delete': url_for("patients.api_patient_file_attach_delete"),
            'api_event_actions': url_for("event.api_event_actions"),
            'api_user_mail_summary': url_for("useraccount.api_mail_summary"),
            'api_user_mail': url_for("useraccount.api_mail_get") + '{0}',
            'api_user_mail_alter': url_for("useraccount.api_mail_mark") + '{0}/{1}',
            'api_subscription': url_for("useraccount.api_subscription") + '{0}',
            # accounting
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
            'api_pricelist_list': url_for('accounting.api_0_pricelist_list'),
            'api_service_search': url_for('accounting.api_0_service_search'),
            'api_service_get': url_for('accounting.api_0_service_get'),
            'api_service_list_save': url_for('accounting.api_0_service_list_save'),
            'api_service_list': url_for('accounting.api_0_service_list'),
            'api_service_delete': url_for('accounting.api_0_service_delete'),
            'api_service_refresh_subservices': url_for('accounting.api_0_service_refresh_subservices'),
            'api_service_at_price_get': url_for('accounting.api_0_service_at_price_get'),
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
        }
    }

if __name__ == "__main__":
    app.run(port=app.config.get('SERVER_PORT', 6600))
