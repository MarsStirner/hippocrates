# -*- coding: utf-8 -*-

from flask import request, abort

from hippocrates.blueprints.risar.app import module
from celery_tasks import test_task, test_db_task, update_card_attrs_cfrs
from nemesis.app import app
from nemesis.lib.html_utils import UIException


@module.before_request
def before_risar_tasks_request():
    if '/tasks/' in request.endpoint and not app.config['CELERY_ENABLED']:
        raise UIException(403, u'Невозможно выполнить задачи, так как поддержка Celery не включена (CELERY_ENABLED в конфигурации системы)')


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
