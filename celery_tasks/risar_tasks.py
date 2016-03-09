# coding: utf-8

import datetime
from celery.utils.log import get_task_logger

from nemesis.systemwide import celery, db
from nemesis.models.celery_tasks import TaskInfo
from nemesis.models.event import Event
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.utils import safe_dict
from blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent import represent_event_cfrs
from blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all


logger = get_task_logger(__name__)


@celery.task(bind=True)
def update_card_attrs_cfrs(self):
    new_task = TaskInfo()
    new_task.start_datetime = datetime.datetime.now()
    new_task.task_name = update_card_attrs_cfrs.__name__
    new_task.celery_task_uuid = self.request.id

    task_data = {}

    # before
    event_list = db.session.query(Event).filter(
        Event.deleted == 0,
        Event.execDate.is_(None)
    ).order_by(Event.setDate).all()
    cfrs_before = []
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        cfrs_before.append({
            'event_id': event.id,
            'card_fill_rates': represent_event_cfrs(card.attrs)
        })
    task_data['cfrs_before'] = cfrs_before
    new_task.task_data = json_dumps(task_data, pretty=True)
    db.session.add(new_task)
    db.session.commit()

    # work
    logger.info('starting card cfrs update')
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        if not card or not card.attrs:
            logger.critical('event {0} is not valid'.format(event.id))
            continue
        reevaluate_card_fill_rate_all(card)
    db.session.commit()
    logger.info('card cfrs update finished')

    # after
    cfrs_after = []
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        cfrs_after.append({
            'event_id': event.id,
            'card_fill_rates': represent_event_cfrs(card.attrs)
        })
    task_data['cfrs_after'] = cfrs_after

    diff = []
    for b, a in zip(cfrs_before, cfrs_after):
        if safe_dict(b) != safe_dict(a):
            logger.debug(u'diff in {0} and {1}'.format(b, a))
            diff.append((b, a))
    task_data['diff'] = diff

    new_task.task_data = json_dumps(task_data, pretty=True)
    new_task.finish_datetime = datetime.datetime.now()
    db.session.add(new_task)
    db.session.commit()
    return safe_dict(diff)
