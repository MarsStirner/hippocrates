# -*- coding: utf-8 -*-
from usagicompat import HippoUsagiClient
from celery_schedule import CELERYBEAT_SCHEDULE, \
    schedule_close_yesterday_checkups



class HippoCeleryUsagiClient(HippoUsagiClient):
    def on_configuration(self, configuration):
        if 'SQLALCHEMY_ECHO' in configuration:
            configuration['SQLALCHEMY_ECHO'] = False
        configuration['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

        super(HippoCeleryUsagiClient, self).on_configuration(configuration)

        from hippocrates.blueprints.risar.lib.specific import SpecificsManager
        if SpecificsManager.close_yesterday_checkups():
            CELERYBEAT_SCHEDULE.update(schedule_close_yesterday_checkups)
