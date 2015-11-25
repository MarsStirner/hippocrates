# -*- coding: utf-8 -*-
import os
from flask import url_for
from nemesis.app import app, bootstrap_app
import config
from nemesis.lib.frontend import frontend_config
from version import version as app_version

__author__ = 'viruzzz-kun'

app.config.from_object(config)
bootstrap_app(os.path.join(os.path.dirname(__file__), 'templates'))


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
        title=u'Расчет пациентов',
        visible=UserProfileManager.has_ui_cashier(),
        icon='fa fa-calculator'
    ), dict(
        link='accounting.cashbook_operations',
        title=u'Журнал кассовых операций',
        visible=UserProfileManager.has_ui_cashier(),
        icon='fa fa-book'
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
        'app_version': app_version,
    }


from blueprints.accounting.app import module as accounting_module
from blueprints.anareports.app import module as anareports_module
from blueprints.event.app import module as event_module
from blueprints.patients.app import module as patients_module
from blueprints.schedule.app import module as schedule_module
from blueprints.actions.app import module as actions_module
from blueprints.useraccount.app import module as useraccount_module

app.register_blueprint(accounting_module, url_prefix='/accounting')
app.register_blueprint(anareports_module, url_prefix='/anareports')
app.register_blueprint(event_module, url_prefix='/event')
app.register_blueprint(patients_module, url_prefix='/patients')
app.register_blueprint(schedule_module, url_prefix='/schedule')
app.register_blueprint(actions_module, url_prefix='/actions')
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
            'api_contingent_get': url_for('accounting.api_0_contingent_get'),
            'api_pricelist_list': url_for('accounting.api_0_pricelist_list')
        }
    }

if __name__ == "__main__":
    app.run()
