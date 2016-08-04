#! coding:utf-8
"""


@author: BARS Group
@date: 16.05.2016

"""
import json
from flask import make_response, request
from nemesis.lib.utils import jsonify, public_endpoint
from nemesis.app import app

from blueprints.reports.jasper_client import JasperReport
from blueprints.reports.models import rbRisarPrintTemplateMeta, RisarReports
from blueprints.reports.prepare import InputPrepare
from blueprints.risar.lib.specific import SpecificsManager
from .app import module


@module.route('/templates/')
@public_endpoint
def api_jr_templates():
    data = request.args
    locate_reports = data.get('folder')
    templates = JasperReport.get_reports(locate_reports)

    ext_url = SpecificsManager.get_reports_redirect_url()
    # these will be redirected to external system
    redirect_map = dict(RisarReports.query.values(
        RisarReports.template_uri, RisarReports.redirect_url)
    ) if ext_url is not None else {}

    res = []
    for t in templates:
        t_data = {
            'id': t['uri'],
            'code': t['label'],
            'name': t['description'],
        }
        if ext_url:
            t_data['redirect_to'] = ext_url + redirect_map[t['uri']]\
                if t['uri'] in redirect_map else None
        res.append(t_data)
    return jsonify(res)


@module.route('/templates-meta')
@public_endpoint
def api_jr_templates_meta():
    data = request.args
    template_uri = data.get('template_id')
    templates_meta = rbRisarPrintTemplateMeta.query.filter(
        rbRisarPrintTemplateMeta.template_uri == template_uri,
    ).all()
    return jsonify(templates_meta)


@public_endpoint
@module.route('/print_template', methods=["POST", "OPTIONS"])
def print_jr_templates_post():
    data = dict(request.args)
    if request.form and request.form.get('json'):
        data.update(json.loads(request.form.get('json')))
    report_data_list = [
        InputPrepare().report_data(doc)
        for doc in data.get('documents', [])
    ]
    # несколько отчетов на один запрос еще не поддерживается
    report_data = report_data_list[0]
    template_uri, template_code, params = report_data
    table_name, file_format = template_code.rsplit('.', 1)
    params.update({
        'mongo_host': app.config.get('MONGO_HOST', '10.1.2.11'),
        'mongo_port': app.config.get('MONGO_PORT', '27017'),
        'mongo_dbname': app.config.get('MONGO_DBNAME', 'nvesta'),
        'mongo_user': app.config.get('MONGO_USERNAME', ''),
        'mongo_pw': app.config.get('MONGO_PASSWORD', ''),
    })
    jasper_report = JasperReport(
        table_name,
        template_uri,
        params=params,
    )
    jasper_report.generate(file_format)
    return make_response(jasper_report.get_response_data())
