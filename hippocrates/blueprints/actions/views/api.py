# -*- coding: utf-8 -*-
import datetime

from flask import request, abort
from flask.ext.login import current_user

from ..app import module
from ..lib.api import update_template_action
from nemesis.lib.agesex import AgeSex
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action, update_action, create_new_action, get_planned_end_datetime, int_get_atl_flat, \
    get_patient_location
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import safe_traverse, safe_datetime, parse_id
from nemesis.models.actions import Action, ActionType, ActionTemplate
from nemesis.models.event import Event
from nemesis.models.exists import Person
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db, cache


__author__ = 'viruzzz-kun'


prescriptionFlatCodes = (
    u'prescription',
    u'infusion',
    u'analgesia',
    u'chemotherapy',
)


@module.route('/api/action/new/')
@module.route('/api/action/new/<int:action_type_id>/<int:event_id>', methods=['GET'])
@api_method
def api_action_new_get(action_type_id, event_id):
    src_action_id = request.args.get('src_action_id')
    src_action = None
    if src_action_id:
        src_action = Action.query.get(src_action_id)

    action = create_action(action_type_id, event_id, src_action=src_action)

    v = ActionVisualizer()
    result = v.make_action(action)
    db.session.rollback()
    return result


@module.route('/api/action/')
@module.route('/api/action/<int:action_id>', methods=['GET'])
@api_method
def api_action_get(action_id):
    action = Action.query.get(action_id)
    v = ActionVisualizer()
    return v.make_action(action)


@module.route('/api/action/<int:action_id>/previous', methods=['GET'])
@api_method
def api_find_previous(action_id):
    action = Action.query.get(action_id)
    if not action:
        raise ApiException(404, u'Действие с id="%s" не найдено' % action_id)
    prev = Action.query.filter(
        Action.event_id == action.event_id,
        Action.deleted == 0,
        Action.begDate < action.begDate,
        Action.actionType_id == action.actionType_id,
    ).order_by(Action.id.desc()).first()
    if prev:
        v = ActionVisualizer()
        return v.make_action(prev)
    raise ApiException(404, u'В обращении %s других действий типа "%s" не найдено' % (action.event_id, action.actionType.name))


@module.route('/api/action/', methods=['DELETE'])
@module.route('/api/action/<int:action_id>', methods=['DELETE'])
@api_method
def api_delete_action(action_id=None):
    if not action_id:
        raise ApiException(404, "Argument 'action_id' cannot be found.")
    action = Action.query.get(action_id)
    if not action:
        raise ApiException(404, "Действие с id=%s не найдено" % action_id)
    if not UserUtils.can_delete_action(action):
        raise ApiException(403, u'У пользователя нет прав на удаление действия с id = %s' % action.id)

    action.delete()
    db.session.commit()


@module.route('/api/action/', methods=['POST'])
@module.route('/api/action/<int:action_id>', methods=['POST'])
@api_method
def api_action_post(action_id=None):
    action_desc = request.get_json()
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
        import pprint
        pprint.pprint(action_desc)
        at_id = safe_traverse(action_desc, 'action_type', 'id', default=action_desc['action_type_id'])
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


@module.route('/api/templates/<type_id>', methods=['GET'])
@api_method
def api_action_template_list(type_id):
    user_id = safe_current_user_id()
    speciality_id = current_user.speciality_id
    templates = ActionTemplate.query.join(Action).filter(
        db.and_(
            db.or_(
                ActionTemplate.owner_id == user_id,
                ActionTemplate.owner_id.is_(None)),
            db.or_(
                ActionTemplate.speciality_id == speciality_id,
                ActionTemplate.speciality_id.is_(None))
            ),
        db.or_(
            Action.actionType_id == type_id,
            ActionTemplate.action_id.is_(None)),
        ActionTemplate.deleted == 0,
    )
    return [
        {
            'id': at.id,
            'gid': at.group_id,
            'name': at.name,
            'aid': at.action_id,
            'con': AgeSex(at)
        }
        for at in templates
    ]


@module.route('/api/templates/<type_id>', methods=['PUT'])
@module.route('/api/templates/<type_id>/<id_>', methods=['POST'])
@api_method
def api_action_template_save(type_id, id_=None):
    data = request.get_json()
    now = datetime.datetime.now()
    if id_:
        template = ActionTemplate()
        template.createDatetime = now
        template.createPerson_id = safe_current_user_id()
    else:
        template = ActionTemplate.query.join(Action).filter(
            ActionTemplate.deleted == 0,
            Action.actionType_id == type_id,
        ).first()
    if not template:
        raise ApiException(404, 'Template not found')

    action_id = data.get('action_id')

    if not template.action and action_id:
        action = Action()
        db.session.add(action)
        update_template_action(action, action_id)
        template.action = action

    elif template.action and action_id:
        update_template_action(template.action, action_id)

    elif template.action and 'action' in data and data['action'] is None:
        action = template.action
        template.action = None
        db.session.delete(action)

    template.modifyDatetime = now
    template.modifyPerson_id = safe_current_user_id()

    if 'name' in data:
        template.name = data['name']
    if 'code' in data:
        template.code = data['code']
    if 'owner' in data:
        if data['owner']:
            template.owner_id = safe_current_user_id()
        else:
            template.owner_id = None
    if 'speciality' in data:
        if data['speciality']:
            template.speciality_id = current_user.speciality_id
        else:
            template.speciality_id = None

    db.session.add(template)
    db.commit()


