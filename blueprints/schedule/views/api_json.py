# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime

from flask import abort, request
from application.database import db

from application.lib.sphinx_search import SearchPatient, SearchPerson
from application.lib.utils import public_endpoint, jsonify
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Person, Client, rbSpeciality
from blueprints.schedule.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType
from blueprints.schedule.views.jsonify import ScheduleVisualizer, ClientVisualizer, Format


__author__ = 'mmalkov'


@module.route('/api/schedule.json')
@public_endpoint
def api_schedule():
    try:
        person_id = int(request.args['person_id'])
        client_id = int(request.args['client_id']) if 'client_id' in request.args else None
        person = Person.query.get(person_id)
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
        attendance_type = request.args.get('attendance_type')
    except KeyError or ValueError:
        return abort(404)
    schedules = Schedule.query.\
        filter(Schedule.person_id == person_id).\
        filter(month_f <= Schedule.date).\
        filter(Schedule.date <= month_l).\
        order_by(Schedule.date)
    context = ScheduleVisualizer()
    context.client_id = client_id
    context.attendance_type = attendance_type
    return jsonify({
        'schedule': context.make_schedule(schedules, month_f, month_l),
        'person': context.make_person(person),
    })


@module.route('/api/schedules.json')
@public_endpoint
def api_schedules():
    pid = request.args.get('person_id', '')
    if pid and not (pid.startswith('[') and pid.endswith(']')) or pid and len(pid) < 3:
        return abort(404)
    try:
        person_ids = map(int, pid[1:-1].split(','))
        client_id = int(request.args['client_id']) if 'client_id' in request.args else None
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
        attendance_type = request.args.get('attendance_type')
    except KeyError or ValueError:
        return abort(404)
    context = ScheduleVisualizer()
    context.client_id = client_id
    context.attendance_type = attendance_type
    result = []
    for person_id in person_ids:
        person = Person.query.get(person_id)
        schedules = Schedule.query.\
            filter(Schedule.person_id == person_id).\
            filter(month_f <= Schedule.date).\
            filter(Schedule.date <= month_l).\
            order_by(Schedule.date)
        result.append({
            'schedule': context.make_schedule(schedules, month_f, month_l),
            'person': context.make_person(person),
        })
    return jsonify(result)

@module.route('/api/patient.json')
@public_endpoint
def api_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    context = ClientVisualizer()
    return jsonify({
        'clientData': context.make_client_info(client),
        'records': context.make_records(client),
    })


@module.route('/api/search_clients.json')
@public_endpoint
def api_search_clients():
    try:
        query_string = request.args['q']
    except KeyError or ValueError:
        return abort(404)

    if query_string:
        result = SearchPatient.search(query_string)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            clients = Client.query.filter(Client.id.in_(id_list)).all()
        else:
            clients = []
    else:
        clients = Client.query.limit(100).all()
    context = ClientVisualizer(Format.JSON)
    return jsonify(map(context.make_client_info, clients))


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


@module.route('/api/client_appointments.json')
@public_endpoint
def api_client_appointments():
    try:
        client_id = int(request.args['client_id'])
        month_f = datetime.datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        month_l = month_f + datetime.timedelta(weeks=1)
    except KeyError or ValueError:
        return abort(404)
    persons = Person.query.\
        join(ScheduleClientTicket.ticket).\
        join(ScheduleTicket.schedule).\
        join(Schedule.person).\
        filter(month_f <= Schedule.date, Schedule.date <= month_l).\
        filter(ScheduleClientTicket.client_id == client_id).\
        filter(ScheduleClientTicket.deleted == 0).\
        distinct()

    context = ScheduleVisualizer()
    context.client_id = client_id
    context.attendance_type = 'amb'
    return jsonify([
        {
            'person': context.make_person(person),
            'schedule': context.make_schedule(
                Schedule.query.filter(Schedule.person_id == int(person.id)).order_by(Schedule.date).all(),
                month_f, month_l
            )
        }
        for person in persons
    ])

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