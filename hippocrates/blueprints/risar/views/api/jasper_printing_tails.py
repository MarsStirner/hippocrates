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


@module.route('/printing/anamnesis', methods=['POST'])
def printing_jsp_anamnesis():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'anamnesis',
        '/reports/Hippocrates/Risar/anamnesis',
        params={
            'event_id': str(data['event_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()


@module.route('/printing/first-checkup', methods=['POST'])
def printing_first_checkup():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'first_checkup',
        '/reports/Hippocrates/Risar/first_checkup',
        params={
            'action_id': str(data['action_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()


@module.route('/printing/second-checkup', methods=['POST'])
def printing_second_checkup():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'second_checkup',
        '/reports/Hippocrates/Risar/second_checkup',
        params={
            'action_id': str(data['action_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()


@module.route('/printing/gyn-anamnesis', methods=['POST'])
def printing_jsp_gyn_anamnesis():
    data = request.args.to_dict()
    if request.form:
        data.update(json.loads(request.form.get('json', {})))
    file_format = data.get('extension', 'html')
    jasper_report = JasperReport(
        'gyn_anamnesis',
        '/reports/Hippocrates/Risar/anamnesis_gynecological',
        params={
            'event_id': str(data['event_id'])
        }
    )
    jasper_report.generate(file_format)
    return jasper_report.get_response_data()
