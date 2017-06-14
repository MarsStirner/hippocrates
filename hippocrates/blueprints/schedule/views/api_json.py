# -*- coding: utf-8 -*-

import calendar
import datetime
from collections import defaultdict
import logging

from flask import abort, request
from flask_login import current_user
from nemesis.lib.html_utils import UIException

from nemesis.systemwide import db, cache
from nemesis.lib.sphinx_search import SearchPerson
from nemesis.lib.utils import (safe_traverse, parse_id, safe_date, safe_time_as_dt, safe_traverse_attrs, format_date, initialize_name, safe_bool,
                               bail_out)
from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method, ApiException
from sqlalchemy.orm import joinedload
from ..app import module
from ..lib.data import delete_schedules
from nemesis.models.exists import (rbSpeciality, rbReasonOfAbsence, Person, vrbPersonWithSpeciality)
from nemesis.models.schedule import (Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType,
    rbAttendanceType, QuotingByTime)
from nemesis.lib.jsonify import ScheduleVisualizer, PersonTreeVisualizer


__author__ = 'mmalkov'

logger = logging.getLogger('simple')


@module.route('/api/schedule.json')
@api_method
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
        raise ApiException(400, u'Проблемы с параметрами')

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
            raise ApiException(400, u'client_id должен быть указан, если related')
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

    return result


@module.route('/api/schedule-description.json', methods=['GET'])
@api_method
def api_schedule_description():
    person_id = parse_id(request.args, 'person_id')
    person_id is False and bail_out(ApiException(400, u'Некорректное значение person_id'))
    start_date_s = request.args.get('start_date')
    try:
        start_date = datetime.datetime.strptime(start_date_s, '%Y-%m').date()
        end_date = start_date + datetime.timedelta(calendar.monthrange(start_date.year, start_date.month)[1])
    except ValueError:
        raise ApiException(400, u'Некорректная дата')

    context = ScheduleVisualizer()
    person = Person.query.get(person_id) or bail_out(ApiException(404, u'Врач не найден'))
    return context.make_person_schedule_description(person, start_date, end_date)


@module.route('/api/copy_schedule_description.json', methods=['GET'])
@api_method()
def api_copy_schedule_description():
    person_id = parse_id(request.args, 'person_id')
    person_id is False and bail_out(ApiException(400, u'Некорректное значение person_id'))
    from_start_date = safe_date(request.args.get('from_start_date'))
    from_end_date = safe_date(request.args.get('from_end_date'))
    to_start_date = safe_date(request.args.get('to_start_date'))
    to_end_date = safe_date(request.args.get('to_end_date'))
    if not (from_start_date and from_end_date and to_start_date and to_end_date):
        raise ApiException(400, u'Все параметры должны быть указаны: from_start_date, from_end_date, to_start_date, to_end_date')

    context = ScheduleVisualizer()
    person = Person.query.get(person_id) or bail_out(ApiException(404, u'Врач не найден'))
    return context.make_copy_schedule_description(person, from_start_date, from_end_date, to_start_date, to_end_date)


@module.route('/api/day_schedule.json', methods=['GET'])
@api_method
def api_day_schedule():
    person_id = parse_id(request.args, 'person_id')
    proc_office_id = parse_id(request.args, 'proc_office_id')
    person_id is False and bail_out(ApiException(400, u'Некорректное значение person_id'))
    try:
        start_date = datetime.datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = start_date + datetime.timedelta(days=1)
    except ValueError:
        raise ApiException(400, u'Некорректная дата')

    viz = ScheduleVisualizer()
    person = Person.query.get(person_id) or bail_out(ApiException(404, u'Врач не найден'))
    if proc_office_id:
        return viz.make_procedure_office_schedule_description(proc_office_id, start_date, end_date, person)
    else:
        return viz.make_person_schedule_description(person, start_date, end_date)


@module.route('/api/schedule-description.json', methods=['POST'])
@api_method()
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
        attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == u'planned').first()
        for i in xrange(planned):
            ticket = make_default_ticket(schedule)
            begDateTime = datetime.datetime.combine(schedule.date, it.time())
            ticket.begTime = begDateTime.time()
            ticket.endTime = (begDateTime + dt).time()
            ticket.attendanceType = attendanceType
            it += dt
            db.session.add(ticket)

        if extra:
            attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == u'extra').first()
            for i in xrange(extra):
                ticket = make_default_ticket(schedule)
                ticket.attendanceType = attendanceType
                db.session.add(ticket)

        if cito:
            attendanceType = rbAttendanceType.query.filter(rbAttendanceType.code == u'CITO').first()
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
            raise ApiException(422, msg)

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
                new_sched.finance_id = safe_traverse(sub_sched, 'finance', 'id')
                office_id = safe_traverse(sub_sched, 'office', 'id')
                if not office_id and safe_traverse(sub_sched, 'reception_type', 'code') == 'amb':
                    raise ApiException(422, u'На %s не указан кабинет' % format_date(date))
                new_sched.office_id = office_id
                new_sched.numTickets = sub_sched.get('planned', 0)

                planned_count = sub_sched.get('planned')
                if not planned_count:
                    raise ApiException(422, u'На %s указаны интервалы с нулевым планом' % format_date(date))
                make_tickets(new_sched, planned_count, sub_sched.get('extra', 0), sub_sched.get('CITO', 0))

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
    person = Person.query.get(person_id) or bail_out(ApiException(404, u'Врач не найден'))
    return context.make_person_schedule_description(person, start_date, end_date)


@module.route('/api/all_persons_tree.json')
@api_method
def api_all_persons_tree():
    sub_result = defaultdict(list)
    persons = Person.query.filter(
        Person.deleted == 0,
        Person.speciality,
    ).order_by(
        Person.lastName, Person.firstName
    ).options(
        joinedload(Person.org_structure),
        joinedload(Person.speciality),
    )
    for person in persons:
        sub_result[person.speciality_id].append({
            'id': person.id,
            'name': person.shortNameText,
            'nameFull': [person.lastName, person.firstName, person.patrName],
            'org_structure': safe_traverse_attrs(person, 'org_structure', 'name')
        })
    rbSpecialityDict = rbSpeciality.cache().dict('id')
    result = [
        {
            'speciality': {
                'id': spec_id,
                'name': rbSpecialityDict.get(spec_id).name,
            },
            'persons': person_list,
        } for spec_id, person_list in sub_result.iteritems()
    ]
    return result


@module.route('/api/person/persons_tree_schedule_info.json')
@api_method
def api_persons_tree_schedule_info():
    beg_date = safe_date(request.args.get('beg_date'))
    end_date = safe_date(request.args.get('end_date'))
    if not (beg_date and end_date):
        raise ApiException(400, u'параметры beg_date и end_date должны быть указаны')
    result = db.session.query(Schedule.person_id).filter(
        Schedule.deleted == 0,
        Schedule.reasonOfAbsence_id.is_(None),
        beg_date <= Schedule.date,
        Schedule.date <= end_date
    ).distinct()
    return {
        'persons_with_scheds': [row[0] for row in result]
    }


@module.route('/api/search_persons.json')
@api_method
def api_search_persons():
    query_string = request.args.get('q') or bail_out(ApiException(400, u'Параметр "q" должен быть указан'))
    only_doctors = safe_bool(request.args.get('only_doctors', True))
    try:
        result = SearchPerson.search(query_string)

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
        if only_doctors:
            result = filter(lambda item: item['orgstructure_id'] and item['speciality_id'], result['result']['items'])
        data = map(cat, result)
    except Exception, e:
        logger.critical(u'Ошибка в сервисе поиска сотрудника через sphinx: %s' % e, exc_info=True)
        query_string = query_string.split()
        data = vrbPersonWithSpeciality.query.filter(
            *[vrbPersonWithSpeciality.name.like(u'%%%s%%' % q) for q in query_string]
        ).order_by(
            vrbPersonWithSpeciality.name
        )
        if only_doctors:
            data.filter(
                vrbPersonWithSpeciality.speciality_id != None,
                vrbPersonWithSpeciality.orgStructure_id != None
            )
        data = data.all()
    return data


@module.route('/api/person/')
@module.route('/api/person/<int:person_id>')
@api_method
def api_person_get(person_id=None):
    person = Person.query.get(person_id) or bail_out(ApiException(404, u'Врач не найден'))
    return PersonTreeVisualizer().make_full_person(person)


# Следующие 2 функции следует привести к приличному виду - записывать id создавших, проверки, ответы
@module.route('/api/appointment.json', methods=['POST'])
@api_method
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
    ticket_id = data['ticket_id']
    create_person = data.get('create_person', current_user.get_id())
    appointment_type_id = data.get('appointment_type_id')
    event_id = data.get('event_id')
    delete = safe_bool(data.get('delete', False))
    ticket = ScheduleTicket.query.get(ticket_id)
    if not ticket:
        raise ApiException(404, u'Талончик не найден')
    client_ticket = ticket.client_ticket
    if client_ticket and client_ticket.client_id != client_id:
        raise ApiException(
            400, u'Запись занята другим пациентом. Выполните запись на другой свободный талон',
            client_id=client_ticket.client_id,
        )
    if delete:
        if not client_ticket:
            raise ApiException(404, u'Талончик не занят. Запись уже отменена или не была создана.')
        if client_ticket.client_id != client_id:
            raise ApiException(400, u'Талончик занят другим пациентом. Запись этого пациента уже была отменена или не была создана')
        client_ticket.deleted = 1
        db.session.commit()
        return
    # Проверим, не записан ли пациент к кому-то на это же время
    busy_tickets = ScheduleClientTicket.query.join(
        ScheduleTicket
    ).join(
        Schedule
    ).filter(
        Schedule.date == ticket.schedule.date,
        ScheduleClientTicket.client_id == client_id,
        ScheduleClientTicket.deleted == 0,
        ScheduleTicket.deleted == 0,
        db.or_(
            ScheduleTicket.begTime.between(ticket.begTime, ticket.endTime),
            ScheduleTicket.endTime.between(ticket.begTime, ticket.endTime),
        )
    ).order_by(ScheduleTicket.begTime).all()
    if busy_tickets:
        if len(busy_tickets) == 1:
            msg = u'Пациент уже записан на приём к врачу %s на %s-%s' % (
                busy_tickets[0].ticket.schedule.person.shortNameText,
                busy_tickets[0].ticket.begTime.strftime('%H:%M'),
                busy_tickets[0].ticket.endTime.strftime('%H:%M'),
            )
        else:
            msg = u'Пациент уже записан на приёмы: %s' % (
                u', '.join(u'к %s на %s-%s' % (
                    busy_ticket.ticket.schedule.person.shortNameText,
                    busy_ticket.ticket.begTime.strftime('%H:%M'),
                    busy_ticket.ticket.endTime.strftime('%H:%M'),
                ) for busy_ticket in busy_tickets)
            )
        raise ApiException(400, msg, records=[{
            'person_id': busy_ticket.ticket.schedule.person_id,
            'begDateTime': busy_ticket.ticket.begDateTime,
            'endDateTime': busy_ticket.ticket.endDateTime,
        } for busy_ticket in busy_tickets])
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


@module.route('/api/schedule_lock.json', methods=['POST'])
@api_method
def api_schedule_lock():
    j = request.json
    person_id = parse_id(j, 'person_id')
    person_id is False and bail_out(ApiException(400, u'person_id должен быть числом'))
    'roa' not in j and bail_out(ApiException(400, u'roa должен быть указан'))
    roa = j['roa']
    try:
        date = datetime.datetime.strptime(j['date'], '%Y-%m-%d')
    except (ValueError, KeyError):
        raise ApiException(400, u'Ошибка в дате')
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

        if not scheds.count():
            raise ApiException(404, u'Нечего блокировать')
        if not reasonOfAbsence:
            raise ApiException(404, u'Нет причины отсутствия с таким кодом')
        scheds.update({
            Schedule.reasonOfAbsence_id: reasonOfAbsence.id
        }, synchronize_session=False)
    db.session.commit()


@module.route('/api/move_client.json', methods=['POST'])
@api_method
def api_move_client():
    j = request.get_json()
    try:
        ticket_id = int(j['ticket_id'])
        destination_tid = j['destination_ticket_id']
    except (ValueError, KeyError):
        raise ApiException(418, 'Both ticket_id and destination_ticket_id must be specified')
    source = ScheduleTicket.query.get(ticket_id)
    oldCT = source.client_ticket

    dest = ScheduleTicket.query.get(destination_tid)
    if dest.client:
        raise ApiException(418, 'Destination ticket is busy')
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


@cache.memoize(86400)
def int_get_orgstructure(org_id, with_deleted=False, with_hidden=False):
    from nemesis.models.exists import OrgStructure
    query = OrgStructure.query.filter(OrgStructure.organisation_id == org_id)
    if not with_deleted:
        query = query.filter(OrgStructure.deleted == 0)
    if not with_hidden:
        query = query.filter(OrgStructure.show == 1)
    return [{
        'id': t.id,
        'name': t.shortName,
        'full_name': t.name,
        'code': t.code,
        'parent_id': t.parent_id,
    } for t in query]


@module.route('/api/org-structure.json')
@api_method
def api_org_structure():
    org_id = int(request.args['org_id'])
    with_deleted = safe_bool(request.args.get('with_deleted', False))
    with_hidden = safe_bool(request.args.get('with_hidden', False))
    return int_get_orgstructure(org_id, with_deleted, with_hidden)


@module.route('/api/schedule/procedure_offices.json', methods=['GET'])
@api_method
def api_procedure_offices_get():
    proc_offices = Person.query.filter(Person.id.in_(
        # I have a dream one day
        # all the procedures will get their own entity.
        [710, 879, 751, 555, 557, 553, 554, 752, 552, 556, 935,
         915, 916, 917, 913, 911, 912, 914, 962, 961, 608, 920,
         924, 709, 963, 936, 934, 934, 943, 944, 1200]
    )).all()
    return proc_offices