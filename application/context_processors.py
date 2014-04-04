# -*- coding: utf-8 -*-
from application.app import app
from werkzeug.utils import import_string
from datetime import datetime


@app.context_processor
def copyright():
    return dict(copy_year=datetime.now())


@app.context_processor
def print_subsystem():
    return dict(print_subsystem_url=app.config['PRINT_SUBSYSTEM_URL'])


@app.context_processor
def general_menu():
    menu_items = list()
    blueprints = app.blueprints
    for k, v in blueprints.items():
        try:
            config = import_string('%s.config' % import_string(v.import_name).__package__)
        except ImportError, e:
            print e
        else:
            if hasattr(config, 'RUS_NAME'):
                menu_items.append(dict(module=v.name, name=config.RUS_NAME))
            else:
                menu_items.append(dict(module=v.name, name=v.name))

    return dict(main_menu=menu_items)