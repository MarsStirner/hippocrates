# -*- coding: utf-8 -*-
import datetime
from jinja2 import FileSystemLoader
from jinja2.environment import Environment
from nemesis.app import app

from context import CTemplateContext
from html import escape, escapenl, HTMLRipper, date_toString, time_toString, addDays
from flask import url_for

__author__ = 'mmalkov'


class Render:
    standard = 0
    jinja2   = 1


class RenderTemplateException(Exception):
    class Type:
        syntax = 0
        other = 1
    def __init__(self, message, data=None):
        super(RenderTemplateException, self).__init__(message)
        self.data = data


def make_jinja_environment():
    from .filters import do_datetime_format, do_datetime_combine, do_datetime_add_days, do_sum_columns, \
        do_table_column, do_table_uniform, do_transpose_table
    env = Environment(
        loader=FileSystemLoader('blueprints/print_subsystem/templates/print_subsystem'),
        finalize=finalizer,
    )
    env.filters.update({
        'datetime_format': do_datetime_format,
        'datetime_combine': do_datetime_combine,
        'datetime_add_days': do_datetime_add_days,
        'transpose_table': do_transpose_table,
        'sum_columns': do_sum_columns,
        'table_column': do_table_column,
        'table_uniform': do_table_uniform,
    })
    return env


def renderTemplate(template, data, render=1):
    # Формируем execContext
    global_vars = {
        'escape': escape,
        'escapenl': escapenl,
        'HTMLRipper': HTMLRipper,
        'hard_rip': HTMLRipper.hard_rip,
        'soft_rip': HTMLRipper.soft_rip,
        'setPageSize': setPageSize,
        'setOrientation': setOrientation,
        'setPageOrientation': setOrientation,
        'setMargins': setMargins,
        'setLeftMargin': setLeftMargin,
        'setTopMargin': setTopMargin,
        'setRightMargin': setRightMargin,
        'setBottomMargin': setBottomMargin
    }

    execContext = CTemplateContext(global_vars, data)

    if render == Render.jinja2:
        try:
            context = {}
            context.update(execContext.builtin)
            context.update(execContext.globals)
            context.update(execContext.data)
            context.update({"now": execContext.now,
                            "date_toString": date_toString,
                            "time_toString": time_toString,
                            "addDays": addDays,
                            "images": url_for(".static", filename="i/", _external=True),
                            "trfu_service": app.config['TRFU_URL'],
                            })
            env = make_jinja_environment()
            macros = "{% import '_macros.html' as macros %}"
            result = env.from_string(macros+template, globals=global_vars).render(context)
        except Exception:
            print "ERROR: template.render(data)"
            raise
    else:
        result = u"<HTML><HEAD></HEAD><BODY>Не удалось выполнить шаблон</BODY></HTML>"
    # canvases = execContext.getCanvases()
    # for k in canvases:
    #     print k, canvases[k]
    return result


def finalizer(obj):
    if obj is None:
        return ''
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%d.%m.%Y %H:%M')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%d.%m.%Y')
    elif isinstance(obj, datetime.time):
        return obj.strftime('%H:%M')
    return obj


def setPageSize(page_size):
    return ''


def setOrientation(orientation):
    return ''


def setMargins(margin):
    return ''


def setLeftMargin(left_margin):
    return ''


def setTopMargin(top_margin):
    return ''


def setRightMargin(right_margin):
    return ''


def setBottomMargin(bottom_margin):
    return ''
