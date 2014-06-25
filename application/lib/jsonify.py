# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import itertools
from application.lib.utils import safe_unicode, safe_int
from application.models.enums import EventPrimary, EventOrder, ActionStatus, Gender
from application.models.event import Event, EventType, Diagnosis, Diagnostic

from application.models.schedule import Schedule, rbReceptionType
from application.models.actions import Action, ActionProperty
from application.models.exists import rbRequestType

__author__ = 'mmalkov'


class Format:
    JSON = 0
    HTML = 1


class ScheduleVisualizer(object):
    def __init__(self):
        self.reception_type = None
        self.client_id = None
        self.reception_types = [at.code for at in rbReceptionType.query]

    def make_ticket(self, ticket):
        client_id = ticket.client_ticket.client_id if ticket.client_ticket else None
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client_id else 'free',
            'client': ticket.client.shortNameText if client_id else None,
            'attendance_type': ticket.attendanceType,
        }

    def make_day(self, schedule):
        return {
            'id': schedule.id,
            'office': schedule.office,
            'tickets': [
                self.make_ticket(ticket)
                for ticket in schedule.tickets
                if not (self.client_id and ticket.client_ticket and ticket.client_ticket.client_id != self.client_id)
            ],
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
        }

    def make_person(self, person):
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_schedule(self, schedules, date_start, date_end):
        one_day = datetime.timedelta(days=1)

        def new_rt():
            date_iter = date_start
            rt_group = []
            while date_iter < date_end:
                rt_group.append({
                    'date': date_iter,
                    'scheds': []
                })
                date_iter += one_day
            return {
                'max_tickets': 0,
                'schedule': rt_group,
            }
        if self.reception_type:
            result = {self.reception_type: new_rt()}
        else:
            result = dict((rt, new_rt()) for rt in self.reception_types)

        for schedule in schedules:
            if schedule.receptionType.code in result:
                result[schedule.receptionType.code]['schedule'][(schedule.date - date_start).days]['scheds'].\
                    append(self.make_day(schedule))

        for group in result.itervalues():
            group['max_tickets'] = max(
                sum(
                    len(sched['tickets'])
                    for sched in day['scheds']
                )
                for day in group['schedule']
            )

        for group in result.itervalues():
            for day in group['schedule']:
                tickets = list(itertools.chain(*(sched['tickets'] for sched in day['scheds'])))
                planned_tickets = sorted(filter(lambda t: t['attendance_type'].code == 'planned', tickets), key=lambda t: t['begDateTime'])
                extra_tickets = filter(lambda t: t['attendance_type'].code == 'extra', tickets)
                CITO_tickets = filter(lambda t: t['attendance_type'].code == 'CITO', tickets)
                day['tickets'] = CITO_tickets + planned_tickets + extra_tickets
                roa = None
                for sched in day['scheds']:
                    if not roa and sched['roa']:
                        roa = sched['roa']
                    del sched['roa']
                day['roa'] = roa
                del day['scheds']
        return result

    def make_persons_schedule(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule(
                Schedule.query.filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date),
                start_date, end_date
            )} for person in persons]

    def make_sched_description(self, schedule):
        planned = 0
        CITO = 0
        extra = 0
        busy = False
        for ticket in schedule.tickets:
            at = ticket.attendanceType.code
            if at == 'planned':
                planned += 1
            elif at == 'CITO':
                CITO += 1
            elif at == 'extra':
                extra += 1
            if not busy and ticket.client_ticket:
                busy = True
        return {
            'id': schedule.id,
            'office': schedule.office,
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
        }

    def collapse_scheds_description(self, scheds):
        planned = 0
        CITO = 0
        extra = 0
        roa = None
        busy = False
        office = None
        mini_scheds = []
        for sched in scheds:
            if not roa and sched['roa']:
                roa = sched['roa']
            if not busy and sched['busy']:
                busy = True
            if not office and sched['office']:
                office = sched['office']
            planned += sched['planned']
            CITO += sched['CITO']
            extra += sched['extra']
            mini_scheds.append({
                'begTime': sched['begTime'],
                'endTime': sched['endTime'],
            })
        return {
            'scheds': mini_scheds if not roa else [],
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'roa': roa,
            'office': office,
        }

    def make_schedule_description(self, schedules, date_start, date_end):
        one_day = datetime.timedelta(days=1)

        def new_rt():
            date_iter = date_start
            rt_group = []
            while date_iter < date_end:
                rt_group.append({
                    'date': date_iter,
                    'scheds': []
                })
                date_iter += one_day
            return {
                'max_tickets': 0,
                'schedule': rt_group,
            }
        result = dict((rt, new_rt()) for rt in self.reception_types)

        for schedule in schedules:
            rtcode = schedule.receptionType.code if schedule.receptionType else 'amb'
            if rtcode in result:
                result[rtcode]['schedule'][(schedule.date - date_start).days]['scheds'].\
                    append(self.make_sched_description(schedule))

        for group in result.itervalues():
            for day in group['schedule']:
                day.update(self.collapse_scheds_description(day['scheds']))

        return result

    def make_persons_schedule_description(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule_description(
                Schedule.query.filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date).order_by(Schedule.begTime).all(),
                start_date, end_date
                )} for person in persons]


class ClientVisualizer(object):
    def __init__(self, mode=Format.JSON):
        self.__mode = mode

    def make_identification_info(self, identification):
        return {'id': identification.id,
                'deleted': identification.deleted,
                'identifier': identification.identifier,
                'accountingSystem_code': identification.accountingSystems.code,
                'accountingSystem_name': identification.accountingSystems.name,
                'checkDate': identification.checkDate or ''}

    def make_relation_info(self, client_id, relation):
        if client_id == relation.client_id:
            return {
                'type': relation.relativeType,
                'relative': self.make_short_client_info(relation.relative),
                'direct': True,
            }
        else:
            return {
                'type': relation.relativeType,
                'relative': self.make_short_client_info(relation.client),
                'direct': False,
            }

    def make_contact_info(self, contact):
        return {'id': contact.id,
                'deleted': contact.deleted,
                'contactType': contact.contactType,
                'contact': contact.contact,
                'notes': contact.notes}

    def make_client_info(self, client):

        documents = [doc.__json__() for doc in client.documents_all]
        policies = [policy.__json__() for policy in client.policies_all]
        document_history = documents + policies

        identifications = [self.make_identification_info(identification) for identification in client.identifications]
        relations = [self.make_relation_info(client.id, relation) for relation in client.client_relations]
        contacts = [self.make_contact_info(contact) for contact in client.contacts]

        reg_addr = client.reg_address
        live_addr = client.loc_address
        if reg_addr and live_addr:
            if client.has_identical_addresses():
                setattr(live_addr, 'same_as_reg', True)
                setattr(live_addr, 'copy_from_id', reg_addr.id)

        return {
            'info': client,
            'id_document': client.id_document,
            'reg_address': reg_addr,
            'live_address': live_addr,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies,
            'blood_history': client.blood_history.all(),
            'allergies': client.allergies.all(),
            'intolerances': client.intolerances.all(),
            'soc_statuses': client.soc_statuses,

            'document_history': document_history,

            'contact': client.phones,
            'identifications': identifications,
            'relations': relations,
            'contacts': contacts,

        }

    def make_short_client_info(self, client):
        """
        :type client: application.models.client.Client
        :return:
        """
        return {
            'id': client.id,
            'first_name': client.firstName,
            'patr_name': client.patrName,
            'last_name': client.lastName,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': u' '.join(u' '.join((client.firstName, client.patrName, client.lastName)).split())
        }

    def make_appointments(self, client):
        return map(
            self.make_appointment,
            client.appointments#.order_by(ScheduleTicket.begDateTime.desc())
        )

    def make_appointment(self, apnt):
        return {
            'id': apnt.id,
            'mark': None,
            'begDateTime': apnt.ticket.begDateTime,
            'office': apnt.ticket.schedule.office,
            'person': safe_unicode(apnt.ticket.schedule.person),
            'createPerson': apnt.createPerson,
            'note': apnt.note,
            'receptionType': apnt.ticket.schedule.receptionType
        }

    def make_events(self, client):
        return map(
            self.make_event,
            client.events.join(EventType).join(rbRequestType).filter(rbRequestType.code == u'policlinic')
        )

    def make_person(self, person):
        if person is None:
            return {}
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_event(self, event):
        return {
            'id': event.id,
            'externalId': event.externalId,
            'setDate': event.setDate,
            'execDate': event.execDate,
            'person': self.make_person(event.execPerson),
            'requestType': event.eventType.requestType,
            'event_type': event.eventType,
            'result': event.result,
        }

    def make_payer_for_lc(self, client):
        id_doc = client.id_document
        return {
            'first_name': client.firstName,
            'last_name': client.lastName,
            'patr_name': client.patrName,
            'birth_date': client.birthDate,
            'doc_type': id_doc.documentType.__json__() if id_doc else None,
            'doc_type_id': id_doc.id if id_doc else None,
            'serial_left': id_doc.serial_left if id_doc else None,
            'serial_right': id_doc.serial_right if id_doc else None,
            'number': id_doc.number if id_doc else None,
            'reg_address': client.reg_address,
        }


class PersonTreeVisualizer(object):
    def make_person(self, person):
        return {
            'id': person.id,
            'name': person.shortNameText,
        }

    def make_speciality(self, speciality):
        return {
            'id': speciality.id,
            'name': speciality.name,
            'persons': [],
        }

    def make_tree(self, persons):
        specs = defaultdict(list)
        for person in persons:
            if person.speciality:
                specs[person.speciality.name].append(self.make_person(person))


class PrintTemplateVisualizer(object):
    def make_template_info(self, template):
        return {'id': template.id,
                'code': template.code,
                'name': template.name,
                }


class EventVisualizer(object):
    def make_event(self, event):
        """
        @type event: Event
        """
        cvis = ClientVisualizer()
        return {
            'id': event.id,
            'deleted': event.deleted,
            'external_id': event.externalId,
            'order': EventOrder(event.order),
            'order_': event.order,
            'is_primary': EventPrimary(event.isPrimaryCode),
            'is_primary_': event.isPrimaryCode,
            'client': cvis.make_client_info(event.client),
            'client_id': event.client.id,
            'set_date': event.setDate,
            'exec_date': event.execDate,
            'exec_person': event.execPerson,
            'result': event.result,
            'ache_result': event.rbAcheResult,
            'contract': event.contract,
            'event_type': event.eventType,
            'organisation': event.organisation,
            'org_structure': event.orgStructure,
            'med_doc_actions': [self.make_action(action) for action in event.actions if action.actionType.class_ == 0],
            'diag_actions': [self.make_action(action) for action in event.actions if action.actionType.class_ == 1],
            'cure_actions': [self.make_action(action) for action in event.actions if action.actionType.class_ == 2]
        }

    def make_diagnoses(self, event):
        """
        @type event: Event
        """
        result = []
        for diagnostic in event.diagnostics:
            for diagnosis in diagnostic.diagnoses:
                result.append(self.make_diagnose_row(diagnostic, diagnosis))
        return result

    def make_diagnose_row(self, diagnostic, diagnosis):
        """
        @type diagnostic: application.models.event.Diagnostic
        @type diagnosis: Diagnosis
        """
        return {
            'diagnosis_id': diagnosis.id,
            'diagnostic_id': diagnostic.id,
            'diagnosis_type': diagnostic.diagnosisType,
            'person': diagnosis.person,
            'mkb': diagnosis.mkb,
            'mkb_ex': diagnosis.mkb_ex,
            'character': diagnosis.character,
            'phase': diagnostic.phase,
            'stage': diagnostic.stage,
            'health_group': diagnostic.healthGroup,
            'dispanser': diagnosis.dispanser,
            'trauma': diagnosis.traumaType,
            'notes': diagnostic.notes,
        }

    def make_action(self, action):
        """
        @type action: Action
        """
        return {
            'id': action.id,
            'name': action.actionType.name,
            'begDate': action.begDate,
            'endDate': action.endDate,
            'person_text': safe_unicode(action.person)
        }

    def make_event_payment(self, local_contract, event_id=None):
        return {
            'local_contract': local_contract,
            'payments': [payment
                         for payment in local_contract.payments
                         if payment.master_id == event_id] if local_contract else []
        }

    def make_event_services(self, event):
        def make_service(action):
            return {
                'at_id': action.actionType.id,
                'at_code': action.actionType.code,
                'at_name': action.actionType.name,
                'service_name': action.actionType.service.name,
                'price': action.price
            }

        return map(make_service, event.actions)


class ActionVisualizer(object):
    def make_action(self, action):
        """
        @type action: Action
        """
        return {
            'id': action.id,
            'action_type': action.actionType,
            'event_id': action.event_id,
            'client': action.event.client,
            'direction_date': action.directionDate,
            'begDate': action.begDate,
            'endDate': action.endDate,
            'planned_endDate': action.plannedEndDate,
            'status': ActionStatus(action.status),
            'set_person': action.setPerson,
            'person': action.person,
            'note': action.note,
            'office': action.office,
            'amount': action.amount,
            'uet': action.uet,
            'pay_status': action.payStatus,
            'account': action.account,
            'properties': [
                self.make_property(prop)
                for prop in action.properties
            ]
        }
    
    def make_property(self, prop):
        """
        @type prop: ActionProperty
        """
        action_property_type = prop.type
        if action_property_type.isVector:
            values = [item.get_value() for item in prop.raw_values_query.all()]
        else:
            value = prop.raw_values_query.first()
            values = value.get_value() if value else None
        return {
            'id': prop.id,
            'idx': prop.type.idx,
            'type': prop.type,
            'is_assigned': prop.isAssigned,
            'value': values
        }

    def make_abstract_property(self, prop, value):
        """
        @type prop: ActionProperty
        @type value: any
        """
        return {
            'id': prop.id,
            'idx': prop.type.idx,
            'type': prop.type,
            'is_assigned': prop.isAssigned,
            'value': value
        }
