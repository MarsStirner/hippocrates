# -*- coding: utf-8 -*-
from flask import Blueprint, url_for

from nemesis.lib.frontend import frontend_config
from .config import MODULE_NAME


module = Blueprint(MODULE_NAME, __name__, static_folder='static', template_folder='template')


# noinspection PyUnresolvedReferences
from .views import *

# @frontend_config
# def fc_urls():
#     return {
#         'url': {
#             'hospitalization': {
#                 'index': url_for('hospitalization.index'),
#             }
#         }
#     }