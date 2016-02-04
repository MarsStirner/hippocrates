# -*- coding: utf-8 -*-
import os

from nemesis.app import app, bootstrap_app
from tsukino_usagi.client import TsukinoUsagiClient

__author__ = 'viruzzz-kun'


class HippoUsagiClient(TsukinoUsagiClient):
    def on_configuration(self, configuration):
        app.config.update(configuration)
        bootstrap_app(os.path.join(os.path.dirname(__file__), 'templates'))
