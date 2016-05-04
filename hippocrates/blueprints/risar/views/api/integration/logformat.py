# -*- coding: utf-8 -*-
import logging

import flask

__author__ = 'viruzzz-kun'


logger = logging.getLogger('simple')


format_exception = u'''Request:
%(method)s %(url)s
%(request_headers)s%(request_json)s

Response: %(code)i
Exception: %(exception)r
Body: %(body)s
'''

format_ok = u'''Request:
%(method)s %(url)s
%(request_headers)s%(request_json)s

Response: %(code)i
Body: %(body)s
'''


def format_logger_message(code, j, exception=None):
    data = flask.request.get_data(as_text=True, parse_form_data=True)
    d = {
        'method': flask.request.method,
        'url': flask.request.url,
        'request_headers': u'\n'.join('%s: %s' % i for i in flask.request.headers.iteritems()),
        'request_json': '\n\n%s' % data if data else '',
        'code': code,
        'exception': exception,
        'body': j,
    }
    if exception:
        return format_exception % d
    else:
        return format_ok % d


def hook(code, j, e=None):
    if e:
        logger.error(format_logger_message(code, j))
    else:
        logger.debug(format_logger_message(code, j))
