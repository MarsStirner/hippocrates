# -*- coding: utf-8 -*-
from datetime import datetime
from uuid import uuid4
from application.systemwide import db
from application.lib.utils import logger
from application.models.actions import Action, ActionType, ActionPropertyType, ActionProperty
from application.models.exists import Person, UUID
from application.models.event import Event
from application.lib.agesex import recordAcceptableEx


def create_action(event_id, action_type_id, person_id, data):
    if not event_id or action_type_id:
        raise AttributeError

    now = datetime.now()
    actionType = ActionType.query.get(int(action_type_id))
    event = Event.query.get(int(event_id))

    action = Action()
    action.createDatetime = action.modifyDatetime = action.begDate = now
    action.createPerson = action.modifyPerson = action.setPerson = Person.query.get(int(person_id))
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.status = 0
    action.note = ''
    action.payStatus = 0
    action.account = 0
    action.coordText = ''
    action.AppointmentType = 0
    uuid = UUID()
    uuid.uuid = '{%s}' % uuid4().get_hex
    action.uuid = uuid

    for field, value in data.items():
        if field in action.__dict__ and not getattr(action, field):
            setattr(action, field, value)

    prop_types = actionType.property_types.filter(ActionPropertyType.deleted == 0)
    now_date = now.date()
    for prop_type in prop_types:
        if recordAcceptableEx(event.client.sex, event.client.age_tuple(now_date), prop_type.sex, prop_type.age):
            prop = ActionProperty()
            prop.type = prop_type
            prop.action = action
            prop.createDatetime = prop.modifyDatetime = now
            prop.norm = ''
            prop.evaluation = ''
            prop.createPerson_id = prop.modifyPerson_id = int(data.get('person_id', 1))
            db.session.add(prop)

    db.session.add(action)

    try:
        db.session.commit()
    except Exception, e:
        logger.error(e)
        db.session.rollback()
    else:
        return action
    return None