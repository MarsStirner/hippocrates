# -*- coding: utf-8 -*-
import calendar
from collections import defaultdict
import datetime

from flask import abort, request
from flask.ext.login import current_user

from application.models.event import Event
from application.systemwide import db, cache
from application.lib.sphinx_search import SearchPerson
from application.lib.agesex import recordAcceptableEx
from application.lib.utils import (jsonify, safe_traverse, get_new_uuid, parse_id, safe_date, safe_time,
                                   string_to_datetime, safe_time_as_dt)
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.lib.data import delete_schedules
from application.models.exists import (rbSpeciality, rbReasonOfAbsence, rbPrintTemplate, Person)
from application.models.actions import Action, ActionType, ActionProperty, ActionPropertyType
from application.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType, \
    rbReceptionType, rbAttendanceType
from application.lib.jsonify import ScheduleVisualizer, PrintTemplateVisualizer, \
    ActionVisualizer


__author__ = 'mmalkov'


@module.route('/api/schedule.json')
@public_endpoint
def api_schedule():
    person_id_s = request.args.get('person_ids')
    client_id_s = request.args.get('client_id')
    start_date_s = request.args.get('start_date')
    one_day = bool(request.args.get('one_day', False))
    reception_type = request.args.get('reception_type')
    related = bool(request.args.get('related', False))
    try:
        start_date = datetime.datetime.strptime(start_date_s, '%Y-%m-%d').date()
        if one_day:
            end_date = start_date + datetime.timedelta(days=1)
        else:
            end_date = start_date + datetime.timedelta(weeks=1)
        client_id = int(client_id_s) if client_id_s else None
    except ValueError:
        return abort(400)

    result = {
        'schedules': [],
    }

    context = ScheduleVisualizer()
    context.client_id = client_id
    context.reception_type = reception_type

    if person_id_s and not person_id_s == '[]':
        if person_id_s.startswith('[') and person_id_s.endswith(']'):
            person_ids = set(int(person_id) for person_id in person_id_s[1:-1].split(','))
        else:
            try:
                person_ids = {int(person_id_s)}
            except ValueError:
                person_ids = set()
    else:
        person_ids = set()

    if related:
        if not client_id:
            return abort(400)
        persons = Person.query.\
            join(ScheduleClientTicket.ticket, ScheduleTicket.schedule, Schedule.person).\
            filter(start_date <= Schedule.date, Schedule.date <= end_date).\
            filter(ScheduleClientTicket.client_id == client_id, ScheduleClientTicket.deleted == 0).\
            distinct()
        related_schedules = context.make_persons_schedule(persons, start_date, end_date)
        related_person_ids = set(person.id for person in persons)
        person_ids -= related_person_ids
        result['related_schedules'] = related_schedules

    if person_ids:
        persons = Person.query.filter(Person.id.in_(person_ids))
        schedules = context.make_persons_schedule(persons, start_date, end_date)
        result['schedules'] = schedules

    return jsonify(result)


@module.route('/api/schedule-description.json', methods=['GET'])
def api_schedule_description():
    person_id = parse_id(request.args, 'person_id')
    if person_id is False:
        return abort(400)
    start_date_s = request.args.get('start_date')
    try:
        start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
        end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
    except ValueError:
        return abort(400)

    context = ScheduleVisualizer()
    person = Person.query.get(person_id)
    return jsonify(context.make_person_schedule_description(person, start_date, end_date))


@module.route('/api/schedule-description.json', methods=['POST'])
def api_schedule_description_post():
    # TODO: validations

    def make_default_ticket(schedule):
        ticket = ScheduleTicket()
        ticket.schedule = schedule
        return ticket

    def make_tickets(schedule, planned, extra, cito):
        # here cometh another math
        dt = (datetime.datetime.combine(schedule.date, schedule.endTime) -
              datetime.datetime.combine(schedule.date, schedule.begTime)) / planned
        it = schedule.begTimeAsDt
        attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == 'planned').first()
        for i in xrange(planned):
            ticket = make_default_ticket(schedule)
            begDateTime = datetime.datetime.combine(schedule.date, it.time())
            ticket.begTime = begDateTime.time()
            ticket.endTime = (begDateTime + dt).time()
            ticket.attendanceType = attendanceType
            it += dt
            db.session.add(ticket)

        if extra:
            attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == 'extra').first()
            for i in xrange(extra):
                ticket = make_default_ticket(schedule)
                ticket.attendanceType = attendanceType
                db.session.add(ticket)

        if cito:
            attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == 'CITO').first()
            for i in xrange(cito):
                ticket = make_default_ticket(schedule)
                ticket.attendanceType = attendanceType
                db.session.add(ticket)

    schedule_data = request.json
    schedule = schedule_data['schedule']
    person_id = schedule_data['person_id']
    dates = [day['date'] for day in schedule]

    ok = delete_schedules(dates, person_id)

    for day_desc in schedule:
        date = safe_date(day_desc['date'])
        roa = day_desc['roa']

        if roa:
            new_sched = Schedule()
            new_sched.person_id = person_id
            new_sched.date = date
            new_sched.reasonOfAbsence = rbReasonOfAbsence.query.\
                filter(rbReasonOfAbsence.code == roa['code']).first()
            new_sched.begTime = '00:00'
            new_sched.endTime = '00:00'
            new_sched.numTickets = 0
            db.session.add(new_sched)
        else:
            new_scheds_by_rt = defaultdict(list)
            for sub_sched in day_desc['scheds']:
                new_sched = Schedule()
                new_sched.person_id = person_id
                new_sched.date = date
                new_sched.begTimeAsDt = safe_time_as_dt(sub_sched['begTime'])
                new_sched.begTime = new_sched.begTimeAsDt.time()
                new_sched.endTimeAsDt = safe_time_as_dt(sub_sched['endTime'])
                new_sched.endTime = new_sched.endTimeAsDt.time()
                new_sched.receptionType_id = safe_traverse(sub_sched, 'reception_type', 'id')
                new_sched.office_id = safe_traverse(sub_sched, 'office', 'id')
                new_sched.numTickets = sub_sched.get('planned', 0)

                make_tickets(new_sched,
                             sub_sched.get('planned', 0),
                             sub_sched.get('extra', 0),
                             sub_sched.get('CITO', 0))

    db.session.commit()

    start_date_s = schedule_data.get('start_date')
    start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
    end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
    context = ScheduleVisualizer()
    person = Person.query.get(person_id)
    return jsonify(context.make_person_schedule_description(person, start_date, end_date))


@module.route('/api/all_persons_tree.json')
def api_all_persons_tree():
    sub_result = defaultdict(list)
    persons = Person.query.\
        filter(Person.deleted == 0).\
        filter(Person.speciality).\
        order_by(Person.lastName, Person.firstName).\
        all()
    for person in persons:
        sub_result[person.speciality_id].append({
            'id': person.id,
            'name': person.shortNameText,
            'nameFull': [person.lastName, person.firstName, person.patrName]
        })
    result = [
        {
            'speciality': {
                'id': spec_id,
                'name': rbSpeciality.query.get(spec_id).name,
            },
            'persons': person_list,
        } for spec_id, person_list in sub_result.iteritems()
    ]
    return jsonify(result)


@module.route('/api/search_persons.json')
def api_search_persons():
    try:
        query_string = request.args['q']
    except KeyError or ValueError:
        return abort(404)
    result = SearchPerson.search(query_string)

    def cat(item):
        return {
            'display': u'#%d - %s %s %s (%s)' % (
                item['id'], item['lastname'], item['firstname'], item['patrname'], item['speciality']),
            'name': u'%s %s %s' % (item['lastname'], item['firstname'], item['patrname']),
            'speciality': item['speciality'],
            'id': item['id'],
            'tokens': [item['lastname'], item['firstname'], item['patrname']] + item['speciality'].split(),
        }
    data = map(cat, result['result']['items'])
    return jsonify(data)


    # Следующие 2 функции следует привести к приличному виду - записывать id создавших, проверки, ответы


@module.route('/api/appointment.json', methods=['POST'])
@public_endpoint
def api_appointment():
    """
    Запись (отмена записи) пациента на приём.
    Параметры:
        client_id (int) - id пациента
        ticket_id (int) - ScheduleTicket.id
        [opt] appointment_type_code (str) - rbAppointmentType.code
        [opt] delete (bool) - удалять ли запись
        [opt] note (str) - жалобы
    """
    data = request.get_json()
    client_id = int(data['client_id'])
    ticket_id = int(data['ticket_id'])
    appointment_type_code = data.get('appointment_type_code', 'amb')
    delete = bool(data.get('delete', False))
    ticket = ScheduleTicket.query.get(ticket_id)
    if not ticket:
        return abort(404)
    client_ticket = ticket.client_ticket
    if client_ticket and client_ticket.client_id != client_id:
        return jsonify(None, 400, u'Талончик занят другим пациентом (%d)' % client_ticket.client_id)
    if delete:
        if not client_ticket:
            return abort(404)
        client_ticket.deleted = 1
        db.session.commit()
        return jsonify(None)
    if not client_ticket:
        client_ticket = ScheduleClientTicket()
        client_ticket.client_id = client_id
        client_ticket.ticket_id = ticket_id
        client_ticket.createDatetime = client_ticket.modifyDatetime = datetime.datetime.now()
        client_ticket.createPerson_id = client_ticket.modifyPerson_id = current_user.get_id()
        db.session.add(client_ticket)
        client_ticket.appointmentType = rbAppointmentType.query.filter(rbAppointmentType.code == appointment_type_code).first()
    if 'note' in data:
        client_ticket.note = data['note']
    db.session.commit()
    return jsonify(None)


@module.route('/api/schedule_lock.json', methods=['POST'])
def api_schedule_lock():
    j = request.json
    try:
        person_id = j['person_id']
        date = datetime.datetime.strptime(j['date'], '%Y-%m-%d')
        roa = j['roa']
    except ValueError or KeyError:
        return abort(418)
    scheds = Schedule.query.filter(
        Schedule.person_id == person_id,
        Schedule.date == date,
        Schedule.deleted == 0
    )
    reasonOfAbsence = rbReasonOfAbsence.query.filter(rbReasonOfAbsence.code == roa).first()
    if not scheds.count() or not reasonOfAbsence:
        return abort(404)
    scheds.update({
        Schedule.reasonOfAbsence_id: reasonOfAbsence.id
    }, synchronize_session=False)
    db.session.commit()
    return ''


@module.route('/api/move_client.json', methods=['POST'])
def api_move_client():
    j = request.get_json()
    try:
        ticket_id = int(j['ticket_id'])
        destination_tid = j['destination_ticket_id']
    except ValueError or KeyError:
        return jsonify(None, 418, 'Both ticket_id and destination_ticket_id must be specified')
    source = ScheduleTicket.query.get(ticket_id)
    oldCT = source.client_ticket

    dest = ScheduleTicket.query.get(destination_tid)
    if dest.client:
        return jsonify(None, 418, 'Destination ticket is busy')
    ct = ScheduleClientTicket()
    ct.appointmentType_id = oldCT.appointmentType_id
    ct.client_id = oldCT.client_id
    ct.createDatetime = datetime.datetime.now()
    ct.modifyDatetime = ct.createDatetime
    ct.isUrgent = oldCT.isUrgent
    ct.infisFrom = oldCT.infisFrom
    ct.ticket_id = destination_tid
    oldCT.deleted = 1

    db.session.add(ct)
    db.session.add(oldCT)

    db.session.commit()
    return jsonify(None)


@module.route('/api/actions', methods=['GET'])
def api_action_get():
    from application.models.actions import Action
    action_id = int(request.args.get('action_id'))
    action = Action.query.get(action_id)
    v = ActionVisualizer()
    return jsonify(v.make_action(action))


@module.route('/api/actions/new.json', methods=['GET'])
def api_action_new_get():

    # Preparación de datos de entrada

    now = datetime.datetime.now()
    src_action = Action.query.get(int(request.args['src_action_id'])) \
        if 'src_action_id' in request.args else None
    """@type: Action | None"""
    src_props = dict((prop.type_id, prop) for prop in src_action.properties) if src_action else {}
    given_datetime = datetime.datetime.strptime(request.args['datetime'], '%Y-%m-%dT%H:%M') \
        if 'datetime' in request.args else None
    actionType = ActionType.query.get(int(request.args['action_type_id']))
    """@type: ActionType"""
    event = Event.query.get(int(request.args['event_id']))
    """@type: Event"""

    # Action creation starts

    action = Action()
    action.createDatetime = action.modifyDatetime = action.begDate = now
    action.createPerson = action.modifyPerson = action.setPerson = Person.query.get(current_user.get_id())
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.uet = 0  # TODO: calculate UET

    if given_datetime:
        action.plannedEndDate = given_datetime or now
    else:
        action.plannedEndDate = now
        # TODO: calculate plannedEndDate

    if actionType.defaultEndDate == 1:
        action.endDate = now
    elif actionType.defaultEndDate == 2:
        action.endDate = event.setDate
    elif actionType.defaultEndDate == 3:
        action.endDate = event.execDate
    if actionType.defaultDirectionDate == 1:
        action.directionDate = event.setDate
    elif actionType.defaultDirectionDate == 2:
        action.directionDate = now
    elif actionType.defaultDirectionDate == 3 and action.endDate:
        action.directionDate = max(action.endDate, event.setDate)
    else:
        action.directionDate = event.setDate

    if src_action:
        action.person = src_action.person
    elif actionType.defaultExecPerson_id:
        action.person = Person.query.get(actionType.defaultExecPerson_id)
    elif actionType.defaultPersonInEvent == 0:
        action.person = None
    elif actionType.defaultPersonInEvent == 2:
        action.person = action.setPerson
    elif actionType.defaultPersonInEvent == 3:
        action.person = event.execPerson
    elif actionType.defaultPersonInEvent == 4:
        action.person = Person.query.get(current_user.get_id())

    action.event = event
    action.event_id = event.id
    action.actionType = actionType
    action.status = actionType.defaultStatus
    prop_types = actionType.property_types.filter(ActionPropertyType.deleted == 0)
    v = ActionVisualizer()

    result = v.make_action(action)

    # アクションプロパティを作成する

    now_date = now.date()
    for prop_type in prop_types:
        if recordAcceptableEx(event.client.sex, event.client.age_tuple(now_date), prop_type.sex, prop_type.age):
            prop = ActionProperty()
            prop.type = prop_type
            prop.action = action
            value = src_props[prop_type.id].value if src_props.get(prop_type.id) else None
            result['properties'].append(v.make_abstract_property(prop, value))
    db.session.rollback()

    return jsonify(result)


@module.route('/api/actions', methods=['POST'])
def api_action_post():
    now = datetime.datetime.now()
    action_desc = request.json
    if action_desc['id']:
        action = Action.query.get(action_desc['id'])
        for prop_desc in action_desc['properties']:
            prop_type = ActionPropertyType.query.get(prop_desc['type']['id'])
            prop = ActionProperty.query.get(prop_desc['id'])
            prop.action = action
            prop.isAssigned = prop_desc['is_assigned']
            prop.type = prop_type
            if prop_desc['type']['vector']:
                # Идите в жопу со своими векторными значениями
                continue
            if prop_desc['value'] is not None:
                prop_value = prop.raw_values_query.first()
                if isinstance(prop_desc['value'], dict):
                    if prop_value:
                        if prop_desc['value']['id'] != prop_value.value:
                            prop_value.value = prop_desc['value']['id']
                            db.session.add(prop_value)
                    else:
                        prop_value = prop.valueTypeClass()
                        prop_value.property_object = prop
                        prop_value.value = prop_desc['value']['id']
                        db.session.add(prop_value)
                else:
                    if prop_value:
                        if prop_value.value != prop_desc['value']:
                            prop_value.value = prop_desc['value']
                            db.session.add(prop_value)
                    else:
                        prop_value = prop.valueTypeClass()
                        prop_value.property_object = prop
                        prop_value.value = prop_desc['value']
                        db.session.add(prop_value)
            else:
                prop.raw_values_query.delete()
            db.session.add(prop)
    else:
        # new action
        action = Action()
        action.createDatetime = now
        action.actionType = ActionType.query.get(action_desc['action_type']['id'])
        action.event = Event.query.get(action_desc['event_id'])
        for prop_desc in action_desc['properties']:
            prop_type = ActionPropertyType.query.get(prop_desc['type']['id'])
            prop = ActionProperty()
            prop.createDatetime = prop.modifyDatetime = now
            prop.norm = ''
            prop.evaluation = ''
            prop.action = action
            prop.isAssigned = prop_desc['is_assigned']
            prop.type = prop_type
            if prop_desc['type']['vector']:
                # Идите в жопу со своими векторными значениями
                continue
            if prop_desc['value'] is not None:
                prop_value = prop.valueTypeClass()
                prop_value.property_object = prop
                if isinstance(prop_desc['value'], dict):
                    prop_value.value = prop_desc['value']['id']
                else:
                    prop_value.value = prop_desc['value']
                db.session.add(prop_value)
            db.session.add(prop)

    action.modifyDatetime = now
    action.begDate = action_desc['begDate']
    action.endDate = action_desc['endDate']
    action.plannedEndDate = action_desc['planned_endDate'] or now
    action.status = action_desc['status']['id']
    action.setPerson_id = safe_traverse(action_desc, 'set_person', 'id')
    action.person_id = safe_traverse(action_desc, 'person', 'id')
    action.note = action_desc['note'] or ''
    action.directionDate = action_desc['direction_date']
    action.office = action_desc['office']
    action.amount = action_desc['amount']
    action.uet = action_desc['uet']
    action.payStatus = action_desc['pay_status'] or 0
    action.account = action_desc['account'] or 0
    action.coordText = ''
    action.AppointmentType = 0
    if not action.uuid:
        action.uuid = get_new_uuid()

    db.session.add(action)
    db.session.commit()

    context = action.actionType.context
    print_templates = rbPrintTemplate.query.filter(rbPrintTemplate.context == context).all()
    v = ActionVisualizer()
    print_context = PrintTemplateVisualizer()
    return jsonify({
        'action': v.make_action(action),
        'print_templates': map(print_context.make_template_info, print_templates)
    })


@cache.memoize(86400)
def int_get_atl(at_class):
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
def api_atl_get():
    at_class = int(request.args['at_class'])
    if not (0 <= at_class < 4):
        return abort(401)

    result = int_get_atl(at_class)

    return jsonify(result)
