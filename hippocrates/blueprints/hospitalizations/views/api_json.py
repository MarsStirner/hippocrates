# -*- coding: utf-8 -*-
from flask import request

from hippocrates.blueprints.hospitalizations.lib.data_ctrl import HospitalizationController
from nemesis.lib.apiutils import api_method
from hippocrates.blueprints.hospitalizations.app import module


@module.route('/api/0/current_hosps')
@api_method
def api_0_current_hosps_get():
    args = request.args.to_dict()
    ctrl = HospitalizationController()
    hosps_data = ctrl.get_current_hosps(**args)
    return hosps_data
