# -*- coding: utf-8 -*-
from flask import request, abort
from ..app import module
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action, update_action, create_new_action, get_planned_end_datetime, int_get_atl_flat, \
    get_patient_location
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import safe_traverse, safe_datetime, parse_id
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event
from nemesis.models.exists import Person
from nemesis.systemwide import db, cache

__author__ = 'viruzzz-kun'


prescriptionFlatCodes = (
    u'prescription',
    u'infusion',
    u'analgesia',
    u'chemotherapy',
)

@module.route('/api/actions', methods=['GET'])
@api_method
def api_action_get():
    action_id = int(request.args.get('action_id'))
    action = Action.query.get(action_id)
    v = ActionVisualizer()
    return v.make_action(action)


@module.route('/api/actions/new.json', methods=['GET'])
@api_method
def api_action_new_get():
    src_action = Action.query.get(int(request.args['src_action_id'])) \
        if 'src_action_id' in request.args else None
    action_type_id = int(request.args['action_type_id'])
    event_id = int(request.args['event_id'])

    action = create_action(action_type_id, event_id, src_action=src_action)

    v = ActionVisualizer()
    result = v.make_action(action)
    db.session.rollback()
    return result


@module.route('/api/actions', methods=['POST'])
@api_method
def api_action_post():
    action_desc = request.get_json()
    action_id = action_desc['id']
    set_person_id = safe_traverse(action_desc, 'set_person', 'id')
    person_id = safe_traverse(action_desc, 'person', 'id')
    data = {
        'begDate': safe_datetime(action_desc['beg_date']),
        'endDate': safe_datetime(action_desc['end_date']),
        'plannedEndDate': safe_datetime(action_desc['planned_end_date']),
        'directionDate': safe_datetime(action_desc['direction_date']),
        'isUrgent': action_desc['is_urgent'],
        'status': action_desc['status']['id'],
        'setPerson_id': set_person_id,
        'person_id':  person_id,
        'setPerson': Person.query.get(set_person_id) if set_person_id else None,
        'person':  Person.query.get(person_id) if person_id else None,
        'note': action_desc['note'],
        'amount': action_desc['amount'],
        'account': action_desc['account'] or 0,
        'uet': action_desc['uet'],
        'payStatus': action_desc['pay_status'] or 0,
        'coordDate': safe_datetime(action_desc['coord_date']),
        'office': action_desc['office']
    }
    properties_desc = action_desc['properties']
    if action_id:
        data['properties'] = properties_desc
        action = Action.query.get(action_id)
        if not action:
            raise ApiException(404, 'Action %s not found' % action_id)
        if not UserUtils.can_edit_action(action):
            raise ApiException(403, 'User cannot edit action %s' % action_id)
        action = update_action(action, **data)
    else:
        at_id = action_desc['action_type']['id']
        if not at_id:
            raise ApiException(404, u'Невозможно создать действие без указания типа action_type.id')
        event_id = action_desc['event_id']
        if not UserUtils.can_create_action(event_id, at_id):
            raise ApiException(403, (
                u'У пользовател нет прав на создание действия с ActionType id = %s '
                u'для обращения с event id = %s') % (at_id, event_id)
            )
        action = create_new_action(at_id, event_id, properties=properties_desc, data=data)

    db.session.add(action)
    db.session.commit()

    v = ActionVisualizer()
    return v.make_action(action)


@module.route('/api/action_type/planned_end_date.json', methods=['GET'])
@api_method
def api_get_action_ped():
    at_id = parse_id(request.args, 'action_type_id')
    if at_id is False:
        return abort(404)
    at = ActionType.query.get(at_id)
    if not at:
        return abort(404)
    return {
        'ped': get_planned_end_datetime(at_id)
    }


@cache.memoize(86400)
def int_get_atl(at_class):
    # not used?
    atypes = ActionType.query.filter(
        ActionType.class_ == at_class, ActionType.deleted == 0, ActionType.hidden == 0
    )
    at = dict((item.id, (item.name, item.group_id, item.code, set())) for item in atypes)
    for item_id, (name, gid, code, children) in at.iteritems():
        if gid in at:
            at[gid][3].add(item_id)

    def render_node(node_id):
        node = at[node_id]
        return {
            'id': node_id,
            'name': node[0],
            'code': node[2],
            'children': [render_node(child_id) for child_id in node[3]] if node[3] else None
        }

    result = {
        'id': None,
        'name': None,
        'code': None,
        'children': [
            render_node(item_id) for item_id, (name, gid, code, children) in at.iteritems() if not gid
        ]
    }

    def res_sort(node):
        if node['children']:
            node['children'].sort(key=lambda nd: nd['code'])
            for nd in node['children']:
                res_sort(nd)

    res_sort(result)
    return result


@module.route('/api/action-type-list.json')
@api_method
def api_atl_get():
    # not used?
    at_class = int(request.args['at_class'])
    if not (0 <= at_class < 4):
        return abort(401)

    result = int_get_atl(at_class)

    return result


@module.route('/api/action-type-list-flat.json')
@api_method
def api_atl_get_flat():
    at_class = int(request.args['at_class'])
    event_type_id = parse_id(request.args, 'event_type_id') or None
    contract_id = parse_id(request.args, 'contract_id') or None
    if not (0 <= at_class < 4):
        return abort(401)
    result = int_get_atl_flat(at_class, event_type_id, contract_id)

    return result


@module.route('/api/create-lab-direction.json', methods=['POST'])
@api_method
def api_create_lab_direction():
    ja = request.get_json()
    event_id = ja['event_id']
    event = Event.query.get(event_id)
    org_structure = get_patient_location(event)
    if not org_structure:
        raise ApiException(422, u'Пациент не привязан ни к одному из отделений')

    for j in ja['directions']:
        action_type_id = j['type_id']
        assigned = j['assigned']
        data = {
            'plannedEndDate': safe_datetime(j['planned_end_date'])
        }
        action = create_new_action(
            action_type_id,
            event_id,
            assigned=assigned,
            data=data
        )
        db.session.add(action)

    db.session.commit()
