# -*- encoding: utf-8 -*-
import datetime
import json

from flask import render_template, abort, request
from jinja2 import TemplateNotFound

from ..app import module
from application.lib.sphinx_search import SearchPerson
from application.lib.utils import public_endpoint
from blueprints.schedule.models.exists import Person, Client
from blueprints.schedule.models.schedule import Schedule
from blueprints.schedule.views.jsonify import ScheduleVisualizer, MyJsonEncoder, ClientVisualizer, Format


@module.route('/')
@public_endpoint
def index():
    try:
        return render_template('schedule/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/doctors/')
@public_endpoint
def doctors():
    try:
        return render_template('schedule/doctors.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patients/')
@public_endpoint
def patients():
    try:
        return render_template('schedule/patients.html')
    except TemplateNotFound:
        abort(404)


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
    context.push_all(schedules, month_f, month_l)
    return json.dumps({
        'schedule': context.schedule,
        'max_tickets': context.max_tickets,
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


@module.route('/api/patient.html')
@public_endpoint
def html_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    context = ClientVisualizer(Format.HTML)
    return render_template(
        'schedule/patient_info_nojs.html',
        client=client,
        client_info_codes_rus={
            'id': u'Код пациента',
            'birthDate': u'Дата рождения',
            'regAddress': u'Адрес регистрации',
            'liveAddress': u'Адрес проживания',
            'SNILS': u'СНИЛС',
            'nameText': u'ФИО',
            'sex': u'Пол',
            'document': u'Документ',
            'contact': u'Контакты',
            'voluntaryPolicy': u'Полис ДМС',
            'compulsoryPolicy': u'Полис ОМС'
        },
        client_info_codes_order=['id', 'nameText', 'birthDate', 'sex', 'regAddress', 'liveAddress', 'document', 'compulsoryPolicy', 'voluntaryPolicy', 'SNILS', 'contact'],
        record_codes_rus={
            'mark': u'Отметка',
            'begDateTime': u'Дата и время приёма',
            'office': u'Кабинет',
            'person': u'Специалист',
            'createPerson': u'Записал',
            'note': u'Примечания'
        },
        record_codes_order=['mark', 'begDateTime', 'office', 'person', 'createPerson', 'note'],
        clientData=context.make_client_info(client),
        records=context.make_records(client),
    )


@module.route('/api/search_clients.json')
@public_endpoint
def api_search_clients():
    try:
        query_string = request.args['q']
    except KeyError or ValueError:
        return abort(404)
    # Здесь должен быть полнотекстный поиск
    clients = Client.query.filter(Client.lastName.like('%%%s%%' % query_string)).limit(100).all()
    context = ClientVisualizer(Format.JSON)
    return json.dumps(
        map(context.make_client_info, clients),
        cls=MyJsonEncoder
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