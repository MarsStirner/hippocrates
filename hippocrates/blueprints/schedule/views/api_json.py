# -*- coding: utf-8 -*-

import calendar
import datetime
import logging
from collections import defaultdict

from hippocrates.blueprints.risar.lib import sirius
from flask import abort, request
from flask_login import current_user

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.jsonify import ScheduleVisualizer, PersonTreeVisualizer
from nemesis.lib.sphinx_search import SearchPerson
from nemesis.lib.utils import (jsonify, safe_traverse, parse_id, safe_date, safe_time_as_dt,
    safe_traverse_attrs, format_date, initialize_name, safe_int)
from nemesis.lib.utils import public_endpoint
from nemesis.models.exists import (rbSpeciality, rbReasonOfAbsence, Person, vrbPersonWithSpeciality, )

from nemesis.models.schedule import (Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType,
    rbAttendanceType, QuotingByTime)
from nemesis.systemwide import db, cache
from ..app import module
from ..lib.data import delete_schedules, create_schedules, create_time_quotas
from ..lib.utils import person_contacts_for_errand

__author__ = 'mmalkov'

logger = logging.getLogger('simple')


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
    proc_office_id = parse_id(request.args, 'proc_office_id')
    if person_id is False:
        return abort(400)
    try:
        start_date = datetime.datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = start_date + datetime.timedelta(days=1)
    except ValueError:
        return abort(400)

    viz = ScheduleVisualizer()
    person = Person.query.get(person_id)
    if proc_office_id:
        result = viz.make_procedure_office_schedule_description(proc_office_id, start_date, end_date, person)
    else:
        result = viz.make_person_schedule_description(person, start_date, end_date)
    return jsonify(result)


@module.route('/api/schedule-description.json', methods=['POST'])
@api_method
def api_schedule_description_post():
    schedule_data = request.get_json()
    schedule = schedule_data['schedule']
    quotas = schedule_data['quotas']
    person_id = schedule_data['person_id']
    dates = [day['date'] for day in schedule]
    person = Person.query.get(person_id)

    if schedule:
        ok, msg = delete_schedules(dates, person_id)
        if not ok:
            raise ApiException(422, msg)

    scheds = create_schedules(person, schedule)
    db.session.add_all(scheds)

    quotas = create_time_quotas(person, quotas)
    db.session.add_all(quotas)

    db.session.commit()

    start_date_s = schedule_data.get('start_date')
    start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
    end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
    context = ScheduleVisualizer()
    person = Person.query.get(person_id)
    return context.make_person_schedule_description(person, start_date, end_date)


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
    personKind = {
        0: 'only_doctors',
        1: 'only_org_persons'
    }
    try:
        query_string = request.args['q']
        pkind = safe_int(request.args.get('person_kind'))
        pkind = personKind.get(pkind)
        org_id = safe_int(request.args.get('org_id'))
    except (KeyError, ValueError):
        return abort(404)
    try:
        result = SearchPerson.search(query_string, org_id=org_id)

        def cat(item):
            return {
                'id': item['id'],
                'name': u'%s %s %s' % (item['lastname'], item['firstname'], item['patrname']),
                'full_name': u'%s %s %s (%s)' % (
                    item['lastname'], item['firstname'], item['patrname'], item['speciality']),
                'short_name': u'%s%s%s' % (
                    initialize_name(item['lastname'], item['firstname'], item['patrname']),
                    u', ' if item['speciality'] else u'',
                    item['speciality']),
                'speciality': {
                    'id': item['speciality_id'],
                    'code': item['speciality_code'],
                    'name': item['speciality']
                } if item['speciality_id'] else None,
                'org_structure': {
                    'id': item['orgstructure_id'],
                    'code': item['orgstructure_code'],
                    'name': item['orgstructure']
                } if item['orgstructure_id'] else None,

                'tokens': [item['lastname'], item['firstname'], item['patrname']] + item['speciality'].split(),
            }
        if pkind == 'only_doctors':
            result = filter(lambda item: item['orgstructure_id'] and item['speciality_id'], result['result']['items'])
        elif pkind == 'only_org_persons':
            result = filter(lambda item: item['org_id'], result['result']['items'])
        data = map(cat, result)
    except Exception, e:
        logger.critical(u'Ошибка в сервисе поиска сотрудника через sphinx: %s' % e, exc_info=True)
        query_string = query_string.split()
        data = vrbPersonWithSpeciality.query.filter(
            *[vrbPersonWithSpeciality.name.like(u'%%%s%%' % q) for q in query_string]
        ).filter(
            vrbPersonWithSpeciality.deleted == 0
        ).order_by(
            vrbPersonWithSpeciality.name
        )
        if pkind == 'only_doctors':
            data.filter(
                vrbPersonWithSpeciality.speciality_id != None,
                vrbPersonWithSpeciality.orgStructure_id != None
            )
        elif pkind == 'only_org_persons':
            data.filter(
                vrbPersonWithSpeciality.org_id != None
            )
        data = data.all()
    return jsonify(data)


@module.route('/api/person/')
@module.route('/api/person/<int:person_id>')
@api_method
def api_person_get(person_id=None):
    person = Person.query.get_or_404(person_id)
    return PersonTreeVisualizer().make_full_person(person)

@module.route('/api/person_contacts/')
@module.route('/api/person_contacts/<int:person_id>')
@api_method
def api_person_contacts_get(person_id=None):
    return person_contacts_for_errand(person_id, delimiter=', ')



# Следующие 2 функции следует привести к приличному виду - записывать id создавших, проверки, ответы
@module.route('/api/appointment.json', methods=['POST'])
@public_endpoint
def api_appointment():
    """
    Запись (отмена записи) пациента на приём.
    Параметры:
        client_id (int) - id пациента
        ticket_id (int) - ScheduleTicket.id
        [opt] appointment_type_id (int) - rbAppointmentType.id
        [opt] event_id (int) - id обращения в рамках которого проводится запись на приём
        [opt] delete (bool) - удалять ли запись
        [opt] note (str) - жалобы
    """
    data = request.get_json()
    client_id = data['client_id']
    ticket_id = data.get('ticket_id')
    schedule_id = data.get('schedule_id')
    create_person = data.get('create_person', current_user.get_id())
    appointment_type_id = data.get('appointment_type_id')
    event_id = data.get('event_id')
    delete = bool(data.get('delete', False))

    if ticket_id:
        ticket = ScheduleTicket.query.get(ticket_id)
    else:
        att_extra_id = rbAttendanceType.query.filter(
            rbAttendanceType.code == 'extra'
        ).value(rbAttendanceType.id)
        new_ticket = ScheduleTicket(
            schedule_id=schedule_id,
            attendanceType_id=att_extra_id,
        )
        db.session.add(new_ticket)
        db.session.flush([new_ticket])
        ticket_id = new_ticket.id
        ticket = new_ticket
    if not ticket:
        return abort(404)

    # todo: запрос вынести на клиент, чтобы лишнее соединение не держать
    schedule = ticket.schedule
    res = sirius.check_mis_schedule_ticket(
        client_id,
        ticket_id,
        delete,
        schedule.person.organisation,
        schedule.person,
        schedule.date,
        ticket.begTime,
        ticket.endTime,
        schedule.id,
    )
    if not res:
        return jsonify(None, 400, u'Не удалось занять талончик в РМИС')

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
        if event_id:
            client_ticket.event_id = event_id
        if appointment_type_id:
            client_ticket.appointmentType_id = appointment_type_id
        else:
            client_ticket.appointmentType = rbAppointmentType.query.filter(rbAppointmentType.code == u'amb').first()
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
    if roa is None:
        scheds.update({
            Schedule.reasonOfAbsence_id: None
        }, synchronize_session=False)
    else:
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


@cache.memoize(86400)
def int_get_orgstructure(org_id):
    from nemesis.models.exists import OrgStructure
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


@module.route('/api/schedule/procedure_offices.json', methods=['GET'])
def api_procedure_offices_get():
    proc_offices = Person.query.filter(Person.id.in_(
        # I have a dream one day
        # all the procedures will get their own entity.
        [710, 879, 751, 555, 557, 553, 554, 752, 552, 556, 935,
         915, 916, 917, 913, 911, 912, 914, 962, 961, 608, 920,
         924, 709, 963, 936, 934, 934, 943, 944, 1200]
    ))
    return jsonify([po for po in proc_offices])