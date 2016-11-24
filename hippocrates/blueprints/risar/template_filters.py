# -*- coding: utf-8 -*-

import datetime

from nemesis.app import app as nemesis_app


@nemesis_app.template_filter('as_date')
def human_date(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime('%d.%m.%Y')
    return ''


@nemesis_app.template_filter('ifempty')
def if_empty(value, replacement=''):
    if value:
        return value
    return replacement
