# -*- coding: utf-8 -*-

import datetime
import itertools

from collections import defaultdict
from application.systemwide import db

from application.lib.utils import safe_unicode, safe_int, safe_dict
from application.models.enums import EventPrimary, EventOrder, ActionStatus, Gender
from application.models.event import Event, EventType, Diagnosis, Diagnostic

from application.models.schedule import Schedule, rbReceptionType, ScheduleClientTicket, ScheduleTicket
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

    def make_client_ticket_record(self, client_ticket):
        return {
            'id': client_ticket.id,
            'client_id': client_ticket.client_id,
            'event_id': client_ticket.event_id,
            'finance': client_ticket.event.finance if client_ticket.event else None,
            'appointment_type': client_ticket.appointmentType,
            'note': client_ticket.note,
        }

    def make_ticket(self, ticket):
        client_ticket = ticket.client_ticket
        client_id = client_ticket.client_id if client_ticket else None
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client_id else 'free',
            'client': ticket.client.shortNameText if client_id else None,
            'attendance_type': ticket.attendanceType,
            'office': ticket.schedule.office.name if ticket.schedule.office else None,
            'record': self.make_client_ticket_record(client_ticket) if client_ticket else None
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
            'speciality': {
                'id': speciality.id,
                'name': speciality.name
            } if speciality else None
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
            if schedule.receptionType and schedule.receptionType.code in result:
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
                day['beg_time'] = min(sched['begTime'] for sched in day['scheds']) if day['scheds'] else None
                day['end_time'] = max(sched['endTime'] for sched in day['scheds']) if day['scheds'] else None
                day['planned_count'] = len(planned_tickets) or None
                day['roa'] = roa
                del day['scheds']
        return result

    def make_persons_schedule(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule(
                Schedule.query.join(Schedule.tickets).filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date).options(db.contains_eager(Schedule.tickets).contains_eager('schedule')),
                start_date, end_date
            )} for person in persons]

    def make_sched_description(self, schedule):
        planned = 0
        CITO = 0
        extra = 0
        busy = False
        planned_tickets = []
        extra_tickets = []
        CITO_tickets = []
        for ticket in schedule.tickets:
            at = ticket.attendanceType.code
            if at == 'planned':
                planned += 1
                planned_tickets.append(self.make_ticket(ticket))
            elif at == 'CITO':
                CITO += 1
                CITO_tickets.append(self.make_ticket(ticket))
            elif at == 'extra':
                extra += 1
                extra_tickets.append(self.make_ticket(ticket))
            if not busy and ticket.client_ticket:
                busy = True
        return {
            'id': schedule.id,
            'office': safe_dict(schedule.office),
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
            'reception_type': safe_dict(schedule.receptionType),
            'tickets': CITO_tickets + planned_tickets + extra_tickets
        }

    def collapse_scheds_description(self, scheds):
        info = {}
        roa = None
        busy = False
        sub_scheds = []
        for sub_sched in scheds:
            if not busy and sub_sched['busy']:
                busy = True

            if not roa and sub_sched['roa']:
                roa = sub_sched['roa']
                # На день установлена причина отсутствия - не может быть приема
                continue

            rec_type = sub_sched['reception_type']
            info_rt = info.setdefault(rec_type['code'], {'planned': 0, 'CITO': 0, 'extra': 0})

            info_rt['planned'] += sub_sched['planned']
            info_rt['CITO'] += sub_sched['CITO']
            info_rt['extra'] += sub_sched['extra']
            sub_scheds.append(sub_sched)
        return {
            'scheds': sub_scheds if not roa else [],
            'info': info,
            'busy': busy,
            'roa': roa
        }

    def make_schedule_description(self, schedules, date_start, date_end):

        def new_empty_day(offset):
            return {
                'date': date_start + datetime.timedelta(days=offset),
                'scheds': []
            }

        result = [new_empty_day(day_offset) for day_offset in xrange((date_end - date_start).days)]

        for schedule in schedules:
            idx = (schedule.date - date_start).days
            result[idx]['scheds'].append(self.make_sched_description(schedule))

        for day in result:
            day.update(self.collapse_scheds_description(day['scheds']))

        return result

    def make_person_schedule_description(self, person, start_date, end_date):
        schedules_by_date = (Schedule.query.join(Schedule.tickets)
                             .filter(Schedule.person_id == person.id,
                                     start_date <= Schedule.date, Schedule.date < end_date,
                                     Schedule.deleted == 0)
                             .order_by(Schedule.date)
                             .order_by(Schedule.begTime)
                             .options(db.contains_eager(Schedule.tickets).contains_eager('schedule')))
        return {
            'person': self.make_person(person),
            'schedules': self.make_schedule_description(schedules_by_date, start_date, end_date)
        }


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

    def make_addresses_info(self, client):
        reg_addr = client.reg_address
        live_addr = client.loc_address
        if reg_addr and live_addr:
            if client.has_identical_addresses():
                live_addr = {
                    'id': live_addr.id,
                    'synced': True,
                }
        return safe_dict(reg_addr), safe_dict(live_addr)

    def make_relation_info(self, client_id, relation):
        if client_id == relation.client_id:
            return {
                'id': relation.id,
                'deleted': relation.deleted,
                'rel_type': relation.relativeType,
                'relative': self.make_short_client_info(relation.relative),
                'direct': True,
            }
        elif client_id == relation.relative_id:
            return {
                'id': relation.id,
                'deleted': relation.deleted,
                'rel_type': relation.relativeType,
                'relative': self.make_short_client_info(relation.client),
                'direct': False,
            }
        else:
            raise ValueError('Relation info does not match Client')

    def make_client_info(self, client):
        reg_addr, live_addr = self.make_addresses_info(client)

        relations = [self.make_relation_info(client.id, relation) for relation in client.client_relations]

        documents = [safe_dict(doc) for doc in client.documents_all]
        policies = [safe_dict(policy) for policy in client.policies_all]
        document_history = documents + policies
        # identifications = [self.make_identification_info(identification) for identification in client.identifications]
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
            'relations': relations,
            'contacts': client.contacts.all(),
            'phones': client.phones,
            'document_history': document_history,
            # 'identifications': identifications,
        }

    def make_client_info_for_event(self, client):
        reg_addr, live_addr = self.make_addresses_info(client)
        relations = [self.make_relation_info(client.id, relation) for relation in client.client_relations]
        return {
            'info': client,
            'id_document': client.id_document,
            'reg_address': reg_addr,
            'live_address': live_addr,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies,
            'relations': relations,
            'phones': client.phones,
            'work_org_id': client.works[0].org_id if client.works else None,  # FIXME: ...
        }

    def make_search_client_info(self, client):
        return {
            'info': client,
            'id_document': client.id_document,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies
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
            'sex': Gender(client.sexCode) if client.sexCode is not None else None,
            'full_name': client.nameText
        }

    def make_client_info_for_servicing(self, client):
        return {
            'client_data': self.make_search_client_info(client),
            'appointments': self.make_appointments(client),
            'events': self.make_events(client)
        }

    def make_appointments(self, client, every=False):
        if every:
            return map(
                self.make_appointment,
                client.appointments
            )
        else:
            appointments = (client.appointments.join(ScheduleClientTicket.ticket).join(ScheduleTicket.schedule).
                            filter(ScheduleClientTicket.event_id.is_(None)).
                            order_by(Schedule.date.desc(), ScheduleTicket.begTime.desc()))
            return map(
                self.make_appointment,
                appointments
            )

    def make_appointment(self, apnt):
        return {
            'id': apnt.id,
            'mark': None,
            'date': apnt.ticket.schedule.date,
            'begDateTime': apnt.ticket.begDateTime,
            'office': apnt.ticket.schedule.office,
            'person': safe_unicode(apnt.ticket.schedule.person),
            'createPerson': apnt.createPerson,
            'note': apnt.note,
            'receptionType': apnt.ticket.schedule.receptionType,
            'person_id': apnt.ticket.schedule.person_id,
            'org_from': apnt.org_from,
            'event_id': apnt.event_id,
            'attendance_type': apnt.ticket.attendanceType,
            'ticket_id': apnt.ticket_id
        }

    def make_events(self, client):
        return map(
            self.make_event,
            (client.events.join(EventType).join(rbRequestType)
             .filter(rbRequestType.code == u'policlinic')
             .order_by(Event.setDate.desc()))
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
            'doc_type': safe_dict(id_doc.documentType) if id_doc else None,
            'doc_type_id': id_doc.id if id_doc else None,
            'serial_left': id_doc.serial_left if id_doc else None,
            'serial_right': id_doc.serial_right if id_doc else None,
            'number': id_doc.number if id_doc else None,
            'reg_address': safe_unicode(client.reg_address),
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
    def make_short_event(self, event):
        return {
            'id': event.id,
            'client_id': event.client_id,
            'client_full_name': event.client.nameText,
            'beg_date': event.setDate,
            'end_date': event.execDate,
            'type_name': event.eventType.name,
            'person_short_name': event.execPerson.shortNameText if event.execPerson else u'Нет',
        }
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
            'client': cvis.make_client_info_for_event(event.client),
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
            'note': event.note,
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
            'status': action.status,
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
