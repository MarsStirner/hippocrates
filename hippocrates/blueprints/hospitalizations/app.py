# -*- coding: utf-8 -*-
import os

from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config


module = Blueprint(
    os.path.basename(os.path.dirname(__file__)),
    __name__,
    template_folder='templates',
    static_folder='static'
)


# noinspection PyUnresolvedReferences
from .views import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'hospitalizations': {
                'api_current_hosps_get': url_for('hospitalizations.api_0_current_hosps_get'),
            }
        }
    }
