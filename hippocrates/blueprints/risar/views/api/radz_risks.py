# -*- coding: utf-8 -*-
import json

from hippocrates.blueprints.reports.jasper_client import JasperReport
from hippocrates.blueprints.risar.app import module
from flask import request, make_response

@module.route('/api/0/radz-print/', methods=['POST'])
def api_0_radz_print():
    data = dict(request.args)
    if request.form and request.form.get('json'):
        data.update(json.loads(request.form.get('json')))
    file_format = data.get('extension')
    fields_to_insert = ("event_idm", )
    data = dict((k, v) for k, v in data.items()
                if k in fields_to_insert)
    if data:
        jasper_report = JasperReport(
            'Radzinsky',
            '/reports/Hippocrates/Risar/Radzinsk',
            params=data
        )
        jasper_report.generate(file_format)
        return make_response(jasper_report.get_response_data())
