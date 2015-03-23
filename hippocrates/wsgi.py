# -*- coding: utf-8 -*-
import os
from nemesis.app import app, bootstrap_app
import config

__author__ = 'viruzzz-kun'

app.config.from_object(config)
bootstrap_app(os.path.join(os.path.dirname(__file__), 'templates'))


@app.context_processor
def general_menu():
    from flask.ext.login import current_user
    from nemesis.lib.user import UserProfileManager
    menu_items = [dict(
        link='index',
        title=u'Главная страница',
        homepage=True,
        visible=(UserProfileManager.has_ui_doctor() or UserProfileManager.has_ui_registrator())
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
        link='risar.index_html',
        title={
            'obstetrician': u'АРМ Акушера-гинеколога',
            'overseer1': u'АРМ Куратора 1 уровня',
            'overseer2': u'АРМ Куратора 2 уровня',
            'overseer3': u'АРМ Куратора 3 уровня',
            }.get(getattr(current_user, 'current_role', None), u'АРМ Администратора РИСАР'),
        visible=UserProfileManager.has_ui_risar()
    ), dict(
        link='anareports.index_html',
        title=u'Аналитические отчёты',
        visible=True
    )]
    return dict(main_menu=menu_items)


from blueprints.accounting.app import module as accounting_module
from blueprints.anareports.app import module as anareports_module
from blueprints.event.app import module as event_module
from blueprints.patients.app import module as patients_module
from blueprints.schedule.app import module as schedule_module
from blueprints.risar.app import module as risar_module

app.register_blueprint(accounting_module, url_prefix='/accounting')
app.register_blueprint(anareports_module, url_prefix='/anareports')
app.register_blueprint(event_module, url_prefix='/event')
app.register_blueprint(patients_module, url_prefix='/patients')
app.register_blueprint(schedule_module, url_prefix='/schedule')
app.register_blueprint(risar_module, url_prefix='/risar')

if __name__ == "__main__":
    app.run()