from celery.schedules import crontab
import datetime

CELERYBEAT_SCHEDULE = {
    # 'test_task': {
    #     'task': 'celery_tasks.test_task',
    #     'schedule': datetime.timedelta(seconds=3),
    #     # 'args': (None, '3')
    # },
    # 'test_db_task': {
    #     'task': 'celery_tasks.test_db_task',
    #     'schedule': datetime.timedelta(seconds=30),
    # },
    'update_card_attrs_crfs': {
        'task': 'celery_tasks.risar_tasks.update_card_attrs_cfrs',
        'schedule': crontab(minute=0, hour=0),
    },
    'close_yesterday_checkups': {
        'task': 'celery_tasks.risar_tasks.close_yesterday_checkups',
        'schedule': crontab(minute=0, hour=8),
    },
}

try:
    from celery_schedule_local import *
    print('modified schedule used')
except ImportError:
    pass