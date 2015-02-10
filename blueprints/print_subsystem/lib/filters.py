# -*- coding: utf-8 -*-
import datetime

__author__ = 'viruzzz-kun'


def do_datetime_format(d, fmt=None):
    if isinstance(d, datetime.datetime):
        return d.strftime(fmt or '%d.%m.%Y %H:%M')
    elif isinstance(d, datetime.date):
        return d.strftime(fmt or '%d.%m.%Y')
    elif isinstance(d, datetime.time):
        return d.strftime(fmt or '%H:%M')
    return d


def do_datetime_combine(date_time_tuple):
    return datetime.datetime.combine(*date_time_tuple)


def do_datetime_add_days(dt, add):
    return dt + datetime.timedelta(days=add)


def do_transpose_table(table):
    return [[row[column_number] for row in table] for column_number in xrange(len(table[0]))] if table else [[]]


def do_sum_columns(table):
    return [sum(row[column_number] for row in table) for column_number in xrange(len(table[0]))] if table else [[]]


def do_table_uniform(list_list, null=None):
    max_len = max(len(row) for row in list_list)
    return [(row + [null] * (max_len - len(row))) for row in list_list]


def do_table_column(table, column=0):
    return [row[column] for row in table] if table and table[0] else []
