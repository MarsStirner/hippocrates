# -*- coding: utf-8 -*-
import json

from flask import request, make_response

from hippocrates.blueprints.reports.jasper_client import JasperReport
from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.radzinsky_risks.calc import get_event_radzinsky_risks_info, \
    radzinsky_risk_factors
from hippocrates.blueprints.risar.lib.radzinsky_risks.calc_regional_risks import get_event_regional_risks_info, \
    regional_risk_factors
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.models.risar import RisarRiskGroup

from nemesis.lib.apiutils import api_method
from nemesis.models.event import Event


@module.route('/api/0/pregnancy/chart/<int:event_id>/risks')
@api_method
def api_0_chart_risks(event_id):
    return RisarRiskGroup.query.filter(RisarRiskGroup.event_id == event_id, RisarRiskGroup.deleted == 0).all()


@module.route('/api/0/chart/<int:event_id>/radzinsky_risks')
@api_method
def api_0_chart_radzinsky_risks(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    return get_event_radzinsky_risks_info(card)


@module.route('/api/0/rb_radzinsky_risk_factors')
@api_method
def api_0_rb_radzinsky_riskfactors():
    return radzinsky_risk_factors()


@module.route('/api/0/chart/<int:event_id>/regional_risks')
@api_method
def api_0_chart_regional_risks(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    return get_event_regional_risks_info(card)


@module.route('/api/0/rb_regional_risk_factors')
@api_method
def api_0_rb_regional_riskfactors():
    return regional_risk_factors()


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
