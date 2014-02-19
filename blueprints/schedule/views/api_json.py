# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import json
from flask import render_template, abort, request
from jinja2 import TemplateNotFound
from application.lib.sphinx_search import SearchPatient, SearchPerson
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Person, Client
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer, MyJsonEncoder, ClientVisualizer, Format

__author__ = 'mmalkov'


@module.route('/patient_info/')
@public_endpoint
def patient_info():
    try:
        return render_template('schedule/patient_info.html')
    except TemplateNotFound:
        abort(404)


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
    return json.dumps({
        'schedule': context.make_schedule(schedules, month_f, month_l),
        'person': context.make_person(person),
    }, cls=MyJsonEncoder)


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
    return json.dumps({
        'clientData': context.make_client_info(client),
        'records': context.make_records(client),
    }, cls=MyJsonEncoder)


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
    return json.dumps(
        map(context.make_client_info, clients),
        cls=MyJsonEncoder
    )


@module.route('/api/all_persons_tree.json')
@public_endpoint
def api_all_persons_tree():
    result = defaultdict(list)
    persons = Person.query.\
        filter(Person.deleted == 0).\
        filter(Person.speciality).\
        order_by(Person.lastName, Person.firstName).\
        all()
    for person in persons:
        result[person.speciality.name].append({'id': person.id, 'name': person.shortNameText})
    return json.dumps(
        result,
        cls=MyJsonEncoder,
    )


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
    return json.dumps(
        data,
        cls=MyJsonEncoder
    )