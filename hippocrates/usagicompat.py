# -*- coding: utf-8 -*-
import os

from nemesis.app import app, bootstrap_app
from tsukino_usagi.client import TsukinoUsagiClient

__author__ = 'viruzzz-kun'


class HippoUsagiClient(TsukinoUsagiClient):
    def on_configuration(self, configuration):
        app.config.update(configuration)
        bootstrap_app(os.path.join(os.path.dirname(__file__), 'templates'))

        from hippocrates.blueprints.accounting.app import module as accounting_module
        from hippocrates.blueprints.anareports.app import module as anareports_module
        from hippocrates.blueprints.biomaterials.app import module as biomaterials_module
        from hippocrates.blueprints.event.app import module as event_module
        from hippocrates.blueprints.hospitalizations.app import module as hospitalizations_module
        from hippocrates.blueprints.patients.app import module as patients_module
        from hippocrates.blueprints.schedule.app import module as schedule_module
        from hippocrates.blueprints.actions.app import module as actions_module
        from hippocrates.blueprints.useraccount.app import module as useraccount_module
        from hippocrates.blueprints.risar.app import module as risar_module

        app.register_blueprint(accounting_module, url_prefix='/accounting')
        app.register_blueprint(anareports_module, url_prefix='/anareports')
        app.register_blueprint(biomaterials_module, url_prefix='/biomaterials')
        app.register_blueprint(event_module, url_prefix='/event')
        app.register_blueprint(hospitalizations_module, url_prefix='/hospitalizations')
        app.register_blueprint(patients_module, url_prefix='/patients')
        app.register_blueprint(schedule_module, url_prefix='/schedule')
        app.register_blueprint(actions_module, url_prefix='/actions')
        app.register_blueprint(useraccount_module, url_prefix='/user')
        app.register_blueprint(risar_module, url_prefix='/risar')

