# -*- coding: utf-8 -*-

import calendar
from collections import defaultdict
import datetime

from flask import abort, request

from application.models.event import Event
from application.systemwide import db, cache
from application.lib.sphinx_search import SearchPerson
from application.lib.agesex import recordAcceptableEx
from application.lib.utils import (jsonify, safe_traverse, get_new_uuid, parse_id)
from blueprints.schedule.app import module
from application.models.exists import (rbSpeciality, rbReasonOfAbsence, rbPrintTemplate, Person)
from application.models.actions import Action, ActionType, ActionProperty, ActionPropertyType
from application.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType, \
    rbReceptionType, rbAttendanceType
from application.lib.jsonify import ScheduleVisualizer, PrintTemplateVisualizer, \
    ActionVisualizer


def delete_schedules(dates, person_id):
    schedules = Schedule.query.filter(
        Schedule.deleted == 0, Schedule.person_id == person_id, Schedule.date.in_(dates),
    )
    schedules_with_clients = schedules.join(ScheduleTicket, ScheduleClientTicket).filter(
        ScheduleClientTicket.client_id is not None
    ).all()  # todo: checked deleted ?
    if schedules_with_clients:
        return jsonify({}, 401, u'Пациенты успели записаться на приём')
    schedules.update({
        Schedule.deleted: 1
    }, synchronize_session=False)
    return True