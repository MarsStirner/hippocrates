# -*- coding: utf-8 -*-
from application.app import app, bootstrap_app
import config_hippocrates

__author__ = 'viruzzz-kun'

app.config.from_object(config_hippocrates)
bootstrap_app()

from blueprints.accounting.app import module as accounting_module
from blueprints.anareports.app import module as anareports_module
from blueprints.event.app import module as event_module
from blueprints.patients.app import module as patients_module
from blueprints.schedule.app import module as schedule_module

app.register_blueprint(accounting_module, url_prefix='/accounting')
app.register_blueprint(anareports_module, url_prefix='/anareports')
app.register_blueprint(event_module, url_prefix='/event')
app.register_blueprint(patients_module, url_prefix='/patients')
app.register_blueprint(schedule_module, url_prefix='/schedule')

if __name__ == "__main__":
    app.run()