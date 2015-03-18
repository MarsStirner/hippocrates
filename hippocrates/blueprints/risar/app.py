# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )

@module.route('/config.js')
def config_js():
    return render_template('risar/config.js')

# noinspection PyUnresolvedReferences
from .views import *