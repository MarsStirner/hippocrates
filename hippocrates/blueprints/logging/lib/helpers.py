# -*- encoding: utf-8 -*-
from datetime import datetime
from dateutil.parser import parse
import re
from jinja2 import evalcontextfilter, Markup, escape


def datetimeformat_filter(value, _format='%Y-%m-%d'):
    if isinstance(value, datetime):
        return value.strftime(_format)
    else:
        return None


def strpdatetime_filter(value):
    return parse(value)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def nl2br_filter(eval_ctx, value):
    result = u'\n\n'.join(u'{0}'.format(p.replace('\n', Markup('<br>\n')))
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result