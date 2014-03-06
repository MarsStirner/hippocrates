# -*- coding: utf-8 -*-
import calendar
from collections import defaultdict
import datetime
import json

from flask import abort, request

from application.database import db
from application.lib.sphinx_search import SearchPatient, SearchPerson
from application.lib.utils import public_endpoint, jsonify
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Person, Client, rbSpeciality, rbDocumentType
from blueprints.schedule.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType
from blueprints.schedule.views.jsonify import ScheduleVisualizer, ClientVisualizer, RbVisualizer, Format


__author__ = 'mmalkov'


@module.route('/api/schedule.json')
@public_endpoint
def api_schedule():
    person_id_s = request.args.get('person_ids')
    client_id_s = request.args.get('client_id')
    start_date_s = request.args.get('start_date')
    reception_type = request.args.get('reception_type')
    related = bool(request.args.get('related', False))
    expand = bool(request.args.get('expand', False))
    try:
        try:
            # Пытаемся вытащить расписание на неделю
            start_date = datetime.datetime.strptime(start_date_s, '%Y-%m-%d').date()
            end_date = start_date + datetime.timedelta(weeks=1)
        except ValueError:
            # Пытаемся вытащить расписание на месяц
            start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
            end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
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
        related_schedules = context.make_persons_schedule(persons, start_date, end_date, expand)
        related_person_ids = set(person.id for person in persons)
        person_ids -= related_person_ids
        result['related_schedules'] = related_schedules

    if person_ids:
        persons = Person.query.filter(Person.id.in_(person_ids))
        schedules = context.make_persons_schedule(persons, start_date, end_date, expand)
        result['schedules'] = schedules

    return jsonify(result)


@module.route('/api/schedule-description.json')
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
    rbDocumentTypes = [document_type for document_type in rbDocumentType.query.all() if document_type.group.code == '1']
    rb_context = RbVisualizer()
    reference_books = [rb_context.make_rb_info(document_type) for document_type in rbDocumentTypes]
    return jsonify({
        'clientData': context.make_client_info(client),
        'records': context.make_records(client),
        'referenceBooks': reference_books
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


@module.route('/api/save_patient_info.json')
@public_endpoint
def api_save_patient_info():
    try:
        client_info = json.loads(request.args['client_info'])
        client_id = int(client_info['id'])
        client = Client.query.get(client_id)
        db.session.add(client)
        client.lastName = client_info['lastName']
        client.firstName = client_info['firstName']
        client.patrName = client_info['patrName']
        client.sexCode = 1 if client_info['sex'] == u'М' else 2
        client.birthDate = client_info['birthDate']
        client.document.serial = client_info['document']['serial']
        client.document.number = client_info['document']['number']
        client.document.date = client_info['document']['date']
        client.document.endDate = client_info['document']['endDate']
        client.document.documentType = rbDocumentType.query.filter(rbDocumentType.code == client_info['document']['typeCode']).first()
        client.SNILS = client_info['SNILS'].replace(" ", "").replace("-", "")
        db.session.commit()
    except KeyError or ValueError:
        return abort(404)

    return ''