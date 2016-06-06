# -*- coding: utf-8 -*-
import os
from hippocrates.usagicompat import HippoUsagiClient
from nemesis.app import app
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


if __name__ == "__main__":
    app.run(port=app.config.get('SERVER_PORT', 6600))
