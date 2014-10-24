# -*- coding: utf-8 -*-

import calendar
import datetime

from collections import defaultdict
from dateutil.parser import parse as dateutil_parse
from flask import abort, request
from flask.ext.login import current_user
from application.lib.user import UserUtils

from application.models.event import Event
from application.systemwide import db, cache
from application.lib.sphinx_search import SearchPerson
from application.lib.utils import (jsonify, safe_traverse, parse_id, safe_date, safe_time_as_dt, safe_datetime,
                                   safe_traverse_attrs, format_date)
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.lib.data import delete_schedules
from application.models.exists import (rbSpeciality, rbReasonOfAbsence, Person)
from application.models.actions import Action, ActionType
from application.models.schedule import (Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType,
    rbAttendanceType, QuotingByTime)
from application.lib.jsonify import ScheduleVisualizer, ActionVisualizer
from application.lib.data import (create_new_action, create_action, update_action, int_get_atl_flat,
    get_planned_end_datetime)


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


@module.route('/api/copy_schedule_description.json', methods=['GET'])
def api_copy_schedule_description():
    person_id = parse_id(request.args, 'person_id')
    if person_id is False:
        return abort(400)
    from_start_date = safe_date(request.args.get('from_start_date'))
    from_end_date = safe_date(request.args.get('from_end_date'))
    to_start_date = safe_date(request.args.get('to_start_date'))
    to_end_date = safe_date(request.args.get('to_end_date'))
    if not (from_start_date and from_end_date and to_start_date and to_end_date):
        return abort(400)

    context = ScheduleVisualizer()
    person = Person.query.get(person_id)
    return jsonify(context.make_copy_schedule_description(person, from_start_date, from_end_date, to_start_date, to_end_date))


@module.route('/api/day_schedule.json', methods=['GET'])
def api_day_schedule():
    person_id = parse_id(request.args, 'person_id')
    if person_id is False:
        return abort(400)
    try:
        start_date = datetime.datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = start_date + datetime.timedelta(days=1)
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
    quotas = schedule_data['quotas']
    person_id = schedule_data['person_id']
    dates = [day['date'] for day in schedule]

    if schedule:
        ok, msg = delete_schedules(dates, person_id)
        if not ok:
            return jsonify({}, 422, msg)

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
                office_id = safe_traverse(sub_sched, 'office', 'id')
                if not office_id and safe_traverse(sub_sched, 'reception_type', 'code') == 'amb':
                    return jsonify({}, 422, u'На %s не указан кабинет' % format_date(date))
                new_sched.office_id = office_id
                new_sched.numTickets = sub_sched.get('planned', 0)

                planned_count = sub_sched.get('planned')
                if not planned_count:
                    return jsonify({}, 422, u'На %s указаны интервалы с нулевым планом' % format_date(date))
                make_tickets(new_sched,
                             planned_count,
                             sub_sched.get('extra', 0),
                             sub_sched.get('CITO', 0))

    for quota_desc in quotas:
        date = safe_date(quota_desc['date'])
        QuotingByTime.query.filter(QuotingByTime.doctor_id == person_id,
                                   QuotingByTime.quoting_date == date).delete()
        new_quotas = quota_desc['day_quotas']
        for quota in new_quotas:
            quota_record = QuotingByTime()
            quota_record.quoting_date = date
            quota_record.doctor_id = person_id
            quota_record.QuotingTimeStart = safe_time_as_dt(quota['time_start'])
            quota_record.QuotingTimeEnd = safe_time_as_dt(quota['time_end'])
            quota_record.quotingType_id = quota['quoting_type']['id']
            db.session.add(quota_record)

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
        order_by(Person.lastName, Person.firstName)
    for person in persons:
        sub_result[person.speciality_id].append({
            'id': person.id,
            'name': person.shortNameText,
            'nameFull': [person.lastName, person.firstName, person.patrName],
            'org_structure': safe_traverse_attrs(person, 'org_structure', 'name')
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


@module.route('/api/person/persons_tree_schedule_info.json')
def api_persons_tree_schedule_info():
    beg_date = safe_date(request.args.get('beg_date'))
    end_date = safe_date(request.args.get('end_date'))
    if not (beg_date and end_date):
        return abort(404)
    result = db.session.query(Schedule.person_id).filter(
        Schedule.deleted == 0,
        Schedule.reasonOfAbsence_id.is_(None),
        beg_date <= Schedule.date,
        Schedule.date <= end_date
    ).distinct()
    return jsonify({
        'persons_with_scheds': [row[0] for row in result]
    })


@module.route('/api/search_persons.json')
def api_search_persons():
    try:
        query_string = request.args['q']
    except (KeyError, ValueError):
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
    create_person = data.get('create_person', current_user.get_id())
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
        client_ticket.createPerson_id = client_ticket.modifyPerson_id = create_person
        client_ticket.appointmentType = rbAppointmentType.query.filter(rbAppointmentType.code == appointment_type_code).first()
        db.session.add(client_ticket)
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
    except (ValueError, KeyError):
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
    except (ValueError, KeyError):
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
    src_action = Action.query.get(int(request.args['src_action_id'])) \
        if 'src_action_id' in request.args else None
    action_type_id = int(request.args['action_type_id'])
    event_id = int(request.args['event_id'])

    action = create_action(action_type_id, event_id, src_action=src_action)

    v = ActionVisualizer()
    result = v.make_action(action)
    db.session.rollback()
    return jsonify(result)


@module.route('/api/actions', methods=['POST'])
def api_action_post():
    action_desc = request.get_json()
    action_id = action_desc['id']
    data = {
        'begDate': safe_datetime(action_desc['beg_date']),
        'endDate': safe_datetime(action_desc['end_date']),
        'plannedEndDate': safe_datetime(action_desc['planned_end_date']),
        'directionDate': safe_datetime(action_desc['direction_date']),
        'isUrgent': action_desc['is_urgent'],
        'status': action_desc['status']['id'],
        'setPerson_id': safe_traverse(action_desc, 'set_person', 'id'),
        'person_id':  safe_traverse(action_desc, 'person', 'id'),
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
            return jsonify(None, 404, 'Action %s not found' % action_id)
        if not UserUtils.can_edit_action(action):
            return jsonify(None, 403, 'User cannot edit action %s' % action_id)
        action = update_action(action, **data)
    else:
        at_id = action_desc['action_type']['id']
        event_id = action_desc['event_id']
        action = create_new_action(at_id, event_id, properties=properties_desc, data=data)

    db.session.add(action)
    db.session.commit()

    v = ActionVisualizer()
    return jsonify(v.make_action(action))


@module.route('/api/action_type/planned_end_date.json', methods=['GET'])
def api_get_action_ped():
    at_id = parse_id(request.args, 'action_type_id')
    if at_id is False:
        return abort(404)
    at = ActionType.query.get(at_id)
    if not at:
        return abort(404)
    return jsonify({
        'ped': get_planned_end_datetime(at_id)
    })


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
def api_atl_get():
    # not used?
    at_class = int(request.args['at_class'])
    if not (0 <= at_class < 4):
        return abort(401)

    result = int_get_atl(at_class)

    return jsonify(result)


prescriptionFlatCodes = (
    u'prescription',
    u'infusion',
    u'analgesia',
    u'chemotherapy',
)


@module.route('/api/action-type-list-flat.json')
def api_atl_get_flat():
    at_class = int(request.args['at_class'])
    if not (0 <= at_class < 4):
        return abort(401)

    return jsonify(int_get_atl_flat(at_class))


@cache.memoize(86400)
def int_get_orgstructure(org_id):
    from application.models.exists import OrgStructure
    def schwing(t):
        return {
            'id': t.id,
            'name': t.name,
            'code': t.code,
            'parent_id': t.parent_id,
        }
    return map(schwing, OrgStructure.query.filter(OrgStructure.organisation_id == org_id))


@module.route('/api/org-structure.json')
def api_org_structure():
    org_id = int(request.args['org_id'])
    return jsonify(int_get_orgstructure(org_id))


@module.route('/api/create-lab-direction.json', methods=['POST'])
def api_create_lab_direction():
    ja = request.get_json()
    event_id = ja['event_id']
    event = Event.query.get(event_id)
    org_structure = event.current_org_structure
    if not org_structure:
        return jsonify({
            'message': u'Пациент не привязан ни к одному из отделений.'
        }, 422, 'ERROR')

    for j in ja['directions']:
        action_type_id = j['type_id']
        assigned = j['assigned']
        data = {
            'plannedEndDate': dateutil_parse(j['planned_end_date'])
        }
        action = create_new_action(
            action_type_id,
            event_id,
            assigned=assigned,
            data=data
        )
        db.session.add(action)

    db.session.commit()
    return jsonify(None)