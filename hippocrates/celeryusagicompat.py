# -*- coding: utf-8 -*-

from usagicompat import HippoUsagiClient
from celery_schedule import CELERYBEAT_SCHEDULE


class HippoCeleryUsagiClient(HippoUsagiClient):
    def on_configuration(self, configuration):
        if 'SQLALCHEMY_ECHO' in configuration:
            configuration['SQLALCHEMY_ECHO'] = False
        configuration['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

        super(HippoCeleryUsagiClient, self).on_configuration(configuration)