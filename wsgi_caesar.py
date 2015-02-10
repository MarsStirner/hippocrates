# -*- coding: utf-8 -*-
from application.app import app, bootstrap_app
import config_caesar

__author__ = 'viruzzz-kun'

app.config.from_object(config_caesar)
bootstrap_app()


@app.context_processor
def general_menu():
    from application.lib.user import UserProfileManager

    menu_items = [dict(
        link='index',
        title=u'Главная страница',
        homepage=True,
        visible=(not UserProfileManager.has_ui_registrator_cut())
    ), dict(
        link='dict.index',
        title=u'Справочники',
        visible=True,
    ), dict(
        link='logging.index',
        title=u'Журнал',
        visible=True,
    ), dict(
        link='reports.index',
        title=u'Отчёты',
        visible=True,
    ), dict(
        link='print_subsystem.index',
        title=u'Печать',
        visible=True,
    ), dict(
        link='tfoms.index',
        title=u'ТФОМС',
        visible=True,
    )]
    return dict(main_menu=menu_items)


from blueprints.print_subsystem.app import module as print_subsystem_module
from blueprints.dict.app import module as dict_module
from blueprints.logging.app import module as logging_module
from blueprints.reports.app import module as reports_module
from blueprints.tfoms.app import module as tfoms_module

app.register_blueprint(print_subsystem_module, url_prefix='/print_subsystem')
app.register_blueprint(dict_module, url_prefix='/dict')
app.register_blueprint(logging_module, url_prefix='/logging')
app.register_blueprint(reports_module, url_prefix='/reports')
app.register_blueprint(tfoms_module, url_prefix='/tfoms')

if __name__ == "__main__":
    app.run()