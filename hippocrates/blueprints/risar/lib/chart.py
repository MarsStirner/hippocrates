# coding: utf-8
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy
from nemesis.models.event import Event, EventType

from nemesis.models.exists import rbRequestType


def get_event(event_id):
    if not event_id:
        return None
    return Event.query.filter(Event.id == event_id, Event.deleted == 0).first()


def get_latest_pregnancy_event(client_id):
    return Event.query.join(EventType, rbRequestType).filter(
        Event.client_id == client_id,
        Event.deleted == 0,
        rbRequestType.code == request_type_pregnancy,
        Event.execDate.is_(None)
    ).order_by(Event.setDate.desc()).first()