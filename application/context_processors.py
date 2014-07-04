# -*- coding: utf-8 -*-
from application.app import app
from datetime import datetime
from version import version as _version


@app.context_processor
def copyright():
    return dict(copy_year=datetime.today().year)


@app.context_processor
def version():
    return dict(version=_version)


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
    menu_items = list()
    menu_items.append(dict(module='patients.',
                           link='patients.index',
                           title=u'Обслуживание пациентов'))
    menu_items.append(dict(module='schedule.',
                           link='schedule.person_schedule_monthview',
                           title=u'Формирование графика врача'))
    menu_items.append(dict(module='schedule',
                           link='schedule.index',
                           title=u'Просмотр графика работы'))
    return dict(main_menu=menu_items)