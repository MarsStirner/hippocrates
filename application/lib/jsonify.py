# -*- coding: utf-8 -*-

import datetime
import itertools

from collections import defaultdict
from sqlalchemy.sql.functions import current_date
from sqlalchemy.sql.expression import between
from flask import json

from application.systemwide import db
from application.lib.data import int_get_atl_dict_all
from application.lib.utils import safe_unicode, safe_int, safe_dict, logger, safe_traverse_attrs
from application.lib.action.utils import action_is_bak_lab
from application.lib.agesex import recordAcceptableEx
from application.models.enums import EventPrimary, EventOrder, ActionStatus, Gender
from application.models.event import Event, EventType, Diagnosis, Diagnostic
from application.models.schedule import Schedule, rbReceptionType, ScheduleClientTicket, ScheduleTicket, QuotingByTime, \
    Office
from application.models.actions import Action, ActionProperty, ActionType
from application.models.exists import rbRequestType, rbService, ContractTariff, Contract
from application.models.client import Client

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
            'office': ticket.schedule.office.code if ticket.schedule.office else None,
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
        office = Office.query.filter(Office.code == person.office).first()
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': {
                'id': speciality.id,
                'name': speciality.name
            } if speciality else None,
            'office': office if office else person.office
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

    def make_quota_description(self, quota):
        return {
            'id': quota.id,
            'time_start': quota.QuotingTimeStart,
            'time_end': quota.QuotingTimeEnd,
            'quoting_type': safe_dict(quota.quotingType),
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

    def make_quotas_description(self, quotas, date_start, date_end):

        def new_empty_day(offset):
            return {
                'date': date_start + datetime.timedelta(days=offset),
                'day_quotas': []
            }

        result = [new_empty_day(day_offset) for day_offset in xrange((date_end - date_start).days)]

        for quota in quotas:
            idx = (quota.quoting_date - date_start).days
            result[idx]['day_quotas'].append(self.make_quota_description(quota))

        return result

    def make_person_schedule_description(self, person, start_date, end_date):
        schedules_by_date = (Schedule.query.outerjoin(Schedule.tickets)
                             .filter(Schedule.person_id == person.id,
                                     start_date <= Schedule.date, Schedule.date < end_date,
                                     Schedule.deleted == 0)
                             .order_by(Schedule.date)
                             .order_by(Schedule.begTime)
                             .order_by(ScheduleTicket.begTime)
                             .options(db.contains_eager(Schedule.tickets).contains_eager('schedule')))
        quoting_by_date = QuotingByTime.query.filter(QuotingByTime.doctor_id == person.id,
                                                     QuotingByTime.quoting_date >= start_date,
                                                     QuotingByTime.quoting_date < end_date)
        return {
            'person': self.make_person(person),
            'schedules': self.make_schedule_description(schedules_by_date, start_date, end_date),
            'quotas': self.make_quotas_description(quoting_by_date, start_date, end_date)
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
            'person_speciality': safe_unicode(getattr(apnt.ticket.schedule.person.speciality, 'name', None)),
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
             .filter(db.or_(rbRequestType.code == u'policlinic', rbRequestType.code == u'4'))
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
            'id': None,
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
            'payer_org_id': None,
            'payer_org': None
        }


class PersonTreeVisualizer(object):
    def make_person(self, person):
        return {
            'id': person.id,
            'name': person.shortNameText,
        }

    def make_person_ws(self, person):
        return {
            'id': person.id,
            'name': person.shortNameText,
            'speciality': self.make_short_speciality(person.speciality)
        }

    def make_short_speciality(self, speciality):
        return {
            'id': speciality.id,
            'name': speciality.name
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
            'actions': map(self.make_action, event.actions),
        }

    def make_diagnoses(self, event):
        """
        @type event: Event
        """
        result = []
        for diagnostic in event.diagnostics:
            result.append(self.make_diagnostic_record(diagnostic))
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

    def make_diagnostic_record(self, diagnostic):
        """
        :type diagnostic: application.models.event.Diagnostic
        :param diagnostic:
        :return:
        """
        pvis = PersonTreeVisualizer()
        return {
            'id': diagnostic.id,
            'set_date': diagnostic.setDate,
            'end_date': diagnostic.endDate,
            'diagnosis_type': diagnostic.diagnosisType,
            'diagnosis': self.make_diagnosis_record(diagnostic.diagnosis),
            'character': diagnostic.character,
            'person': pvis.make_person_ws(diagnostic.person),
            'notes': diagnostic.notes,
            'action_id': diagnostic.action_id,
            'result': diagnostic.result,
            'ache_result': diagnostic.rbAcheResult,

            'health_group': diagnostic.healthGroup,
            'trauma_type': diagnostic.traumaType,
            'phase': diagnostic.phase,
            'stage': diagnostic.stage,
            'dispanser': diagnostic.dispanser,
            'sanatorium': diagnostic.sanatorium,
            'hospital': diagnostic.hospital,
            'diagnosis_description': diagnostic.diagnosis_description
        }

    def make_diagnosis_record(self, diagnosis):
        """
        :type diagnosis: application.models.event.Diagnosis
        :param diagnosis:
        :return:
        """
        return {
            'id': diagnosis.id,
            'mkb': diagnosis.mkb,
            'mkbex': diagnosis.mkb_ex,
            'client_id': diagnosis.client_id,
        }

    def make_action_type(self, action_type):
        """
        :type action_type: application.models.actions.ActionType
        """
        return {
            'id': action_type.id,
            'name': action_type.name,
            'code': action_type.code,
            'flat_code': action_type.flatCode,
            'class': action_type.class_,
            'is_required_tissue': action_type.isRequiredTissue,
        }

    def make_action(self, action):
        """
        @type action: Action
        """
        return {
            'id': action.id,
            'name': action.actionType.name,
            'type': self.make_action_type(action.actionType),
            'status': ActionStatus(action.status),
            'begDate': action.begDate,
            'endDate': action.endDate,
            'person_text': safe_unicode(action.person)
        }

    def make_event_payment(self, event, client=None):
        if client:
            cvis = ClientVisualizer()
            lc = cvis.make_payer_for_lc(client)
            payments = []
        else:
            if event:
                lc = event.localContract
            else:
                from blueprints.event.lib.utils import create_new_local_contract
                lc = create_new_local_contract({
                    'date_contract': datetime.date.today(),
                    'number_contract': ''
                })
            payments = [payment
                        for payment in event.payments
                        if payment.master_id == event.id] if event else []
        return {
            'local_contract': lc,
            'payments': payments
        }

    def make_event_services(self, event_id):

        def make_raw_service_group(action, service_id, at_code, at_name, service_name, price, at_context):
            service = {
                'at_id': action.actionType_id,
                'service_id': service_id,
                'at_code': at_code,
                'at_name': at_name,
                'service_name': service_name,
                'action': action,
                'price': price,
                'is_lab': False,
                'print_context': at_context
            }

            client = Client.query.get(action.event.client_id)
            client_age = client.age_tuple(datetime.date.today())

            at_id = service['at_id']
            at_data = ats_apts.get(at_id)
            if at_data and at_data[9]:
                prop_types = at_data[9]
                prop_types = [prop_type[:2] for prop_type in prop_types if recordAcceptableEx(client.sexCode,
                                                                                              client_age,
                                                                                              prop_type[3],
                                                                                              prop_type[2])]
                if prop_types:
                    service['is_lab'] = True
                    service['assignable'] = prop_types
            return service

        def make_action_as_service(a, service):
            action = {
                'action_id': a.id,
                'account': a.account,
                'amount': a.amount,
                'beg_date': a.begDate,
                'end_date': a.endDate,
                'status': a.status,
                'coord_date': a.coordDate,
                'coord_person': person_vis.make_person(a.coordPerson) if a.coordPerson else None,
                'sum': service['price'] * a.amount,
            }
            if service['is_lab']:
                action['assigned'] = [prop.type_id for prop in a.properties if prop.isAssigned]
                action['planned_end_date'] = a.plannedEndDate
            return action

        def shrink_service_group(group):
            actions = [make_action_as_service(act_serv.pop('action'), act_serv) for act_serv in service_group]
            total_amount = sum([act['amount'] for act in actions])
            total_sum = sum([act['sum'] for act in actions])

            def calc_all_assigned(actions):
                # [] - all have same assignments, False - have different assignments
                ref_asgn_list = actions[0]['assigned']
                return all(map(lambda act: act['assigned'] == ref_asgn_list, actions)) and ref_asgn_list

            def calc_all_ped(actions):
                # datetime.datetime - all have same planned end date, False - have different dates
                ref_action_ped = actions[0]['planned_end_date']
                return all(map(lambda act: act['planned_end_date'] == ref_action_ped, actions)) and ref_action_ped

            result_service = dict(
                group[0],
                actions=actions,
                total_amount=total_amount,
                sum=total_sum
            )
            if result_service['is_lab']:
                result_service['all_assigned'] = calc_all_assigned(actions)
                result_service['all_planned_end_date'] = calc_all_ped(actions)

            return result_service

        person_vis = PersonTreeVisualizer()
        query = db.session.query(
            Action,
            ActionType.service_id,
            ActionType.code,
            ActionType.name,
            rbService.name,
            ContractTariff.price,
            ActionType.context
        ).join(
            Event,
            EventType,
            Contract,
            ContractTariff,
            ActionType
        ).join(
            rbService, ActionType.service_id == rbService.id
        ).filter(
            Action.event_id == event_id,
            ContractTariff.eventType_id == EventType.id,
            ContractTariff.service_id == ActionType.service_id,
            Action.deleted == 0,
            ContractTariff.deleted == 0,
            between(current_date(), ContractTariff.begDate, ContractTariff.endDate)
        )

        ats_apts = int_get_atl_dict_all()

        services_by_at = defaultdict(list)
        for a, service_id, at_code, at_name, service_name, price, at_context in query:
            services_by_at[(a.actionType_id, service_id)].append(
                make_raw_service_group(a, service_id, at_code, at_name, service_name, price, at_context)
            )
        services_grouped = []
        for key, service_group in services_by_at.iteritems():
            services_grouped.append(
                shrink_service_group(service_group)
            )

        return services_grouped


class ActionVisualizer(object):
    def make_action(self, action):
        """
        @type action: Action
        """
        result = {
            'action': {
                'id': action.id,
                'action_type': action.actionType,
                'event_id': action.event_id,
                'client': action.event.client,
                'direction_date': action.directionDate,
                'beg_date': action.begDate,
                'end_date': action.endDate,
                'planned_end_date': action.plannedEndDate,
                'status': ActionStatus(action.status),
                'set_person': action.setPerson,
                'person': action.person,
                'note': action.note,
                'office': action.office,
                'amount': action.amount,
                'uet': action.uet,
                'pay_status': action.payStatus,
                'account': action.account,
                'is_urgent': action.isUrgent,
                'coord_date': action.coordDate,
                'properties': [
                    self.make_property(prop)
                    for prop in action.properties
                ]
            },
            'layout': self.make_action_layout(action)
        }
        if action_is_bak_lab(action):
            result['bak_lab_info'] = self.make_bak_lab_info(action)
        return result

    def make_action_layout(self, action):
        """
        :type action: Action
        :param action:
        :return:
        """
        at_layout = action.actionType.layout
        if at_layout:
            try:
                at_layout = json.loads(at_layout)
            except ValueError:
                logger.warning('Bad layout for ActionType with id = %s' % action.actionType.id)
            else:
                return at_layout
        # default layout
        layout = {
            'tagName': 'root',
            'children': [{
                'tagName': 'ap',
                'id': ap.type.id,
            } for ap in action.properties]
        }
        if action_is_bak_lab(action):
            layout['children'].append({
                'tagName': 'bak_lab_view',
            })
        return layout
    
    def make_property(self, prop):
        """
        @type prop: ActionProperty
        """
        if prop.value is None:
            value = [] if prop.type.isVector else None
        elif prop.type.isVector:
            maker = getattr(self, 'make_ap_%s' % prop.type.typeName, None)
            value = [maker(v) for v in prop.value] if maker else [v for v in prop.value]
        else:
            maker = getattr(self, 'make_ap_%s' % prop.type.typeName, None)
            value = maker(prop.value) if maker else prop.value
        return {
            'id': prop.id,
            'idx': prop.type.idx,
            'type': prop.type,
            'is_assigned': prop.isAssigned,
            'value': value,
        }

    # Здесь будут кастомные мейкеры экшон пропертей.

    @staticmethod
    def make_ap_OrgStructure(value):
        """
        :type value: application.models.exists.OrgStructure
        :param value:
        :return:
        """
        return {
            'id': value.id,
            'name': value.name,
            'code': value.code,
            'parent_id': value.parent_id, # for compatibility with Reference
        }

    @staticmethod
    def make_ap_Diagnosis(value):
        """
        :type value: application.models.event.Diagnostic
        :param value:
        :return:
        """
        evis = EventVisualizer()
        return evis.make_diagnostic_record(value)

    # ---

    def make_bak_lab_info(self, action):
        bbt_response = action.bbt_response
        if not bbt_response:
            return None

        def make_comment(comment):
            return {
                'id': comment.id,
                'text': comment.valueText
            }

        def make_sens_value(sv):
            return {
                'id': sv.id,
                'mic': sv.MIC,
                'activity': sv.activity,
                'antibiotic': safe_traverse_attrs(sv, 'antibiotic', 'name')
            }

        def make_organism(organism):
            return {
                'id': organism.id,
                'microorganism': safe_traverse_attrs(organism, 'microorganism', 'name'),
                'concentration': organism.concentration,
                'sens_values': [make_sens_value(sv) for sv in organism.sens_values]
            }

        organisms = [make_organism(osm) for osm in bbt_response.values_organism]
        comments = [make_comment(com) for com in bbt_response.values_text]
        pvis = PersonTreeVisualizer()
        result = {
            'doctor': pvis.make_person_ws(bbt_response.doctor),
            'code_lis': bbt_response.codeLIS,
            'defects': bbt_response.defects,
            'final': bool(bbt_response.final),
            'organisms': organisms,
            'comments': comments
        }
        return result
