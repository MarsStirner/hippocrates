# -*- coding: utf-8 -*-

import logging

from flask import request

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import ScheduleXForm, Schedule2XForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/schedule.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule_schema(api_version):
    return ScheduleXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/schedule/<lpu_code>/<doctor_code>')
@api_method(hook=hook)
def api_schedule_get(api_version, lpu_code, doctor_code):
    args = request.args.to_dict()
    xform = ScheduleXForm(api_version)
    xform.init_and_check_params(lpu_code, doctor_code)
    xform.find_schedules(**args)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/schedule/<lpu_code>/<doctor_code>', methods=['POST'])
@api_method(hook=hook)
def api_schedule_save(api_version, lpu_code, doctor_code):
    data = request.get_json()
    xform = ScheduleXForm(api_version, is_create=True)
    xform.init_and_check_params(lpu_code, doctor_code, data)
    date_begin, date_end = xform.create_schedules(data)
    xform.store()
    xform.find_schedules(date_begin=date_begin, date_end=date_end)
    return xform.as_json()


# additional methods

@module.route('/api/integration/<int:api_version>/schedule2.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule2_schema(api_version):
    return Schedule2XForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/schedule2/<int:doctor_id>/')
@api_method(hook=hook)
def api_schedule2_get(api_version, doctor_id):
    args = request.args.to_dict()
    xform = Schedule2XForm(api_version)
    xform.check_params(None, doctor_id)
    xform.find_schedules(**args)
    return xform.as_json()
