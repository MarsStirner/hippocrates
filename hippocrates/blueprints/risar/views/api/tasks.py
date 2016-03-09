# -*- coding: utf-8 -*-

from blueprints.risar.app import module
from celery_tasks import test_task, test_db_task, update_card_attrs_cfrs


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
