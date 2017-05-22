# -*- coding: utf-8 -*-
import datetime

from flask import request

from hippocrates.blueprints.hospitalizations.lib.data_ctrl import HospitalizationController
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_datetime, safe_bool
from hippocrates.blueprints.hospitalizations.app import module


@module.route('/api/0/hosp_list')
@api_method
def api_0_hosp_list_get():
    args = request.args.to_dict()

    if 'for_date' in args:
        for_date = safe_datetime(args['for_date'])
        start_dt = for_date.replace(hour=8, minute=0, second=0, microsecond=0)
        end_dt = start_dt + datetime.timedelta(days=1)
    else:
        start_dt = safe_datetime(args.pop('start_dt', None))
        end_dt = safe_datetime(args.pop('end_dt', None))
    if not start_dt or not end_dt:
        raise ApiException(400, u'Не передан диапазон дат start_dt, end_dt или параметр for_date')
    history = safe_bool(args.pop('history', None)) or False

    ctrl = HospitalizationController()
    hosps_data = ctrl.get_hosps(start_dt, end_dt, history, **args)
    return hosps_data


@module.route('/api/0/hosps_stats')
@api_method
def api_0_hosps_stats_get():
    args = request.args.to_dict()

    if 'for_date' in args:
        for_date = safe_datetime(args['for_date'])
        start_dt = for_date.replace(hour=8, minute=0, second=0, microsecond=0)
        end_dt = start_dt + datetime.timedelta(days=1)
    else:
        start_dt = safe_datetime(args.pop('start_dt', None))
        end_dt = safe_datetime(args.pop('end_dt', None))
    if not start_dt or not end_dt:
        raise ApiException(400, u'Не передан диапазон дат start_dt, end_dt или параметр for_date')
    history = safe_bool(args.pop('history', None)) or False

    ctrl = HospitalizationController()
    hosps_stats = ctrl.get_hosps_stats(start_dt, end_dt, history, **args)
    return hosps_stats
