# -*- coding: utf-8 -*-
import datetime

from flask import request

from hippocrates.blueprints.hospitalizations.lib.data_ctrl import HospitalizationController
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_date
from hippocrates.blueprints.hospitalizations.app import module


@module.route('/api/0/current_hosps')
@api_method
def api_0_current_hosps_get():
    args = request.args.to_dict()
    for_date = safe_date(args.get('for_date')) or datetime.date.today()
    args['for_date'] = for_date

    ctrl = HospitalizationController()
    hosps_data = ctrl.get_current_hosps(**args)
    return hosps_data
