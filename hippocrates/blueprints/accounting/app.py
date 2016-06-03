# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )


from html_views import *
from api import *
from api_json import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'accounting': {
                'event_make_payment': url_for('accounting.api_event_make_payment'),
                'get_event_payments': url_for('accounting.api_get_event_payments'),

            }
        }
    }