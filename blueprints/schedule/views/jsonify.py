# -*- coding: utf-8 -*-
import datetime
from json import JSONEncoder

__author__ = 'mmalkov'


class MyJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        return JSONEncoder.default(self, o)


class ScheduleVisualizer(object):
    class EmptyDay(object):
        def __init__(self, date):
            self.date = date

    def __init__(self):
        self.max_tickets = 0
        self.schedule = []

    def make_ticket(self, ticket):
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime.strftime('%H:%M'),
            'client': None, #FIXME
            'status': 'free', #FIXME
            # 'client': ticket.client.nameText if ticket.client else None,
        }

    def make_empty_ticket(self):
        return {
            # 'id': None,
            # 'begDateTime': None,
            # 'client': None,
            'status': 'empty',
        }

    def make_schedule(self, schedule):
        if isinstance(schedule, self.EmptyDay):
            return {
                'date': schedule.date,
                'tickets': [self.make_empty_ticket()] * self.max_tickets,
            }
        else:
            return {
                'id': schedule.id,
                'date': schedule.date,
                'office': schedule.office,
                'tickets': map(self.make_ticket, schedule.tickets) + [
                    self.make_empty_ticket()
                ] * (self.max_tickets - len(schedule.tickets)),
            }

    def push_all(self, schedules, month_f, month_l):
        result = []
        one_day = datetime.timedelta(days=1)
        max_tickets = 0
        for schedule in schedules:
            if len(schedule.tickets) > max_tickets:
                max_tickets = len(schedule.tickets)

            while schedule.date > month_f:
                result.append(self.EmptyDay(month_f))
                month_f += one_day

            result.append(schedule)
            month_f += one_day

        while month_f < month_l:
            result.append(self.EmptyDay(month_f))
            month_f += one_day

        self.max_tickets = max_tickets

        self.schedule = [self.make_schedule(s) for s in result]
        # self.transposed = [[r['tickets'][i] for r in self.result] for i in xrange(self.max_tickets)]