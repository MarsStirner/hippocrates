# -*- coding: utf-8 -*-
from application.app import app
from datetime import datetime
from application.lib.user import UserUtils, UserProfileManager
from version import version as _version, last_change_date


@app.context_processor
def copyright():
    return dict(copy_year=datetime.today().year)


@app.context_processor
def version():
    return dict(version=_version, change_date=last_change_date)


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
        visible=(UserProfileManager.has_ui_doctor() or UserProfileManager.has_ui_registrator())
    ), dict(
        link='patients.index',
        title=u'Обслуживание пациентов',
        visible=(not UserProfileManager.has_ui_doctor_stat() and (UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_registrator_cut()))
    ), dict(
        link='schedule.person_schedule_monthview',
        title=u'Формирование графика врача',
        visible=(not UserProfileManager.has_ui_doctor_stat() and UserProfileManager.has_ui_registrator())
    ), dict(
        link='schedule.index',
        title=u'График работы',
        visible=(not UserProfileManager.has_ui_doctor_stat() and UserProfileManager.has_ui_registrator())
    ), dict(
        link='schedule.doctor_schedule_day',
        title=u'Приём пациентов',
        visible=(not UserProfileManager.has_ui_doctor_stat() and UserProfileManager.has_ui_doctor())
    ), dict(
        link='patients.search',
        title=u'Поиск пациентов',
        visible=(not UserProfileManager.has_ui_doctor_stat() and UserProfileManager.has_ui_doctor())
    ), dict(
        link='event.get_events',
        title=u'Обращения',
        visible=(not UserProfileManager.has_ui_doctor_stat() and (UserProfileManager.has_ui_registrator() or UserProfileManager.has_ui_doctor()))
    ), dict(
        link='anareports.index_html',
        title=u'Аналитические отчёты',
        visible=True
    )]
    return dict(main_menu=menu_items)


@app.context_processor
def user_utils():
    return {
        'user_utils': UserUtils()
    }
