# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(module_name=RUS_NAME)


# noinspection PyUnresolvedReferences
from .views import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'biomaterials': {
                'api_get_ttj_records': url_for('biomaterials.api_get_ttj_records'),
                'api_ttj_update_status': url_for('biomaterials.api_ttj_change_status')
            }
        }
    }