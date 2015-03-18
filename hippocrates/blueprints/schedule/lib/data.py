# -*- coding: utf-8 -*-

from nemesis.lib.utils import (jsonify, )
from nemesis.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket


def delete_schedules(dates, person_id):
    schedules = Schedule.query.filter(
        Schedule.person_id == person_id, Schedule.date.in_(dates),
    )
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

    schedules.join(ScheduleTicket).filter(
        ScheduleTicket.schedule_id == Schedule.id,
    ).update({
        ScheduleTicket.deleted: 1
    }, synchronize_session=False)
    return True, ''