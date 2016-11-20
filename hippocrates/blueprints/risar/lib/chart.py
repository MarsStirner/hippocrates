# coding: utf-8
import datetime

from sqlalchemy import func

from hippocrates.blueprints.risar.risar_config import request_type_pregnancy
from nemesis.models.event import Event, EventType, EventPersonsControl
from nemesis.models.exists import rbRequestType
from nemesis.lib.user import UserProfileManager
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


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


def can_control_events():
    return UserProfileManager.has_ui_overseers()


def check_event_controlled(event):
    if not event.id or not can_control_events():
        return False
    return EventPersonsControl.query.filter(
        EventPersonsControl.event_id == event.id,
        EventPersonsControl.person_id == safe_current_user_id(),
        EventPersonsControl.endDate.is_(None)
    ).count() > 0


def check_events_controlled(event_ids):
    res = dict((e_id, False) for e_id in event_ids)

    if not can_control_events():
        return res

    query = EventPersonsControl.query.filter(
        EventPersonsControl.event_id.in_(event_ids),
        EventPersonsControl.person_id == safe_current_user_id(),
        EventPersonsControl.endDate.is_(None)
    ).group_by(
        EventPersonsControl.event_id
    ).with_entities(
        EventPersonsControl.event_id.label('event_id'),
        func.count(EventPersonsControl.id) > 0
    )
    for event_id, cnt in query:
        res[event_id] = bool(cnt)
    return res


def take_event_control(event):
    person_id = safe_current_user_id()
    if not check_event_controlled(event):
        epc = EventPersonsControl(
            event_id=event.id,
            person_id=person_id,
            begDate=datetime.datetime.now()
        )
        db.session.add(epc)
        db.session.commit()
    return True


def remove_event_control(event):
    person_id = safe_current_user_id()
    EventPersonsControl.query.filter(
        EventPersonsControl.event_id == event.id,
        EventPersonsControl.person_id == person_id,
        EventPersonsControl.endDate.is_(None)
    ).update({
        EventPersonsControl.endDate: datetime.datetime.now()
    }, synchronize_session=False)
    db.session.commit()
    return False
