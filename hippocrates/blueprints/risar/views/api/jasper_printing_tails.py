# -*- coding: utf-8 -*-

# МЕНЯ ЗАСТАВИЛИ!!!

import json

from flask import request

from hippocrates.blueprints.reports.jasper_client import JasperReport
from hippocrates.blueprints.risar.app import module

__author__ = 'viruzzz-kun'


@module.route('/printing/checkup-ticket-25', methods=['POST'])
def printing_checkup_ticket_25():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'form25_1u',
        '/reports/Hippocrates/Risar/form25_1u',
        params={
            'action_id': str(data['action_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()


@module.route('/printing/epicrisis', methods=['POST'])
def printing_jsp_epicrisis():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'epicrisis',
        '/reports/Hippocrates/Risar/epicrisis',
        params={
            'action_id': str(data['action_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()


