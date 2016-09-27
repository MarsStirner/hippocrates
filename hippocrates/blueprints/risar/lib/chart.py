# coding: utf-8
from nemesis.models.event import Event


def get_event(event_id):
    if not event_id:
        return None
    return Event.query.filter(Event.id == event_id, Event.deleted == 0).first()
