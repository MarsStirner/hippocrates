# -*- coding: utf-8 -*-
import datetime
from flask import request
from flask_login import current_user

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import GynecologicCard
from hippocrates.blueprints.risar.lib.represent.gyn import represent_gyn_anamnesis, represent_general_anamnesis_action
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.client import BloodHistory
from nemesis.models.event import Event
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'

_base = '/api/0/gyn/<int:event_id>/anamnesis'


@module.route(_base, methods=['GET'])
@api_method
def api_0_gyn_anamnesis(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Event не найден')
    card = GynecologicCard.get_for_event(event)
    return represent_gyn_anamnesis(card)


@module.route(_base + '/general', methods=['GET'])
@api_method
def api_0_gyn_anamnesis_general(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Event не найден')
    card = GynecologicCard.get_for_event(event)
    return represent_general_anamnesis_action(card.anamnesis)


@module.route(_base + '/general', methods=['POST'])
@api_method
def api_0_gyn_anamnesis_general_post(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Event не найден')
    card = GynecologicCard.get_for_event(event)
    action = card.anamnesis
    pbc = action.propsByCode
    for code, value in request.get_json().iteritems():
        if code not in ('id', 'blood_type') and code in pbc:
            pbc[code].value = value
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
    return represent_general_anamnesis_action(action)



