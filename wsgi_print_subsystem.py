# -*- coding: utf-8 -*-
from application.app import app, bootstrap_app
import config_print_subsystem

__author__ = 'viruzzz-kun'

app.config.from_object(config_print_subsystem)
bootstrap_app()

from blueprints.print_subsystem.app import module as print_subsystem_module

app.register_blueprint(print_subsystem_module, url_prefix='/print_subsystem')

if __name__ == "__main__":
    app.run()