# -*- coding: utf-8 -*-
import datetime

__author__ = 'mmalkov'


class JsonSchedule(object):
    class EmptyDay(object):
        def __init__(self, date):
            self.date = date

    def __init__(self):
        self.max_tickets = 0
        self.result = []

    @staticmethod
    def make_json_date(d):
        return d.isoformat()

    def make_ticket(self, ticket):
        return {
            'id': ticket.id,
            'begDateTime': self.make_json_date(ticket.begDateTime),
        }

    def make_schedule(self, schedule):
        if isinstance(schedule, self.EmptyDay):
            return {
                'date': self.make_json_date(schedule.date),
                'tickets': [None] * self.max_tickets,
            }
        else:
            return {
                'id': schedule.id,
                'date': self.make_json_date(schedule.date),
                'office': schedule.office,
                'tickets': map(self.make_ticket, schedule.tickets) +
                           [None] * (self.max_tickets - len(schedule.tickets)),
            }

    def __json__(self):
        return self.result

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

        self.result = [self.make_schedule(s) for s in result]
        self.transposed = [[r['tickets'][i] for r in self.result] for i in xrange(self.max_tickets)]