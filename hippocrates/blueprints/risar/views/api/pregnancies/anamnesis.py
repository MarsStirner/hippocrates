# -*- coding: utf-8 -*-
import datetime
import logging

from flask import request
from flask_login import current_user

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_anamnesis, represent_mother_action, \
    represent_father_action
from hippocrates.blueprints.risar.lib.utils import get_action
from hippocrates.blueprints.risar.models.risar import RisarRiskGroup
from hippocrates.blueprints.risar.risar_config import risar_father_anamnesis, risar_mother_anamnesis
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.client import BloodHistory
from nemesis.models.event import Event
from nemesis.systemwide import db

logger = logging.getLogger('simple')


__author__ = 'mmalkov'

@module.route('/api/0/pregnancy/chart/<int:event_id>/anamnesis', methods=['GET'])
@api_method
def api_0_chart_anamnesis(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    return {
        'client_id': event.client.id,
        'anamnesis': represent_pregnancy_anamnesis(card),
    }


@module.route('/api/0/pregnancy/chart/<int:event_id>/mother', methods=['GET', 'POST'])
@api_method
def api_0_chart_mother(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    if not event:
        raise ApiException(404, 'Event not found')
    if request.method == 'GET':
        action = get_action(event, risar_mother_anamnesis)
    else:
        action = get_action(event, risar_mother_anamnesis, True)
        for code, value in request.get_json().iteritems():
            if code not in ('id', 'blood_type') and code in action.propsByCode:
                action.propsByCode[code].value = value
            elif code == 'blood_type' and value:
                mother_blood_type = BloodHistory.query \
                    .filter(BloodHistory.client_id == event.client_id) \
                    .order_by(BloodHistory.bloodDate.desc()) \
                    .first()
                if mother_blood_type and value['id'] != mother_blood_type.bloodType_id or not mother_blood_type:
                    n = BloodHistory.create(value['id'], datetime.date.today(), current_user.id, event.client)
                    db.session.add(n)
        db.session.add(action)
        db.session.commit()
        card.reevaluate_card_attrs()
        db.session.commit()
    return represent_mother_action(action)


@module.route('/api/0/pregnancy/chart/<int:event_id>/father', methods=['GET', 'POST'])
@api_method
def api_0_chart_father(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)
    if not event:
        raise ApiException(404, 'Event not found')
    if request.method == 'GET':
        action = get_action(event, risar_father_anamnesis)
    else:
        action = get_action(event, risar_father_anamnesis, True)
        for code, value in request.get_json().iteritems():
            if code not in ('id', 'finished_diseases', 'current_diseases') and code in action.propsByCode:
                action.propsByCode[code].value = value
            elif (code == 'finished_diseases' or code == 'current_diseases') and value:
                prop = action.propsByCode[code]
                prop.value = value
        db.session.commit()
        card.reevaluate_card_attrs()
        db.session.commit()
    return represent_father_action(action)


@module.route('/api/0/pregnancy/chart/<int:event_id>/risks')
@api_method
def api_0_chart_risks(event_id):
    return RisarRiskGroup.query.filter(RisarRiskGroup.event_id == event_id, RisarRiskGroup.deleted == 0).all()


@module.route('/api/0/chart/<int:event_id>/radzinsky_risks')
@api_method
def api_0_chart_radzinsky_risks(event_id):
    from hippocrates.blueprints.risar.lib.radzinsky_risks.calc import get_event_radzinsky_risks_info
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    return get_event_radzinsky_risks_info(card.radz_risk, card)


@module.route('/api/0/rb_radzinsky_risks')
@api_method
def api_0_rb_radzinsky_riskfactors():
    from hippocrates.blueprints.risar.lib.radzinsky_risks.calc import radzinsky_risk_factors
    return radzinsky_risk_factors()
