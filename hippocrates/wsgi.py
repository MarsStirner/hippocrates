# -*- coding: utf-8 -*-
import os
from flask import url_for
from nemesis.app import app, bootstrap_app
import config
from nemesis.lib.frontend import frontend_config
from blueprints.risar.risar_version import version as risar_version

__author__ = 'viruzzz-kun'

app.config.from_object(config)
bootstrap_app(os.path.join(os.path.dirname(__file__), 'templates'))


@app.context_processor
def general_menu():
    from nemesis.lib.user import UserProfileManager
    menu_items = [dict(
        link='risar.index_html',
        title=u'Рабочий стол',
        visible=True,
        icon='fa fa-home'
    ), dict(
        link='risar.html_search',
        title=u'Расширенный поиск',
        visible=True,
        icon='fa fa-search'
    ), dict(
        link='risar.html_errands_list',
        title=u'Поручения',
        visible=True,
        icon='fa fa-flag-o'
    ), dict(
        external_link=app.config['CAESAR_URL'],
        title=u'Администрирование системы',
        visible=UserProfileManager.has_ui_admin(),
        icon='fa fa-cog'
    ), dict(
        link='risar.html_mis',
        title=u'МИС',
        visible=True,
        icon='fa fa-medkit'
    ), dict(
        link='anareports.index_html',
        title=u'Аналитические отчёты',
        visible=True,
        icon='fa fa-bar-chart'
    )]
    return dict(main_menu=menu_items)


@app.context_processor
def app_enum():
    return {
        'app_version': risar_version,
    }


from blueprints.accounting.app import module as accounting_module
from blueprints.anareports.app import module as anareports_module
from blueprints.biomaterials.app import module as biomaterials_module
from blueprints.event.app import module as event_module
from blueprints.patients.app import module as patients_module
from blueprints.schedule.app import module as schedule_module
from blueprints.actions.app import module as actions_module
from blueprints.risar.app import module as risar_module
from blueprints.useraccount.app import module as useraccount_module

app.register_blueprint(accounting_module, url_prefix='/accounting')
app.register_blueprint(anareports_module, url_prefix='/anareports')
app.register_blueprint(biomaterials_module, url_prefix='/biomaterials')
app.register_blueprint(event_module, url_prefix='/event')
app.register_blueprint(patients_module, url_prefix='/patients')
app.register_blueprint(schedule_module, url_prefix='/schedule')
app.register_blueprint(actions_module, url_prefix='/actions')
app.register_blueprint(risar_module, url_prefix='/risar')
app.register_blueprint(useraccount_module, url_prefix='/user')


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
            'api_service_list_save': url_for('accounting.api_0_service_list_save'),
            'api_service_list_grouped': url_for('accounting.api_0_service_list_grouped'),
            'api_service_delete': url_for('accounting.api_0_service_delete'),
            'api_invoice_get': url_for('accounting.api_0_invoice_get'),
            'api_invoice_save': url_for('accounting.api_0_invoice_save'),
            'api_invoice_delete': url_for('accounting.api_0_invoice_delete'),
            'api_invoice_search': url_for('accounting.api_0_invoice_search'),
            'api_invoice_calc_sum': url_for('accounting.api_0_invoice_calc_sum'),
            'api_finance_transaction_get': url_for('accounting.api_0_finance_transaction_get'),
            'api_finance_transaction_make': url_for('accounting.api_0_finance_transaction_make'),
            'api_finance_transaction_invoice_get': url_for('accounting.api_0_finance_transaction_invoice_get'),
            'api_finance_transaction_invoice_make': url_for('accounting.api_0_finance_transaction_invoice_make'),
            'api_service_discount_list': url_for('accounting.api_0_service_discount_list')
        }
    }

if __name__ == "__main__":
    app.run(port=app.config['SERVER_PORT'])
