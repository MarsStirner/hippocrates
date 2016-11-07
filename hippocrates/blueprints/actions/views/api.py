# -*- coding: utf-8 -*-
import collections
import datetime
import logging
import uuid

from flask import request, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload, aliased

from hippocrates.blueprints.actions.lib.models import ActionAutoSave, ActionAutoSaveUnsaved
from ..app import module
from hippocrates.blueprints.actions.lib.api import represent_action_template
from ..lib.api import update_template_action, is_template_action
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action, update_action, create_new_action, get_planned_end_datetime, int_get_atl_flat, \
    get_patient_location, delete_action, ActionServiceException, fit_planned_end_date
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.jsonify import ActionVisualizer
from nemesis.lib.subscriptions import notify_object, subscribe_user
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import safe_traverse, safe_datetime, parse_id, public_api, safe_bool, bail_out, safe_int
from nemesis.models.actions import Action, ActionType, ActionTemplate
from nemesis.models.event import Event
from nemesis.models.exists import Person
from nemesis.models.utils import safe_current_user_id
from nemesis.models.rls import rlsNomen, rlsTradeName
from nemesis.systemwide import db


__author__ = 'viruzzz-kun'


logger = logging.getLogger('simple')


prescriptionFlatCodes = (
    u'prescription',
    u'infusion',
    u'analgesia',
    u'chemotherapy',
)


def delete_all_autosaves(action_id):
    ActionAutoSave.query.filter(
        ActionAutoSave.action_id == action_id,
    ).delete()


def delete_all_autounsaves(action_type_id, event_id):
    ActionAutoSaveUnsaved.query.filter(
        ActionAutoSaveUnsaved.actionType_id == action_type_id,
        ActionAutoSaveUnsaved.event_id == event_id,
        ActionAutoSaveUnsaved.user_id == safe_current_user_id(),
    ).delete()


@module.route('/api/action/new/')
@module.route('/api/action/new/<int:action_type_id>/<int:event_id>', methods=['GET'])
@api_method
def api_action_new_get(action_type_id, event_id):
    with db.session.no_autoflush:
        src_action_id = request.args.get('src_action_id')
        src_action = None
        if src_action_id:
            src_action = Action.query.get(src_action_id)

        autosave = ActionAutoSaveUnsaved.query.filter(
            ActionAutoSaveUnsaved.actionType_id == action_type_id,
            ActionAutoSaveUnsaved.event_id == event_id,
            ActionAutoSaveUnsaved.user_id == safe_current_user_id(),
        ).first()

        action = create_action(action_type_id, event_id, src_action=src_action)

        if autosave and autosave.data:
            data = prepare_action_data(autosave.data)
            update_action(action, **data)

        v = ActionVisualizer()
        result = v.make_action(action)
        db.session.rollback()
        return result


@module.route('/api/action/')
@module.route('/api/action/<int:action_id>', methods=['GET'])
@api_method
def api_action_get(action_id):
    with db.session.no_autoflush:
        action = Action.query.options(
            joinedload(Action.actionType),
            joinedload(Action.event),
            joinedload(Action.person),
            joinedload(Action.properties),
            joinedload(Action.medication_prescriptions),
            joinedload(Action.diagnoses),
        ).filter(Action.id == action_id).first() or bail_out(ApiException(404, u'Документ не найден'))
        v = ActionVisualizer()
        if is_template_action(action):
            return v.make_action_wo_sensitive_props(action)
        autosave = ActionAutoSave.query.filter(
            ActionAutoSave.action_id == action_id,
            ActionAutoSave.user_id == safe_current_user_id(),
        ).first()
        if autosave and autosave.data:
            data = prepare_action_data(autosave.data)
            update_action(action, **data)
            v.ignore_status = True
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
        raise ApiException(404, u"Argument 'action_id' cannot be found.")
    action = Action.query.get(action_id)
    if not action:
        raise ApiException(404, u"Действие с id=%s не найдено" % action_id)
    try:
        delete_action(action)
    except Exception, e:
        raise ApiException(403, unicode(e))
    delete_all_autosaves(action_id)
    db.session.commit()


@module.route('/api/action/<int:action_id>/autosave/', methods=['POST'])
@api_method
def api_action_autosave(action_id):
    autosave = ActionAutoSave.query.filter(
        ActionAutoSave.action_id == action_id,
        ActionAutoSave.user_id == safe_current_user_id(),
    ).first()
    if not autosave:
        autosave = ActionAutoSave()
        autosave.action_id = action_id
        db.session.add(autosave)
    autosave.data = request.get_json()
    db.session.commit()


@module.route('/api/action/<int:action_id>/autosave/', methods=['DELETE'])
@api_method
def api_action_autosave_delete(action_id):
    ActionAutoSave.query.filter(
        ActionAutoSave.action_id == action_id,
        ActionAutoSave.user_id == safe_current_user_id(),
    ).delete()
    db.session.commit()


@module.route('/api/action/new/autosave/<int:event_id>/<int:action_type_id>/', methods=['POST'])
@api_method
def api_action_autosave_unsaved(event_id, action_type_id):
    data = request.get_json()
    autosave = ActionAutoSaveUnsaved.query.filter(
        ActionAutoSaveUnsaved.actionType_id == action_type_id,
        ActionAutoSaveUnsaved.event_id == event_id,
        ActionAutoSaveUnsaved.user_id == safe_current_user_id(),
    ).first()
    if not autosave:
        autosave = ActionAutoSaveUnsaved()
        autosave.actionType_id = action_type_id
        autosave.event_id = event_id
        db.session.add(autosave)
    autosave.data = data
    db.session.commit()


@module.route('/api/action/new/autosave/<int:event_id>/<int:action_type_id>/', methods=['DELETE'])
@api_method
def api_action_autosave_delete_unsaved(event_id, action_type_id):
    ActionAutoSaveUnsaved.query.filter(
        ActionAutoSaveUnsaved.actionType_id == action_type_id,
        ActionAutoSaveUnsaved.event_id == event_id,
        ActionAutoSaveUnsaved.user_id == safe_current_user_id(),
    ).delete()
    db.session.commit()


def prepare_action_data(action_desc):
    data = {}
    if 'beg_date' in action_desc:
        data['begDate'] = safe_datetime(action_desc['beg_date'])
    if 'end_date' in action_desc:
        data['endDate'] = safe_datetime(action_desc['end_date'])
    if 'planned_end_date' in action_desc:
        data['plannedEndDate'] = safe_datetime(action_desc['planned_end_date'])
    if 'direction_date' in action_desc:
        data['directionDate'] = safe_datetime(action_desc['direction_date'])
    if 'is_urgent' in action_desc:
        data['isUrgent'] = action_desc['is_urgent']
    if 'set_person' in action_desc:
        set_person_id = safe_traverse(action_desc, 'set_person', 'id')
        data['setPerson_id'] = set_person_id
        data['setPerson'] = Person.query.get(set_person_id) if set_person_id else None
    if 'person' in action_desc:
        person_id = safe_traverse(action_desc, 'person', 'id')
        data['person_id'] = person_id
        data['person'] = Person.query.get(person_id) if person_id else None
    if 'status' in action_desc:
        data['status'] = safe_traverse(action_desc, 'status', 'id')
    if 'note' in action_desc:
        data['note'] = action_desc['note']
    if 'amount' in action_desc:
        data['amount'] = action_desc['amount']
    data['account'] = action_desc.get('account') or 0
    if 'uet' in action_desc:
        data['uet'] = action_desc['uet']
    data['payStatus'] = action_desc.get('payStatus') or 0
    if 'coord_date' in action_desc:
        data['coordDate'] = safe_datetime(action_desc['coord_date'])
    if 'office' in action_desc:
        data['office'] = action_desc['office']

    data['prescriptions'] = action_desc.get('prescriptions')
    data['properties'] = action_desc.get('properties')
    return data


@module.route('/api/action/', methods=['POST'])
@module.route('/api/action/<int:action_id>', methods=['POST'])
@api_method
def api_action_post(action_id=None):
    notifications = []
    subscriptions = []
    action_desc = request.get_json()
    set_person_id = safe_traverse(action_desc, 'set_person', 'id')
    person_id = safe_traverse(action_desc, 'person', 'id')
    data = prepare_action_data(action_desc)
    if action_id:
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
        delete_all_autosaves(action_id)
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
            properties_desc = data.pop('properties')
            service_data = action_desc.get('service')
            action = create_new_action(at_id, event_id, properties=properties_desc, data=data, service_data=service_data)
        except ActionServiceException, e:
            logger.error(unicode(e), exc_info=True)
            raise ApiException(500, u'Ошибка в настройках услуг и прайс-листов')
        delete_all_autounsaves(at_id, event_id)

    diagnoses_data = action_desc.get('diagnoses')
    if diagnoses_data:
        create_or_update_diagnoses(action, diagnoses_data)

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
        raise ApiException(404, u'Некорректное значение параметра action_type_id')
    at = ActionType.query.get(at_id)
    if not at:
        raise ApiException(404, u'Не найден тип действия ActionType.id = %s' % at_id)

    ped = get_planned_end_datetime(at_id)

    event_id = request.args.get('event_id')
    if event_id:
        event = db.session.query(Event).get(event_id)
        ped = fit_planned_end_date(ped, event)

    return {
        'ped': ped
    }


@module.route('/api/action-types/flat/')
@module.route('/api/action-types/flat/<int:at_class>/')
@module.route('/api/action-types/flat/<int:at_class>/<int:event_type_id>/')
@api_method
def api_atl_get_flat(at_class, event_type_id=None):
    if not (0 <= at_class < 4):
        raise ApiException(404, u'Класс типа действия должен быть 0, 1, 2, или 3. Получен %s' % at_class)
    result = map(tuple, int_get_atl_flat(at_class, event_type_id).values())
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
            'plannedEndDate': safe_datetime(j['planned_end_date']),
            'isUrgent': safe_bool(j.get('urgent', False))
        }
        service_data = j.get('service')
        ttj_data = j.get('ttj')
        try:
            action = create_new_action(
                action_type_id,
                event_id,
                assigned=assigned,
                data=data,
                service_data=service_data,
                ttj_data=ttj_data
            )
        except Exception, e:
            logger.exception(e.message)
            raise ApiException(500, e.message)
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
            action.uuid = uuid.uuid4()
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
@api_method
def api_search_rls():
    if 'q' not in request.args:
        raise ApiException(400, u'Текст запроса должен быть указан в аргументе "q"')
    query_string = request.args['q']
    try:
        limit = int(request.args.get('limit', 100))
    except ValueError:
        raise ApiException(400, u'Аргумент "limit" должен быть числом')

    base_query = rlsNomen.query

    if query_string:
        query_string = u'{0}%'.format(query_string)
        base_query = base_query \
            .outerjoin(rlsTradeName) \
            .filter(rlsTradeName.localName.like(query_string))

    return base_query.limit(limit).all()


@module.route('/api/search_actions.json', methods=["POST"])
@api_method
def api_search_actions():
    flt = request.get_json()
    context = ActionVisualizer()

    base_query = Action.query.join(Event).filter(
        Action.deleted == 0,
        Event.deleted == 0,
    )
    PersonExec = aliased(Person, name='PersonExec')
    PersonSet = aliased(Person, name='PersonSet')

    if 'id' in flt:
        action = base_query.filter(Action.id == flt['id']).first()
        return {
            'pages': 1,
            'items': [context.make_searched_action(action)] if action else []
        }
    if not any(param in flt for param in ('beg_date_from', 'beg_date_to', 'ped_from', 'ped_to', 'client_id')):
        raise ApiException(422, u'Для проведения поиска необходимо указать интересующий диапазон '
                                u'дат или выбрать пациента')
    if 'status_id' in flt:
        base_query = base_query.filter(Action.status == flt['status_id'])
    if 'client_id' in flt:
        base_query = base_query.filter(Event.client_id == flt['client_id'])
    if 'action_type_id_list' in flt:
        base_query = base_query.filter(Action.actionType_id.in_(flt['action_type_id_list']))
    if 'beg_date_from' in flt:
        base_query = base_query.filter(Action.begDate >= safe_datetime(flt['beg_date_from']))
    if 'beg_date_to' in flt:
        base_query = base_query.filter(Action.begDate <= safe_datetime(flt['beg_date_to']))
    if 'ped_from' in flt:
        base_query = base_query.filter(Action.plannedEndDate >= safe_datetime(flt['ped_from']))
    if 'ped_to' in flt:
        base_query = base_query.filter(Action.plannedEndDate <= safe_datetime(flt['ped_to']))
    if 'set_person_id' in flt:
        base_query = base_query.filter(Action.setPerson_id == flt['set_person_id'])
    if 'person_id' in flt:
        base_query = base_query.filter(Action.person_id == flt['person_id'])
    if 'person_org_structure_id' in flt:
        base_query = base_query.join(
            PersonExec, Action.person_id == PersonExec.id
        ).filter(
            PersonExec.orgStructure_id == flt['person_org_structure_id']
        )

    order_options = flt.get('sorting_params')
    if order_options:
        def is_joined(q, model_class):
            for mapper in q._join_entities:
                if mapper.class_ == model_class or mapper.entity == model_class:
                    return True
            return False

        desc_order = order_options['order'] == 'DESC'
        col_name = order_options['column_name']
        if col_name == 'at_name':
            if not is_joined(base_query, ActionType):
                base_query = base_query.join(ActionType)
            base_query = base_query.order_by(ActionType.name.desc() if desc_order else ActionType.name)
        elif col_name == 'beg_date':
            base_query = base_query.order_by(Action.begDate.desc() if desc_order else Action.begDate)
        elif col_name == 'end_date':
            base_query = base_query.order_by(Action.endDate.desc() if desc_order else Action.endDate)
        elif col_name == 'ped':
            base_query = base_query.order_by(Action.plannedEndDate.desc() if desc_order else Action.plannedEndDate)
        elif col_name == 'set_person_short_name':
            if not is_joined(base_query, PersonSet):
                base_query = base_query.outerjoin(PersonSet, Action.setPerson_id == PersonSet.id)
            base_query = base_query.order_by(PersonSet.lastName.desc() if desc_order else PersonSet.lastName)
        elif col_name == 'person_short_name':
            if not is_joined(base_query, PersonExec):
                base_query = base_query.outerjoin(PersonExec, Action.person_id == PersonExec.id)
            base_query = base_query.order_by(PersonExec.lastName.desc() if desc_order else PersonExec.lastName)
    else:
        base_query = base_query.order_by(Action.begDate.desc())

    per_page = int(flt.get('per_page', 20))
    page = int(flt.get('page', 1))
    paginate = base_query.paginate(page, per_page, False)
    return {
        'pages': paginate.pages,
        'total': paginate.total,
        'items': [
            context.make_searched_action(action)
            for action in paginate.items
        ]
    }