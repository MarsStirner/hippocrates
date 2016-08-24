# -*- coding: utf-8 -*-

from nemesis.models.actions import Action, ActionType
from nemesis.systemwide import db
from sqlalchemy import or_, and_


def get_prev_inspection_query(action, flatcodes):
    return db.session.query(Action).join(ActionType).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        ActionType.flatCode.in_(flatcodes),
        or_(Action.begDate < action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id < action.id if action.id else True)
            ),
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1)