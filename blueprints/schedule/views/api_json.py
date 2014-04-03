# -*- coding: utf-8 -*-
import calendar
from collections import defaultdict
import json
import datetime

from flask import abort, request
from application.database import db
from application.lib.sphinx_search import SearchPerson
from application.lib.agesex import recordAcceptableEx
from application.lib.utils import public_endpoint, jsonify, safe_traverse
from blueprints.schedule.app import module
from application.models.exists import rbSpeciality, rbPolicyType, \
    rbReasonOfAbsence, rbSocStatusClass, rbSocStatusType, rbAccountingSystem, rbContactType, rbRelationType, \
    rbBloodType, BloodHistory, rbPrintTemplate, Event, Person
from application.models.actions import Action, ActionType, ActionProperty, ActionPropertyType
from application.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType, \
    rbReceptionType, rbAttendanceType
from blueprints.schedule.views.jsonify import ScheduleVisualizer, PrintTemplateVisualizer, \
    EventVisualizer, ActionVisualizer


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
@public_endpoint
def api_schedule_description():
    person_id_s = request.args.get('person_ids')
    start_date_s = request.args.get('start_date')
    try:
        start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
        end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
    except ValueError:
        return abort(400)

    result = {
        'schedules': [],
    }

    context = ScheduleVisualizer()

    try:
        person_ids = {int(person_id_s)}
    except ValueError:
        person_ids = set()

    if person_ids:
        persons = Person.query.filter(Person.id.in_(person_ids))
        schedules = context.make_persons_schedule_description(persons, start_date, end_date)
        result['schedules'] = schedules

    return jsonify(result)


@module.route('/api/schedule-description.json', methods=['POST'])
@public_endpoint
def api_schedule_description_post():
    def make_default_ticket(schedule):
        ticket = ScheduleTicket()
        ticket.schedule = schedule
        ticket.createDatetime = datetime.datetime.now()
        ticket.modifyDatetime = datetime.datetime.now()
        return ticket

    def make_tickets(schedule, planned, extra, cito):
        # here cometh another math
        dt = (schedule.endTime - schedule.begTime) / planned
        it = schedule.begTime
        attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == 'planned').first()
        for i in xrange(planned):
            ticket = make_default_ticket(schedule)
            ticket.begDateTime = datetime.datetime.combine(schedule.date, it.time())
            ticket.endDateTime = ticket.begDateTime + dt
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

    json = request.json
    schedule = request.json['schedule']
    person_id = json['person_id']
    reception_type = json['receptionType']
    dates = [
        day['date'] for day in schedule
    ]
    schedules = Schedule.query.join(rbReceptionType).filter(
        Schedule.deleted == 0, Schedule.person_id == person_id,
        Schedule.date.in_(dates), rbReceptionType.code == reception_type
    )
    schedules_with_clients = schedules.join(ScheduleTicket, ScheduleClientTicket).filter(
        ScheduleClientTicket.client_id is not None
    ).all()
    if schedules_with_clients:
        return jsonify({}, 401, u'Пациенты успели записаться на приём')
    schedules.update({
        Schedule.deleted: 1
    }, synchronize_session=False)
    for day_desc in schedule:
        new_sched = Schedule()
        new_sched.person_id = person_id
        new_sched.date = datetime.datetime.strptime(day_desc['date'], '%Y-%m-%d')
        new_sched.createDatetime = datetime.datetime.now()
        new_sched.modifyDatetime = datetime.datetime.now()
        new_sched.receptionType = rbReceptionType.query.filter(rbReceptionType.code == reception_type).first()
        new_sched.office = day_desc['office']
        if day_desc['roa']:
            new_sched.reasonOfAbsence = rbReasonOfAbsence.query.\
                filter(rbReasonOfAbsence.code == day_desc['roa']['code']).first()
            new_sched.begTime = '00:00'
            new_sched.endTime = '00:00'
            new_sched.numTickets = 0
            db.session.add(new_sched)
        else:
            new_sched.begTime = datetime.datetime.strptime(day_desc['scheds'][0]['begTime'], '%H:%M:%S')
            new_sched.endTime = datetime.datetime.strptime(day_desc['scheds'][0]['endTime'], '%H:%M:%S')
            new_sched.numTickets = int(day_desc['planned'])

            if len(day_desc['scheds']) == 1:
                db.session.add(new_sched)
                make_tickets(new_sched, int(day_desc['planned']), int(day_desc['extra']), int(day_desc['CITO']))
            if len(day_desc['scheds']) == 2:
                add_sched = Schedule()
                add_sched.person_id = person_id
                add_sched.date = datetime.datetime.strptime(day_desc['date'], '%Y-%m-%d')
                add_sched.createDatetime = datetime.datetime.now()
                add_sched.modifyDatetime = datetime.datetime.now()
                add_sched.receptionType = rbReceptionType.query.filter(rbReceptionType.code == reception_type).first()
                add_sched.begTime = datetime.datetime.strptime(day_desc['scheds'][1]['begTime'], '%H:%M:%S')
                add_sched.endTime = datetime.datetime.strptime(day_desc['scheds'][1]['endTime'], '%H:%M:%S')
                add_sched.office = day_desc['office']

                # Here cometh thy math

                qt = int(day_desc['planned'])
                M = new_sched.endTime - new_sched.begTime
                N = add_sched.endTime - add_sched.begTime
                qt1 = int(round(float(M.seconds * qt) / (M + N).seconds))
                qt2 = int(round(float(N.seconds * qt) / (M + N).seconds))

                new_sched.numTickets = qt1
                add_sched.numTickets = qt2

                make_tickets(new_sched, qt1, int(day_desc['extra']), int(day_desc['CITO']))
                make_tickets(add_sched, qt2, 0, 0)
                db.session.add(new_sched)
                db.session.add(add_sched)

    db.session.commit()
    return jsonify({})


@module.route('/api/all_persons_tree.json')
@public_endpoint
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
@public_endpoint
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

@module.route('/api/appointment_cancel.json')
@public_endpoint
def api_appointment_cancel():
    try:
        client_id = int(request.args['client_id'])
        ticket_id = int(request.args['ticket_id'])
    except KeyError or ValueError:
        return abort(404)
    ticket = ScheduleTicket.query.get(ticket_id)
    client_ticket = ticket.client_ticket
    if client_ticket and client_ticket.client.id == client_id:
        client_ticket.deleted = 1
        db.session.commit()
        return ''
    else:
        return abort(400)


@module.route('/api/appointment_make.json')
@public_endpoint
def api_appointment_make():
    try:
        client_id = int(request.args['client_id'])
        ticket_id = int(request.args['ticket_id'])
    except KeyError or ValueError:
        return abort(404)
    ticket = ScheduleTicket.query.get(ticket_id)
    client_ticket = ticket.client_ticket
    if client_ticket:
        return abort(400)
    client_ticket = ScheduleClientTicket()
    client_ticket.client_id = client_id
    client_ticket.ticket_id = ticket_id
    client_ticket.createDatetime = datetime.datetime.now()
    client_ticket.modifyDatetime = datetime.datetime.now()
    db.session.add(client_ticket)
    client_ticket.appointmentType = rbAppointmentType.query.filter(rbAppointmentType.code == 'amb').first()
    db.session.commit()
    return ''


@module.route('/api/schedule_lock.json', methods=['POST'])
@public_endpoint
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
@public_endpoint
def api_move_client():
    j = request.json
    try:
        ticket_id = int(j['ticket_id'])
        destination_tid = j['destination_ticket_id']
    except ValueError or KeyError:
        return abort(418)
    source = ScheduleTicket.query.get(ticket_id)
    oldCT = source.client_ticket

    dest = ScheduleTicket.query.get(destination_tid)
    if dest.client:
        return abort(512)
    ct = ScheduleClientTicket()
    ct.appointmentType_id = oldCT.appointmentType_id
    ct.client_id = oldCT.client_id
    ct.createDatetime = datetime.datetime.now()
    ct.modifyDatetime = ct.createDatetime
    ct.isUrgent = oldCT.isUrgent
    ct.orgFrom_id = oldCT.orgFrom_id
    ct.ticket_id = destination_tid
    oldCT.deleted = 1

    db.session.add(ct)
    db.session.add(oldCT)

    db.session.commit()
    return ''


@module.route('/api/event_info.json')
@public_endpoint
def api_event_info():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    print_templates = rbPrintTemplate.query.filter(rbPrintTemplate.context == 'f025').all()
    vis = EventVisualizer()
    print_context = PrintTemplateVisualizer()
    return jsonify({
        'event': vis.make_event(event),
        'diagnoses': vis.make_diagnoses(event),
        'print_templates': map(print_context.make_template_info, print_templates),
    })


@module.route('/api/events/diagnosis.json', methods=['POST'])
@public_endpoint
def api_diagnosis_save():
    current_datetime = datetime.datetime.now()
    from application.models.exists import Diagnosis, Diagnostic
    data = request.json
    diagnosis_id = data.get('diagnosis_id')
    diagnostic_id = data.get('diagnostic_id')
    if diagnosis_id:
        diagnosis = Diagnosis.get(diagnosis_id)
    else:
        diagnosis = Diagnosis()
        diagnosis.createDatetime = current_datetime
    if diagnostic_id:
        diagnostic = Diagnostic.get(diagnostic_id)
    else:
        diagnostic = Diagnostic()
        diagnostic.createDatetime = current_datetime

    diagnosis.modifyDatetime = current_datetime
    diagnostic.modifyDatetime = current_datetime

    diagnosis.client_id = data['client_id']
    diagnosis.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnosis.character_id = safe_traverse(data, 'character', 'id')
    diagnosis.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnosis.traumaType_id = safe_traverse(data, 'trauma', 'id')
    db.session.add(diagnosis)

    diagnostic.event_id = data['event_id']
    diagnostic.diagnosis = diagnosis
    diagnostic.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnostic.character_id = safe_traverse(data, 'character', 'id')
    diagnostic.stage_id = safe_traverse(data, 'stage', 'id')
    diagnostic.phase_id = safe_traverse(data, 'phase', 'id')
    diagnostic.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnostic.traumaType_id = safe_traverse(data, 'trauma', 'id')
    diagnostic.healthGroup_id = safe_traverse(data, 'health_group', 'id')
    diagnostic.result_id = safe_traverse(data, 'result', 'id')
    diagnostic.notes = data.get('notes', '')
    diagnostic.rbAcheResult_id = safe_traverse(data, 'ache_result', 'id')
    db.session.add(diagnostic)

    db.session.commit()


@module.route('/api/events/diagnosis.json', methods=['DELETE'])
@public_endpoint
def api_diagnosis_delete():
    from application.models.exists import Diagnosis, Diagnostic
    data = request.json
    if data['diagnosis_id']:
        Diagnosis.query.filter(Diagnosis.id == data['diagnosis_id']).update({'deleted': 1})
    if data['diagnostic_id']:
        Diagnostic.query.filter(Diagnostic.id == data['diagnostic_id']).update({'deleted': 1})


@module.route('/api/actions', methods=['GET'])
@public_endpoint
def api_action_get():
    from application.models.actions import Action
    action_id = int(request.args.get('action_id'))
    action = Action.query.get(action_id)
    context = action.actionType.context
    print_templates = rbPrintTemplate.query.filter(rbPrintTemplate.context == context).all()
    v = ActionVisualizer()
    print_context = PrintTemplateVisualizer()
    return jsonify({
        'action': v.make_action(action),
        'print_templates': map(print_context.make_template_info, print_templates)
    })


@module.route('/api/actions/new.json', methods=['GET'])
@public_endpoint
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
    action.createPerson = action.modifyPerson = action.setPerson = None  # TODO: current User
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.uet = 0  # TODO: calculate UET

    if given_datetime:
        action.plannedEndDate = given_datetime
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
        action.person = Person.query.get(actionType.defaultExecPersonId)
    elif actionType.defaultPersonInEvent == 0:
        action.person = None
    elif actionType.defaultPersonInEvent == 2:
        action.person = action.setPerson
    elif actionType.defaultPersonInEvent == 3:
        action.person = event.execPerson
    elif actionType.defaultPersonInEvent == 4:
        action.person = None  # TODO: current User

    action.event = event
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
@public_endpoint
def api_action_post():
    from application.models.actions import Action, ActionProperty
    data = request.json
    action_desc = data['action']
    if action_desc['id']:
        action = Action.query.get(action_desc['id'])
    else:
        # new action
        action = Action()
        action.actionType_id = action_desc['action_type']['id']
        action.event_id = action_desc['event_id']
        for prop_desc in action_desc:
            prop = ActionProperty()
            prop.action = action
            prop.isAssigned = prop_desc['is_assigned']
            prop.type_id = prop_desc['type_id']
    action.begDate = action_desc['begDate']
    action.endDate = action_desc['endDate']
    action.plannedEndDate = action_desc['planned_endDate']
    action.status = action_desc['status'].id
    action.setPerson_id = safe_traverse(action_desc, 'set_person', 'id')
    action.person_id = safe_traverse(action_desc, 'person', 'id')
    action.note = action_desc['note']
    # TODO: set properties
