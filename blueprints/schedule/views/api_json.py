# -*- coding: utf-8 -*-
import calendar
from collections import defaultdict
import datetime
from application.lib.data import create_new_action, create_action
from dateutil.parser import parse as dateutil_parse

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
    rbReceptionType, rbAttendanceType, QuotingByTime
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
    now = datetime.datetime.now()
    action_desc = request.get_json()
    if action_desc['id']:
        action = Action.query.get(action_desc['id'])
        for prop_desc in action_desc['properties']:
            prop = ActionProperty.query.get(prop_desc['id'])
            if isinstance(prop_desc['value'], dict):
                prop.set_value(safe_traverse(prop_desc, 'value', 'id'), True)
            else:
                prop.set_value(prop_desc['value'])
            prop.isAssigned = prop_desc['is_assigned']
            db.session.add(prop)
    else:
        # new action
        action = Action()
        action.actionType = ActionType.query.get(action_desc['action_type']['id'])
        action.event = Event.query.get(action_desc['event_id'])
        # orgStructure = action.event.current_org_structure if action.actionType.isRequiredTissue else None
        for prop_desc in action_desc['properties']:
            prop_type = ActionPropertyType.query.get(prop_desc['type']['id'])
            prop = ActionProperty()
            prop.action = action
            prop.isAssigned = prop_desc['is_assigned']
            prop.type = prop_type
            pd_value = prop_desc['value']
            if isinstance(pd_value, dict):
                prop.set_value(safe_traverse(pd_value, 'id'), True)
            elif pd_value is not None:
                prop.set_value(pd_value)
            # elif prop_type.typeName == 'JobTicket' and orgStructure:
            #     prop.value = aux_create_JT(action_desc['planned_endDate'] or now, ActionType.jobType_id, orgStructure.id)
            db.session.add(prop)

    #TODO:begDate, endDate, plannedEndDate, directionDate другой формат дат
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
    if not action.uuid:
        action.uuid = get_new_uuid()

    db.session.add(action)
    db.session.commit()

    v = ActionVisualizer()
    return jsonify(v.make_action(action))


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


prescriptionFlatCodes = (
    u'prescription',
    u'infusion',
    u'analgesia',
    u'chemotherapy',
)


@cache.memoize(86400)
def int_get_atl_flat(at_class):
    from application.lib.agesex import parseAgeSelector

    id_list = {}

    def schwing(t):
        t = list(t)
        t[5] = list(parseAgeSelector(t[7]))
        t[7] = t[7].split() if t[7] else None
        t[8] = bool(t[8])
        t.append([])
        id_list[t[0]] = t
        return t

    raw = db.text(
        ur'''SELECT
            ActionType.id, ActionType.name, ActionType.code, ActionType.flatCode, ActionType.group_id,
            ActionType.age, ActionType.sex,
            GROUP_CONCAT(OrgStructure_ActionType.master_id SEPARATOR ' '),
            ActionType.isRequiredTissue
            FROM ActionType
            LEFT JOIN OrgStructure_ActionType ON OrgStructure_ActionType.actionType_id = ActionType.id
            WHERE ActionType.class = {at_class} AND ActionType.deleted = 0 AND ActionType.hidden = 0
            GROUP BY ActionType.id'''.format(at_class=at_class))
        # This was goddamn unsafe, but I can't get it working other way
    result = map(schwing, db.session.execute(raw))
    raw = db.text(
        ur'''SELECT actionType_id, id, name, age, sex FROM ActionPropertyType
        WHERE isAssignable != 0 AND actionType_id IN ('{0}')'''.format("','".join(map(str, id_list.keys())))
    )
    map(lambda (at_id, apt_id, name, age, sex):
        id_list[at_id][9].append(
            (apt_id, name, list(parseAgeSelector(age)), sex)
        ), db.session.execute(raw)
    )
    return result


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