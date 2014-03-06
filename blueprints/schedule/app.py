# -*- coding: utf-8 -*-
from flask import Blueprint
from blueprints.schedule.models.exists import rbReasonOfAbsence
from blueprints.schedule.models.schedule import rbReceptionType
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
        rbReceptionTypes=rbReceptionType.query.order_by(rbReceptionType.code).all(),  #  u"""[{name: 'Амбулаторно', code: 'amb'}, {name: 'На дому', code: 'home'}]""",
        rbReasonOfAbsence=rbReasonOfAbsence.query.order_by(rbReasonOfAbsence.code).all()
    )

# noinspection PyUnresolvedReferences
from .views import *