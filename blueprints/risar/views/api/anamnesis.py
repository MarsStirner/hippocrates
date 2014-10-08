# -*- coding: utf-8 -*-
from flask import request
import itertools
from application.lib.data import create_action
from application.models.actions import Action, ActionType
from application.lib.utils import jsonify, safe_traverse_attrs, safe_traverse
from application.models.event import Event
from application.models.client import BloodHistory, ClientAllergy, ClientIntoleranceMedicament
from application.systemwide import db, cache
from blueprints.risar.app import module
from blueprints.risar.lib.represent import represent_anamnesis_action, represent_event, represent_intolerance

__author__ = 'mmalkov'

risar_anamnesis_pregnancy = 'risar_anamnesis_pregnancy'
risar_anamnesis_transfusion = 'risar_anamnesis_transfusion'


@module.route('/api/0/anamnesis/')
@module.route('/api/0/anamnesis/<int:event_id>')
def api_0_anamnesis(event_id=None):
    if not event_id:
        return jsonify(None, 400, 'Event id must be provided')
    event = Event.query.get(event_id)
    if not event:
        return jsonify(None, 404, 'Event not found')
    mother = Action.query.join(ActionType).filter(
        Action.event_id == event_id,
        Action.deleted == 0,
        ActionType.flatCode == 'risar_mother_anamnesis'
    ).first()
    father = Action.query.join(ActionType).filter(
        Action.event_id == event_id,
        Action.deleted == 0,
        ActionType.flatCode == 'risar_father_anamnesis'
    ).first()
    represent_mother = represent_anamnesis_action(mother, True) if mother else None
    represent_father = represent_anamnesis_action(father, False) if father else None
    if represent_mother is not None:
        mother_blood_type = BloodHistory.query\
            .filter(BloodHistory.client_id == event.client_id)\
            .order_by(BloodHistory.bloodDate.desc())\
            .first()
        if mother_blood_type:
            represent_mother['blood_type'] = mother_blood_type.bloodType

    event = Event.query.get(event_id)
    allergies = ClientAllergy.query.filter(
        ClientAllergy.client_id == Event.client_id,
        ClientAllergy.deleted == 0)
    medical_intolerances = ClientIntoleranceMedicament.query.filter(
        ClientIntoleranceMedicament.client_id == Event.client_id,
        ClientIntoleranceMedicament.deleted == 0)

    return jsonify({
        'event': represent_event(event),
        'mother': represent_mother,
        'father': represent_father,
        'pregnancies': [
            dict(action_apt_values(action, pregnancy_apt_codes), id=action.id)
            for action in event.actions
            if action.actionType_id == get_action_type_id(risar_anamnesis_pregnancy)
        ],
        'transfusions': [
            dict(action_apt_values(action, transfusion_apt_codes), id=action.id)
            for action in event.actions
            if action.actionType_id == get_action_type_id(risar_anamnesis_transfusion)
        ],
        'intolerances': [
            represent_intolerance(obj)
            for obj in itertools.chain(event.client.allergies, event.client.intolerances)
        ]
    })


@cache.memoize()
def get_action_type_id(flat_code):
    selectable = db.select((ActionType.id, ), whereclause=ActionType.flatCode == flat_code, from_obj=ActionType)
    row = db.session.execute(selectable).first()
    if not row:
        return None
    return row[0]


pregnancy_apt_codes = ['number', 'year', 'pregnancyResult', 'alive', 'weight', 'cause_of_death', 'note']


def action_apt_values(action, codes):
    return dict((key, safe_traverse_attrs(action.propsByCode.get(key), 'value')) for key in codes)


# Беременности

@module.route('/api/0/anamnesis/pregnancies/')
@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['GET'])
def api_0_pregnancies_get(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Pregnancy not found')
    return jsonify(dict(
        action_apt_values(action, pregnancy_apt_codes),
        id=action_id
    ))


@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['DELETE'])
def api_0_pregnancies_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Pregnancy not found')
    if action.deleted:
        return jsonify(None, 400, 'Pregnancy already deleted')
    action.deleted = 1
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/pregnancies/<int:action_id>/undelete', methods=['POST'])
def api_0_pregnancies_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Pregnancy not found')
    if not action.deleted:
        return jsonify(None, 400, 'Pregnancy not deleted')
    action.deleted = 0
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/pregnancies/', methods=['POST'])
@module.route('/api/0/anamnesis/pregnancies/<int:action_id>', methods=['POST'])
def api_0_pregnancies_post(action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_pregnancy)
    if action_id is None:
        event_id = request.args.get('event_id', None)
        if event_id is None:
            return jsonify(None, 400, 'Event is not set')
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id)
        if action is None:
            return jsonify(None, 404, 'Action not found')
    json = request.get_json()
    for key in pregnancy_apt_codes:
        action.propsByCode[key].value = json.get(key)
    db.session.add(action)
    db.session.commit()
    return jsonify(dict(
        action_apt_values(action, pregnancy_apt_codes),
        id=action.id
    ))


# Переливания

transfusion_apt_codes = ['date', 'type', 'blood_type', 'reaction']


@module.route('/api/0/anamnesis/transfusions/')
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['GET'])
def api_0_transfusions_get(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Transfusion not found')
    return jsonify(dict(
        action_apt_values(action, transfusion_apt_codes),
        id=action_id
    ))


@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['DELETE'])
def api_0_transfusions_delete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Transfusion not found')
    if action.deleted:
        return jsonify(None, 400, 'Transfusion already deleted')
    action.deleted = 1
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/transfusions/<int:action_id>/undelete', methods=['POST'])
def api_0_transfusions_undelete(action_id):
    action = Action.query.get(action_id)
    if action is None:
        return jsonify(None, 404, 'Transfusion not found')
    if not action.deleted:
        return jsonify(None, 400, 'Transfusion not deleted')
    action.deleted = 0
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/transfusions/', methods=['POST'])
@module.route('/api/0/anamnesis/transfusions/<int:action_id>', methods=['POST'])
def api_0_transfusions_post(action_id=None):
    actionType_id = get_action_type_id(risar_anamnesis_transfusion)
    event_id = request.args.get('event_id', None)
    if action_id is None:
        if event_id is None:
            return jsonify(None, 400, 'Event is not set')
        action = create_action(actionType_id, event_id)
    else:
        action = Action.query.get(action_id)
        if action is None:
            return jsonify(None, 404, 'Action not found')
    json = request.get_json()
    for key in transfusion_apt_codes:
        action.propsByCode[key].value = json.get(key)
    db.session.add(action)
    db.session.commit()
    return jsonify(dict(
        action_apt_values(action, transfusion_apt_codes),
        id=action.id
    ))


# Аллергии и медикаментозные непереносимости

def intolerance_class_from_type(i_type):
    if i_type == 'allergy':
        return ClientAllergy
    elif i_type == 'medicine':
        return ClientIntoleranceMedicament


@module.route('/api/0/anamnesis/intolerances/')
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['GET'])
def api_0_intolerances_get(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        return jsonify(None, 404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        return jsonify(None, 404, 'Object not found')
    return jsonify(dict(
        represent_intolerance(obj),
        id=object_id
    ))


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['DELETE'])
def api_0_intolerances_delete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        return jsonify(None, 404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        return jsonify(None, 404, 'Allergy not found')
    if obj.deleted:
        return jsonify(None, 400, 'Allergy already deleted')
    obj.deleted = 1
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>/undelete', methods=['POST'])
def api_0_intolerances_undelete(i_type, object_id):
    c = intolerance_class_from_type(i_type)
    if c is None:
        return jsonify(None, 404, 'Intolerance type not found')
    obj = c.query.get(object_id)
    if obj is None:
        return jsonify(None, 404, 'Allergy not found')
    if not obj.deleted:
        return jsonify(None, 400, 'Allergy not deleted')
    obj.deleted = 0
    db.session.commit()
    return jsonify(True)


@module.route('/api/0/anamnesis/intolerances/<i_type>/', methods=['POST'])
@module.route('/api/0/anamnesis/intolerances/<i_type>/<int:object_id>', methods=['POST'])
def api_0_intolerances_post(i_type, object_id=None):
    c = intolerance_class_from_type(i_type)
    if c is None:
        return jsonify(None, 404, 'Intolerance type not found')
    client_id = request.args.get('client_id', None)
    if object_id is None:
        if client_id is None:
            return jsonify(None, 400, 'Client is not set')
        obj = c()
    else:
        obj = c.query.get(object_id)
        if obj is None:
            return jsonify(None, 404, 'Action not found')
    json = request.get_json()
    obj.name = json.get('name')
    obj.client_id = client_id
    obj.power = safe_traverse(json, 'power', 'id')
    obj.createDate = json.get('date')
    obj.notes = json.get('note')
    db.session.add(obj)
    db.session.commit()
    return jsonify(
        represent_intolerance(obj)
    )