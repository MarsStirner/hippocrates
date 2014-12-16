# -*- coding: utf-8 -*-
from pytz import timezone
from application.app import app
from datetime import datetime
from application.lib.user import UserUtils
from version import version as _version, last_change_date

from config import TIME_ZONE

@app.context_processor
def copyright():
    return dict(copy_year=datetime.today().year)


@app.context_processor
def version():
    change_date = timezone(TIME_ZONE).localize(last_change_date)
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
    menu_items = list()
    menu_items.append(dict(link='patients.index',
                           title=u'Обслуживание пациентов',
                           roles=('admin', 'rRegistartor', 'clinicRegistrator')))
    menu_items.append(dict(link='schedule.person_schedule_monthview',
                           title=u'Формирование графика врача',
                           roles=('admin', 'rRegistartor', 'clinicRegistrator')))
    menu_items.append(dict(link='schedule.index',
                           title=u'График работы',
                           roles=('admin', 'rRegistartor', 'clinicRegistrator')))
    menu_items.append(dict(link='schedule.doctor_schedule_day',
                           title=u'Приём пациентов',
                           roles=('admin', 'clinicDoctor', 'diagDoctor')))
    menu_items.append(dict(link='patients.search',
                           title=u'Поиск пациентов',
                           roles=('admin', 'clinicDoctor', 'diagDoctor')))
    menu_items.append(dict(link='event.get_events',
                           title=u'Обращения',
                           roles=('admin', 'rRegistartor', 'clinicRegistrator', 'clinicDoctor', 'diagDoctor')))
    menu_items.append(dict(link='risar.index_html',
                           title=u'АРМ Акушера-гинеколога',
                           roles=('admin', 'obstetrician')))

    return dict(main_menu=menu_items)


@app.context_processor
def user_utils():
    return {
        'user_utils': UserUtils
    }
