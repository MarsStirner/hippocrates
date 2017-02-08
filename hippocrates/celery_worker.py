# coding: utf-8

import os
from celery.utils.log import get_task_logger
from celery.signals import worker_process_init

from celeryusagicompat import HippoCeleryUsagiClient
from nemesis.app import app as flask_app
from nemesis.systemwide import db


logger = get_task_logger(__name__)

usagi = HippoCeleryUsagiClient(flask_app.wsgi_app, os.getenv('TSUKINO_USAGI_URL', 'http://127.0.0.1:5900'), 'hippo')
flask_app.wsgi_app = usagi.app
usagi()

# для генерации url, которые понадобятся клиенту sirius
config = flask_app.config
hippo_url = config.get('HIPPO_URL').rstrip('/').lstrip('http://')
config['SERVER_NAME'] = hippo_url


# https://github.com/Robpol86/Flask-Large-Application-Example
with flask_app.app_context():

    # Fix Flask-SQLAlchemy and Celery incompatibilities.
    @worker_process_init.connect
    def celery_worker_init_db(**_):
        """Initialize SQLAlchemy right after the Celery worker process forks.
        This ensures each Celery worker has its own dedicated connection to the MySQL database. Otherwise
        one worker may close the connection while another worker is using it, raising exceptions.
        Without this, the existing session to the MySQL server is cloned to all Celery workers, so they
        all share a single session. A SQLAlchemy session is not thread/concurrency-safe, causing weird
        exceptions to be raised by workers.
        Based on http://stackoverflow.com/a/14146403/1198943
        """
        logger.debug('Initializing SQLAlchemy for PID {}.'.format(os.getpid()))
        db.init_app(flask_app)


from nemesis.systemwide import celery  # this is what celery process uses
from celery_tasks import *