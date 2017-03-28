# coding: utf-8

# application
from nemesis.systemwide import celery

# tasks
from risar_tasks import update_card_attrs_cfrs, run_coefficient_calculations


@celery.task
def test_task():
    import math
    import random
    return math.factorial(random.randint(1, 20))


@celery.task
def test_db_task():
    from nemesis.systemwide import db
    tables = [t[0] for t in db.session.execute('SHOW TABLES')]
    return tables