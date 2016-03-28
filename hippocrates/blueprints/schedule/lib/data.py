# -*- coding: utf-8 -*-

from nemesis.lib.utils import (jsonify, )
from nemesis.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket


def delete_schedules(dates, person_id):
    schedules = Schedule.query.filter(
        Schedule.person_id == person_id, Schedule.date.in_(dates),
    )
    if not schedules.count():
        return True, ''
    schedules_with_clients = schedules.join(ScheduleTicket).join(ScheduleClientTicket).filter(
        Schedule.deleted == 0,
        ScheduleClientTicket.client_id is not None,
        ScheduleClientTicket.deleted == 0
    ).all()
    if schedules_with_clients:
        return False, u'Пациенты успели записаться на приём'

    schedules.update({
        Schedule.deleted: 1,
    }, synchronize_session=False)

    ScheduleTicket.query.filter(
        ScheduleTicket.schedule_id.in_([s.id for s in schedules])
    ).update({
        ScheduleTicket.deleted: 1
    }, synchronize_session=False)
    return True, ''
