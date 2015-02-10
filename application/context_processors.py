# -*- coding: utf-8 -*-
from pytz import timezone
from application.app import app
from datetime import datetime
from application.lib.user import UserUtils, UserProfileManager
from version import version as _version, last_change_date

@app.context_processor
def copyright():
    return dict(copy_year=datetime.today().year)


@app.context_processor
def version():
    change_date = timezone(app.config['TIME_ZONE']).localize(last_change_date)
    return dict(version=_version, change_date=change_date)


@app.context_processor
def print_subsystem():
    ps_url = app.config['PRINT_SUBSYSTEM_URL'].rstrip('/')
    return {
        'print_subsystem_url': ps_url,
        'print_subsystem_templates': '%s/templates/' % ps_url,
        'print_subsystem_print_template': '%s/print_template' % ps_url,
    }


@app.context_processor
def general_menu():
    menu_items = [dict(
        link='index',
        title=u'Главная страница',
        homepage=True,
        visible=(not UserProfileManager.has_ui_registrator_cut())
    ), dict(
        link='patients.index',
        title=u'Обслуживание пациентов',
        visible=(UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_registrator_cut())
    ), dict(
        link='schedule.person_schedule_monthview',
        title=u'Формирование графика врача',
        visible=(UserProfileManager.has_ui_registrator())
    ), dict(
        link='schedule.index',
        title=u'График работы',
        visible=(UserProfileManager.has_ui_registrator())
    ), dict(
        link='schedule.doctor_schedule_day',
        title=u'Приём пациентов',
        visible=(UserProfileManager.has_ui_doctor())
    ), dict(
        link='patients.search',
        title=u'Поиск пациентов',
        visible=(UserProfileManager.has_ui_doctor())
    ), dict(
        link='event.get_events',
        title=u'Обращения',
        visible=(UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_doctor())
    ), dict(
        link='anareports.index_html',
        title=u'Аналитические отчёты',
        visible=True
    ), dict(
        link='accounting.cashbook_html',
        title=u'Расчет пациентов',
        visible=UserProfileManager.has_ui_cashier()
    ), dict(
        link='accounting.cashbook_operations',
        title=u'Журнал кассовых операций',
        visible=UserProfileManager.has_ui_cashier()
    )]
    return dict(main_menu=menu_items)


@app.context_processor
def user_utils():
    return {
        'user_utils': UserUtils(),
        'user_profiles_mng': UserProfileManager()
    }
