# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import ScheduleXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/schedule.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule_schema(api_version):
    return ScheduleXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/schedule/<int:doctor_id>/')
@api_method(hook=hook)
def api_schedule_get(api_version, doctor_id):
    args = request.args.to_dict()
    xform = ScheduleXForm(api_version)
    xform.check_params(None, doctor_id)
    xform.find_schedules(args)
    return xform.as_json()
