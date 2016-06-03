# -*- coding: utf-8 -*-
import datetime
import logging
import itertools

from flask import request
from flask.ext.login import current_user

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.utils import get_action, action_apt_values, get_action_type_id
from blueprints.risar.models.risar import RisarRiskGroup
from blueprints.risar.lib.prev_children import create_or_update_prev_children
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action, create_action_property
from nemesis.lib.utils import safe_traverse, safe_date, safe_time, safe_int, safe_bool, safe_double
from nemesis.models.actions import Action
from nemesis.models.client import ClientAllergy, ClientIntoleranceMedicament, BloodHistory
from nemesis.models.event import Event
from nemesis.systemwide import db
from ...app import module
from ...lib.represent import represent_intolerance, represent_mother_action, represent_father_action, \
    represent_pregnancy, represent_anamnesis
from ...risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, risar_father_anamnesis, risar_mother_anamnesis

logger = logging.getLogger('simple')


__author__ = 'mmalkov'

# Беременности

@module.route('/api/0/anamnesis/pregnancies/')
@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['GET'])
@api_method
def api_0_pregnancies_get(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Pregnancy not found')
    return dict(
        action_apt_values(action, pregnancy_apt_codes),
        id=action_id
    )


@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_pregnancies_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Pregnancy not found')
    if action.deleted:
        raise ApiException(400, 'Pregnancy already deleted')
    action.deleted = 1
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/pregnancies/<int:action_id>/undelete', methods=['POST'])
@api_method
def api_0_pregnancies_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Pregnancy not found')
    if not action.deleted:
        raise ApiException(400, 'Pregnancy not deleted')
    action.deleted = 0
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/pregnancies/', methods=['POST'])
@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['POST'])
@api_method
def api_0_pregnancies_post(action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_pregnancy)
    if action_id is None:
        event_id = request.args.get('event_id', None)
        if event_id is None:
            raise ApiException(400, 'Event is not set')
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id)
        if action is None:
            raise ApiException(404, 'Action not found')
    event = Event.query.get(action.event_id)
    card = PregnancyCard.get_for_event(event)
    json = request.get_json()

    newborn_inspections = json.pop('newborn_inspections', [])

    # prev pregnancy
    prop_types = {p.code: p for p in action.actionType.property_types if p.code}
    for code in pregnancy_apt_codes:
        if code not in action.propsByCode:
            if code in prop_types:
                action.propsByCode[code] = create_action_property(action, prop_types[code])
            else:
                logger.info('Skipping "%s" in old/corrupted Action id = %s, flat_code = "%s"',
                            code, action_id, risar_anamnesis_pregnancy)
                continue
        action.propsByCode[code].value = json.get(code)

    # prev pregnancy children
    new_children, deleted_children = create_or_update_prev_children(action, newborn_inspections)
    for dc in deleted_children:
        db.session.delete(dc)
    db.session.add(action)
    db.session.add_all(new_children)
    db.session.commit()

    card.reevaluate_card_attrs()
    db.session.commit()
    return represent_pregnancy(action)


# Переливания

@module.route('/api/0/anamnesis/transfusions/')
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['GET'])
@api_method
def api_0_transfusions_get(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Transfusion not found')
    return dict(
        action_apt_values(action, transfusion_apt_codes),
        id=action_id
    )


@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['DELETE'])
@api_method
def api_0_transfusions_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Transfusion not found')
    if action.deleted:
        raise ApiException(400, 'Transfusion already deleted')
    action.deleted = 1
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/transfusions/<int:action_id>/undelete', methods=['POST'])
@api_method
def api_0_transfusions_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        raise ApiException(404, 'Transfusion not found')
    if not action.deleted:
        raise ApiException(400, 'Transfusion not deleted')
    action.deleted = 0
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/transfusions/', methods=['POST'])
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['POST'])
@api_method
def api_0_transfusions_post(action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_transfusion)
    event_id = request.args.get('event_id', None)
    if action_id is None:
        if event_id is None:
            raise ApiException(400, 'Event is not set')
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id)
        if action is None:
            raise ApiException(404, 'Action not found')
    json = request.get_json()
    for key in transfusion_apt_codes:
        action.propsByCode[key].value = json.get(key)
    db.session.add(action)
    db.session.commit()
    card = PregnancyCard.get_for_event(action.event)
    card.reevaluate_card_attrs()
    db.session.commit()
    return dict(
        action_apt_values(action, transfusion_apt_codes),
        id=action.id
    )


# Аллергии и медикаментозные непереносимости

def intolerance_class_from_type(i_type):
    if i_type == 'allergy':
        return ClientAllergy
    elif i_type == 'medicine':
        return ClientIntoleranceMedicament


@module.route('/api/0/anamnesis/intolerances/')
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['GET'])
@api_method
def api_0_intolerances_get(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, 'Object not found')
    return dict(
        represent_intolerance(obj),
        id=object_id
    )


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['DELETE'])
@api_method
def api_0_intolerances_delete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, 'Allergy not found')
    if obj.deleted:
        raise ApiException(400, 'Allergy already deleted')
    obj.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>/undelete', methods=['POST'])
@api_method
def api_0_intolerances_undelete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        raise ApiException(404, 'Allergy not found')
    if not obj.deleted:
        raise ApiException(400, 'Allergy not deleted')
    obj.deleted = 0
    db.session.commit()
    return True


@module.route('/api/0/anamnesis/intolerances/<i_type>/', methods=['POST'])
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['POST'])
@api_method
def api_0_intolerances_post(i_type, object_id=None):
    c = intolerance_class_from_type(i_type)
    if c is None:
        raise ApiException(404, 'Intolerance type not found')
    client_id = request.args.get('client_id', None)
    if object_id is None:
        if client_id is None:
            raise ApiException(400, 'Client is not set')
        obj = c()
    else:
        obj = c.query.get(object_id)
        if obj is None:
            raise ApiException(404, 'Action not found')
    json = request.get_json()
    obj.name = json.get('name')
    obj.client_id = client_id
    obj.power = safe_traverse(json, 'power', 'id')
    obj.createDate = json.get('date')
    obj.notes = json.get('note')
    db.session.add(obj)
    db.session.commit()
    return represent_intolerance(obj)


@module.route('/api/0/chart/<int:event_id>/anamnesis', methods=['GET'])
@api_method
def api_0_chart_anamnesis(event_id):
    event = Event.query.get(event_id)
    return {
        'client_id': event.client.id,
        'anamnesis': represent_anamnesis(event),
    }


@module.route('/api/0/chart/<int:event_id>/mother', methods=['GET', 'POST'])
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
    return represent_mother_action(event, action)


@module.route('/api/0/chart/<int:event_id>/father', methods=['GET', 'POST'])
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
    return represent_father_action(event, action)


@module.route('/api/0/chart/<int:event_id>/risks')
@api_method
def api_0_chart_risks(event_id):
    return RisarRiskGroup.query.filter(RisarRiskGroup.event_id == event_id, RisarRiskGroup.deleted == 0).all()


@module.route('/api/0/chart/<int:event_id>/radzinsky_risks')
@api_method
def api_0_chart_radzinsky_risks(event_id):
    from blueprints.risar.lib.radzinsky_risks.calc import get_event_radzinsky_risks_info
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    return get_event_radzinsky_risks_info(card.radz_risk)


@module.route('/api/0/rb_radzinsky_risks')
@api_method
def api_0_rb_radzinsky_riskfactors():
    from blueprints.risar.lib.radzinsky_risks.calc import radzinsky_risk_factors
    return radzinsky_risk_factors()
