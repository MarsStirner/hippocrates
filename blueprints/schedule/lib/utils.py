# -*- coding: utf-8 -*-
import calendar
import datetime
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer


def get_schedule(person_id, start_date, end_date):
    schedules = Schedule.query.\
        filter(Schedule.person_id == person_id).\
        filter(start_date <= Schedule.date).\
        filter(Schedule.date <= end_date).\
        order_by(Schedule.date)
    context = ScheduleVisualizer()
    context.push_all(schedules, start_date, end_date)
    return context