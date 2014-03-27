# -*- coding: utf-8 -*-
import calendar
from collections import defaultdict
import json

from flask import abort, request

from application.database import db
from application.lib.sphinx_search import SearchPatient, SearchPerson
from application.lib.utils import public_endpoint, jsonify, safe_traverse
from blueprints.schedule.app import module
from application.models.exists import Person, Client, rbSpeciality, rbDocumentType, rbPolicyType, \
    rbReasonOfAbsence, rbSocStatusClass, rbSocStatusType, rbAccountingSystem, rbContactType, rbRelationType, \
    ClientDocument, rbBloodType, Bloodhistory, rbPrintTemplate, Event
from application.models.schedule import Schedule, ScheduleTicket, ScheduleClientTicket, rbAppointmentType, \
    rbReceptionType, rbAttendanceType
from blueprints.schedule.views.jsonify import ScheduleVisualizer, ClientVisualizer, PrintTemplateVisualizer, Format, \
    EventVisualizer, ActionVisualizer
from blueprints.schedule.views.utils import *
from blueprints.schedule.views.uuid_generator import getNewUUID_id

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



@module.route('/api/patient.json')
@public_endpoint
def api_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
        return jsonify({
            'clientData': context.make_client_info(client),
            'records': context.make_records(client),
            'events': context.make_events(client)
        })
    else:
        client = Client()
        return jsonify({
            'clientData': context.make_client_info(client)
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
    print_templates = rbPrintTemplate.query.filter(rbPrintTemplate.context == 'token').all()
    context = ClientVisualizer(Format.JSON)
    print_context = PrintTemplateVisualizer()
    return jsonify({'clients': map(context.make_client_info, clients),
                    'print_templates': map(print_context.make_template_info, print_templates),
                    })


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
        if client_id:
            client = Client.query.get(client_id)
        else:
            client = create_new_client()

        client.lastName = client_info['lastName']
        client.firstName = client_info['firstName']
        client.patrName = client_info['patrName']
        client.sexCode = 1 if client_info['sex'] == u'М' else 2
        client.SNILS = client_info['SNILS'].replace(" ", "").replace("-", "") if client_info['SNILS'] else ''
        client.notes = client_info['notes'] if client_info['notes'] else ''
        client.birthDate = client_info['birthDate']
        client.uuid_id = getNewUUID_id()

        db.session.add(client)
        db.session.commit()

        if not client.document and client_info['document']['number']:
            client_document = create_new_document(client.id, client_info['document'])
            db.session.add(client_document)
        else:
            client.document.serial = client_info['document']['serial']
            client.document.number = client_info['document']['number']
            client.document.date = client_info['document']['begDate']
            client.document.endDate = client_info['document']['endDate']
            client.document.origin = client_info['document']['origin']
            client.document.documentType = rbDocumentType.query.filter(rbDocumentType.code ==
                                                                       client_info['document']['typeCode']).first()

        if client.compulsoryPolicy and check_edit_policy(client.compulsoryPolicy,
                                                         client_info['compulsoryPolicy']['serial'],
                                                         client_info['compulsoryPolicy']['number'],
                                                         client_info['compulsoryPolicy']['typeCode']):
            client.compulsoryPolicy.begDate = client_info['compulsoryPolicy']['begDate']
            client.compulsoryPolicy.endDate = client_info['compulsoryPolicy']['endDate']
            client.compulsoryPolicy.insurer_id = client_info['compulsoryPolicy']['insurer_id']
            client.compulsoryPolicy.modifyDatetime = datetime.datetime.now()
        elif client_info['compulsoryPolicy']['number']:
            client.compulsoryPolicy.deleted = 2
            compulsory_policy = create_new_policy(client_info['compulsoryPolicy'], client.id)
            compulsory_policy.policyType = rbPolicyType.query.filter(rbPolicyType.code ==
                                                                     client_info['compulsoryPolicy']['typeCode']).first()
            db.session.add(compulsory_policy)

        if client.voluntaryPolicy and check_edit_policy(client.compulsoryPolicy,
                                                        client_info['voluntaryPolicy']['serial'],
                                                        client_info['voluntaryPolicyy']['number'],
                                                        client_info['voluntaryPolicy']['typeCode']):
            client.voluntaryPolicy.begDate = client_info['voluntaryPolicy']['begDate']
            client.voluntaryPolicy.endDate = client_info['voluntaryPolicy']['endDate']
            client.voluntaryPolicy.insurer_id = client_info['voluntaryPolicy']['insurer_id']
            client.voluntaryPolicy.modifyDatetime = datetime.datetime.now()
        elif client_info['voluntaryPolicy']['number']:
            client.voluntaryPolicy.deleted = 2
            voluntary_policy = create_new_policy(client_info['voluntaryPolicy'], client.id)
            client.voluntaryPolicy.policyType = rbPolicyType.query.filter(rbPolicyType.code ==
                                                                          client_info['voluntaryPolicy']['typeCode']).first()
            db.session.add(voluntary_policy)

        for soc_status in client_info['socStatuses']:
            if not 'id' in soc_status:
                item = create_new_soc_status(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == soc_status['id'], client.socStatuses)[0]
            item.deleted = soc_status['deleted']
            item.soc_status_class = rbSocStatusClass.query.filter(rbSocStatusClass.code ==
                                                                  soc_status['classCode']).first()
            item.socStatusType = rbSocStatusType.query.filter(rbSocStatusType.code ==
                                                              soc_status['typeCode']).first()
            item.begDate = soc_status['begDate'].split('T')[0]
            if soc_status['endDate']:
                item.endDate = soc_status['endDate'].split('T')[0]

        for allergy in client_info['allergies']:
            if not 'id' in allergy:
                item = create_new_allergy(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == allergy['id'], client.allergies)[0]
            item.name = allergy['nameSubstance']
            item.createDate = allergy['createDate'].split('T')[0]
            item.power = allergy['power']
            item.notes = allergy['notes']
            item.deleted = allergy['deleted']

        for intolerance in client_info['intolerances']:
            if not 'id' in intolerance:
                item = create_new_intolerance(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == intolerance['id'], client.intolerances)[0]
            item.name = intolerance['nameMedicament']
            item.createDate = intolerance['createDate'].split('T')[0]
            item.power = intolerance['power']
            item.notes = intolerance['notes']
            item.deleted = intolerance['deleted']

        for identification in client_info['identifications']:
            if not 'id' in identification:
                item = create_new_identification(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == identification['id'], client.identifications)[0]
            item.accountingSystems = rbAccountingSystem.query.filter(rbAccountingSystem.code == identification['accountingSystem_code']).first()
            item.checkDate = identification['checkDate'].split('T')[0]
            item.identifier = identification['identifier']
            item.deleted = identification['deleted']

        for blood in client_info['bloodHistory']:
            if not 'id' in blood:
                item = Bloodhistory()
                item.client_id = client.id
                db.session.add(item)
                item.bloodType = rbBloodType.query.filter(rbBloodType.code == blood['bloodGroup_code']).first()
                item.bloodDate = blood['bloodDate'].split('T')[0]
                item.person_id = blood['person_id']

        for relation in client_info['direct_relations']:
            if not 'id' in relation:
                item = create_new_direct_relation(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == relation['id'], client.direct_relations)[0]
            item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
            item.other = Client.query.filter(Client.id == relation['other_id']).first()

        for relation in client_info['reversed_relations']:
            if not 'id' in relation:
                item = create_new_reversed_relation(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == relation['id'], client.reversed_relations)[0]
            item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
            item.other = Client.query.filter(Client.id == relation['other_id']).first()

        for contact in client_info['contacts']:
            if not 'id' in contact:
                item = create_new_contact(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == contact['id'], client.contacts)[0]
            item.contactType = rbContactType.query.filter(rbContactType.code == contact['contactType_code']).first()
            item.contact = contact['contact']
            item.deleted = contact['deleted']
            item.notes = contact['notes']

        db.session.commit()
    except KeyError or ValueError:
        return abort(404)

    return ''


@module.route('/api/save_delete_document.json')
@public_endpoint
def api_delete_document():
    document_info = json.loads(request.args['document'])
    if 'documentText' in document_info:
        document = ClientDocument.query.get(document_info['id'])
    elif 'policyText' in document_info:
        document = ClientPolicy.query.get(document_info['id'])
    document.deleted = 1
    db.session.add(document)
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
    return jsonify({'action': v.make_action(action),
                    'print_templates': map(print_context.make_template_info, print_templates)
                    })
