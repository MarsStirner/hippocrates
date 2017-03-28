# -*- coding: utf-8 -*-

from flask import request, abort

from hippocrates.blueprints.risar.app import module
from celery_tasks import test_task, test_db_task, update_card_attrs_cfrs, run_coefficient_calculations
from nemesis.app import app


@module.before_request
def before_risar_tasks_request():
    if '/tasks/' in request.endpoint and not app.config['CELERY_ENABLED']:
        abort(403)


@module.route('/api/0/tasks/test_task/')
def api_0_test_task(*args, **kwargs):
    test_task.delay()
    return 'started'


@module.route('/api/0/tasks/test_db_task/')
def api_0_test_db_task():
    test_db_task.delay()
    return 'started'


@module.route('/api/0/tasks/task_cfrs_update/')
def api_0_update_cfrs():
    update_card_attrs_cfrs.delay()
    return 'cfrs update started'


@module.route('/api/0/tasks/coeff/<int:year>')
def api_0_coefficient_calculations(year=None):
    run_coefficient_calculations.delay(year)
    return 'coefficient_calculations'
