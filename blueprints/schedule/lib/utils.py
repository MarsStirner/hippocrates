# -*- coding: utf-8 -*-
import calendar
import datetime
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer


def paginator_month(mid_date):
    year = mid_date.year
    month = mid_date.month
    last_day = calendar.monthrange(year, month)[1]
    date_start = datetime.date(year, month, 1)
    date_end = datetime.date(year, month, last_day)
    one_week = datetime.timedelta(weeks=1)
    six_days = datetime.timedelta(days=6)
    chosen_page = -1
    current_date = date_start
    current_page = 0
    pages = []
    while current_date <= date_end:
        if mid_date >= current_date:
            chosen_page = current_page
        pages.append((current_date, min(current_date + six_days, date_end)))
        current_date += one_week
        current_page += 1
    return chosen_page, pages


def get_schedule(person_id, start_date, end_date):
    schedules = Schedule.query.\
        filter(Schedule.person_id == person_id).\
        filter(start_date <= Schedule.date).\
        filter(Schedule.date <= end_date).\
        order_by(Schedule.date)
    context = ScheduleVisualizer()
    context.push_all(schedules, start_date, end_date)
    return context