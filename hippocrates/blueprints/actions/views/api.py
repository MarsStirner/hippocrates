# -*- coding: utf-8 -*-
import collections
import datetime

from flask import request, abort, url_for

from flask.ext.login import current_user

from ..app import module
from blueprints.actions.lib.api import represent_action_template
from ..lib.api import update_template_action, is_template_action
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action, update_action, create_new_action, get_planned_end_datetime, int_get_atl_flat, \
    get_patient_location, delete_action
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.lib.subscriptions import notify_object, subscribe_user
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import safe_traverse, safe_datetime, parse_id, public_api, jsonify
from nemesis.models.actions import Action, ActionType, ActionTemplate
from nemesis.models.event import Event
from nemesis.models.exists import Person
from nemesis.models.utils import safe_current_user_id
from nemesis.models.rls import v_Nomen
from nemesis.systemwide import db, cache
from nemesis.lib.action.utils import check_at_service_requirement


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
    if is_template_action(action):
        return v.make_action_wo_sensitive_props(action)
    return v.make_action(action)


@module.route('/api/action/query/previous', methods=['GET'])
@api_method
def api_find_previous():
    client_id = request.args.get('client_id')
    at_id = request.args.get('at_id')
    action_id = request.args.get('id')

    if not (client_id and at_id):
        raise ApiException(400, u'Должны быть указаны и client_id и at_id')

    prev = Action.query.join(Event).filter(
        Event.client_id == client_id,
        Action.deleted == 0,
        Action.actionType_id == at_id,
    )
    if action_id:
        prev = prev.filter(Action.id < action_id)
    else:
        prev = prev.filter(Action.createDatetime < datetime.datetime.now())
    prev = prev.order_by(Action.id.desc()).first()
    if not prev:
        from nemesis.models.client import Client
        client = Client.query.get(client_id)
        action_type = ActionType.query.get(at_id)
        raise ApiException(404, u'У пациента "%s" других действий типа "%s" не найдено' % (client.nameText, action_type.name))
    return ActionVisualizer().make_action_wo_sensitive_props(prev)



@module.route('/api/action/', methods=['DELETE'])
@module.route('/api/action/<int:action_id>', methods=['DELETE'])
@api_method
def api_delete_action(action_id=None):
    if not action_id:
        raise ApiException(404, "Argument 'action_id' cannot be found.")
    action = Action.query.get(action_id)
    if not action:
        raise ApiException(404, "Действие с id=%s не найдено" % action_id)
    try:
        delete_action(action)
    except Exception, e:
        raise ApiException(403, unicode(e))
    db.session.commit()


@module.route('/api/action/', methods=['POST'])
@module.route('/api/action/<int:action_id>', methods=['POST'])
@api_method
def api_action_post(action_id=None):
    notifications = []
    subscriptions = []
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
        'office': action_desc['office'],
        'prescriptions': action_desc.get('prescriptions')
    }
    service_data = action_desc.get('service')
    properties_desc = action_desc['properties']
    if action_id:
        data['properties'] = properties_desc
        action = Action.query.get(action_id)
        if not action:
            raise ApiException(404, 'Action %s not found' % action_id)
        if not UserUtils.can_edit_action(action):
            raise ApiException(403, 'User cannot edit action %s' % action_id)
        if person_id != action.person_id:
            if person_id:
                notifications.append({
                    'person_id': person_id,
                    'reason': 'exec_assigned',
                })
                subscriptions.append(person_id)
            if action.person_id:
                notifications.append({
                    'person_id': action.person_id,
                    'reason': 'exec_unassigned',
                })
        if set_person_id != action.setPerson_id:
            subscriptions.append(set_person_id)
        action = update_action(action, **data)
    else:
        at_id = safe_traverse(action_desc, 'action_type', 'id', default=action_desc['action_type_id'])
        if not at_id:
            raise ApiException(404, u'Невозможно создать действие без указания типа action_type.id')
        event_id = action_desc['event_id']
        if not UserUtils.can_create_action(event_id, at_id):
            raise ApiException(403, (
                u'У пользовател нет прав на создание действия с ActionType id = %s '
                u'для обращения с event id = %s') % (at_id, event_id)
            )
        if set_person_id:
            subscriptions.append(set_person_id)
        if person_id:
            subscriptions.append(person_id)
            notifications.append({
                'person_id': person_id,
                'reason': 'exec_assigned',
            })
        try:
            action = create_new_action(at_id, event_id, properties=properties_desc, data=data,
                                       service_data=service_data)
        except Exception, e:
            raise ApiException(500, e.message)

    db.session.add(action)
    db.session.commit()

    object_id = 'hitsl.action.%s' % action.id

    data = {
        'action_name': action.actionType.name,
        'client_name': action.event.client.nameText,
        'action_url': url_for('actions.html_action', action_id=action.id),
        'client_url': url_for('patients.patient_info_full', client_id=action.event.client_id),
    }

    for pid in subscriptions:
        subscribe_user(pid, object_id)

    reasons_dict = collections.defaultdict(list)

    for d in notifications:
        reasons_dict[d['person_id']].append(d['reason'])

    notify_object(object_id, reasons_dict, data, 'altered')

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
    if not (0 <= at_class < 4):
        return abort(401)
    result = int_get_atl_flat(at_class, event_type_id)

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
        service_data = j.get('service')
        action = create_new_action(
            action_type_id,
            event_id,
            assigned=assigned,
            data=data,
            service_data=service_data
        )
        db.session.add(action)

    db.session.commit()


@module.route('/api/templates/<type_id>', methods=['GET'])
@public_api
@api_method
def api_action_template_list(type_id):
    user_id = request.args.get('user_id') or safe_current_user_id()
    speciality_id = request.args.get('speciality_id') or (
        getattr(current_user, 'speciality_id', None) if current_user is not None else None
    )
    templates = ActionTemplate.query.outerjoin(Action).filter(
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
    return map(represent_action_template, templates)


@module.route('/api/templates/<type_id>', methods=['PUT'])
@module.route('/api/templates/<type_id>/<id_>', methods=['POST'])
@public_api
@api_method
def api_action_template_save(type_id, id_=None):
    data = request.get_json()
    now = datetime.datetime.now()
    user_id = data.get('user_id') or safe_current_user_id()
    speciality_id = data.get('speciality_id') or (
        getattr(current_user, 'speciality_id', None) if current_user is not None else None
    )

    with db.session.no_autoflush:
        src_action = None
        action_id = data.get('aid')
        if action_id:
            src_action = Action.query.get(action_id)

        if id_ is None:
            template = ActionTemplate()
            db.session.add(template)
            template.createDatetime = now
            template.createPerson_id = user_id
            template.deleted = 0
            template.sex = 0
            template.age = ''
        else:
            template = ActionTemplate.query.join(Action).filter(
                ActionTemplate.deleted == 0,
                Action.actionType_id == type_id,
            ).first()
        if not template:
            raise ApiException(404, 'Template not found')

        if not template.action and src_action:
            action = Action()
            template.action = action
            update_template_action(action, src_action)
            db.session.add(action)

        elif template.action and action_id:
            update_template_action(template.action, src_action)

        elif template.action and 'aid' in data and data['aid'] is None:
            action = template.action
            template.action = None
            db.session.delete(action)

        template.modifyDatetime = now
        template.modifyPerson_id = user_id

        if 'gid' in data:
            template.group_id = data['gid']
        if 'name' in data:
            template.name = data['name']
        if 'code' in data:
            template.code = data['code']
        if 'owner' in data:
            if data['owner']:
                template.owner_id = user_id
            else:
                template.owner_id = None
        if 'speciality' in data:
            if data['speciality']:
                template.speciality_id = speciality_id
            else:
                template.speciality_id = None
        if template.code is None:
            template.code = ''

        db.session.commit()
        return represent_action_template(template)


@module.route('/api/search_rls.json')
def api_search_rls():
    try:
        query_string = request.args['q']
        limit = int(request.args.get('limit', 100))
    except (KeyError, ValueError):
        return abort(404)

    base_query = v_Nomen.query

    if query_string:
        query_string = u'{0}%'.format(query_string)
        base_query = base_query.filter(v_Nomen.tradeLocalName.like(query_string))

    result = base_query.limit(limit).all()
    return jsonify(result)


@module.route('/api/check_service_requirement/')
@module.route('/api/check_service_requirement/<int:action_type_id>')
@api_method
def api_check_action_service_requirement(action_type_id=None):
    if not action_type_id:
        raise ApiException(404, '`action_type_id` reuqired')

    try:
        res = check_at_service_requirement(action_type_id)
    except Exception, e:
        raise ApiException(500, e.message)
    return res