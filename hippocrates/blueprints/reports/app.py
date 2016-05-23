#! coding:utf-8
"""


@author: BARS Group
@date: 16.05.2016

"""
from flask import Blueprint
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__)


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )

# noinspection PyUnresolvedReferences
from .views import *
