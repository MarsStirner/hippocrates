# -*- coding: utf-8 -*-
import datetime
from flask import g
from sqlalchemy import func

from application.lib.utils import string_to_datetime
from ..models.models_all import Orgstructure, Person, Organisation, v_Client_Quoting, Event, Action, Account, Rbcashoperation, \
    Client, Mkb, EventPayment
from ..models.schedule import ScheduleClientTicket
from gui import applyTemplate
from specialvars import SpecialVariable


def current_patient_orgStructure(event_id):
    from ..models.models_all import ActionProperty, ActionProperty_OrgStructure, Actionpropertytype
    return g.printing_session.query(Orgstructure).\
        join(ActionProperty_OrgStructure, Orgstructure.id == ActionProperty_OrgStructure.value_).\
        join(ActionProperty, ActionProperty.id == ActionProperty_OrgStructure.id).\
        join(Action).\
        join(Actionpropertytype).\
        filter(
            Actionpropertytype.code == 'orgStructStay',
            Action.event_id == event_id,
            Action.deleted == 0).\
        order_by(Action.begDate_raw.desc()).\
        first()


class Print_Template(object):

    def __init__(self):
        self.today = datetime.date.today()

    def update_context(self, template_id, context):
        from ..models.models_all import Rbprinttemplatemeta, Organisation, Orgstructure, Rbservice, Person
        for desc in g.printing_session.query(Rbprinttemplatemeta).filter(Rbprinttemplatemeta.template_id == template_id):
            name = desc.name
            if name not in context:
                continue
            value = context[name]
            typeName = desc.type
            if typeName == 'Integer':
                context[name] = int(value)
            elif typeName == 'Float':
                context[name] = float(value)
            elif typeName == 'Boolean':
                context[name] = bool(value)
            elif typeName == 'Date':
                context[name] = string_to_datetime(value).date() if value else None
            elif typeName == 'Time':
                context[name] = datetime.datetime.strptime(value, '%H:%M').time() if value else None
            elif typeName == 'Organisation':
                context[name] = g.printing_session.query(Organisation).get(int(value)) if value else None
            elif typeName == 'Person':
                context[name] = g.printing_session.query(Person).get(int(value)) if value else None
            elif typeName == 'OrgStructure':
                context[name] = g.printing_session.query(Orgstructure).get(int(value)) if value else None
            elif typeName == 'Service':
                context[name] = g.printing_session.query(Rbservice).get(int(value)) if value else None
            elif typeName == 'MKB':
                context[name] = g.printing_session.query(Mkb).get(int(value)) if value else None

    def print_template(self, doc):
        context_type = doc['context_type']
        template_id = doc['id']
        data = self.get_context(context_type, doc)
        return applyTemplate(template_id, data)

    def get_context(self, context_type, data):
        context = dict(data['context'])
        self.update_context(data['id'], context)
        if 'special_variables' in context:
            # Я надеюсь, что нам не придётся этим пользоваться
            ext = {}
            for sp_name in context['special_variables']:
                ext[sp_name] = SpecialVariable(sp_name, **context)
            del context['special_variables']
            context.update(ext)
        currentOrganisation = g.printing_session.query(Organisation).get(context['currentOrganisation']) if \
            context['currentOrganisation'] else ""
        currentOrgStructure = g.printing_session.query(Orgstructure).get(context['currentOrgStructure']) if \
            context['currentOrgStructure'] else ""
        currentPerson = g.printing_session.query(Person).get(context['currentPerson']) if \
            context['currentPerson'] else ""

        context.update({
            'currentOrganisation': currentOrganisation,
            'currentOrgStructure': currentOrgStructure,
            'currentPerson': currentPerson,
            'SpecialVariable': SpecialVariable
        })

        context_func = getattr(self, 'context_%s' % context_type, None)
        if context_func and callable(context_func):
            context.update(context_func(context))
        return context

    def context_event(self, data):
        event = None
        quoting = None
        client = None
        patient_os = None
        if 'event_id' in data:
            event_id = data['event_id']
            event = g.printing_session.query(Event).get(event_id)
            client = event.client

            client.date = event.execDate.date if event.execDate else self.today
            quoting = g.printing_session.query(v_Client_Quoting).filter_by(event_id=event_id).\
                filter_by(clientId=event.client.id).first()
            if not quoting:
                quoting = v_Client_Quoting()
            patient_os = current_patient_orgStructure(event.id)

        template_context = {
            'event': event,
            'client': client,
            'tempInvalid': None,
            'quoting': quoting,
            'patient_orgStructure': patient_os,
        }
        if 'payment_id' in data:
            template_context['payment'] = g.printing_session.query(EventPayment).get(data['payment_id'])
        return template_context

    def context_action(self, data):
        # ActionEditDialod, ActionInfoFrame
        action_id = data[u'action_id']
        action = g.printing_session.query(Action).get(action_id)
        event = action.event
        event.client.date = event.execDate.date if event.execDate.date else self.today
        quoting = g.printing_session.query(v_Client_Quoting).filter_by(event_id=event.id).\
            filter_by(clientId=event.client.id).first()
        if not quoting:
            quoting = v_Client_Quoting()
        return {
            'event': event,
            'action': action,
            'client': event.client,
            'currentActionIndex': 0,
            'quoting': quoting,
            'patient_orgStructure': current_patient_orgStructure(event.id),
        }

    def context_account(self, data):
        # расчеты (CAccountingDialog)
        account_id = data['account_id']
        account_items_idList = data['account_items_idList']
        accountInfo = g.printing_session.query(Account).get(account_id)
        accountInfo.selectedItemIdList = account_items_idList
        # accountInfo.selectedItemIdList = self.modelAccountItems.idList() ???
        return {
            'account': accountInfo
        }

    def context_cashbook_list(self, data):
        operations = metrics = None

        def get_metrics():
            m = g.printing_session.query(EventPayment).with_entities(
                func.count(),
                func.sum(func.IF(EventPayment.sum > 0, EventPayment.sum, 0)),
                - func.sum(func.IF(EventPayment.sum < 0, EventPayment.sum, 0))
            ).filter(EventPayment.id.in_(data['payments_id_list'])).first()
            return {
                'total': m[0],
                'income': m[1],
                'expense': abs(m[2])
            }

        if 'payments_id_list' in data:
            operations = g.printing_session.query(EventPayment).filter(
                EventPayment.id.in_(data['payments_id_list'])
            ).order_by(EventPayment.date.desc(), EventPayment.id.desc()).all()
            metrics = get_metrics()
        return {
            'operations': operations,
            'metrics': metrics
        }

    def context_person(self, data):
        # PersonDialogcf
        person_id = data['person_id']
        person = g.printing_session.query(Person).get(person_id)
        return {
            'person': person
        }

    def context_registry(self, data):
        # RegistryWindow
        client_id = data['client_id']
        client = g.printing_session.query(Client).get(client_id)
        client.date = self.today
        return {
            'client': client
        }

    def context_preliminary_records(self, data):
        # BeforeRecord
        client_id = data['client_id']
        client_ticket_id = data['ticket_id']
        client = g.printing_session.query(Client).get(client_id)
        client.date = self.today
        client_ticket = g.printing_session.query(ScheduleClientTicket).get(client_ticket_id)
        timeRange = '--:-- - --:--'
        num = 0
        return {
            'client': client,
            'client_ticket': client_ticket
        }

    def context_risar(self, data):
        event = None
        if 'event_id' in data:
            event_id = data['event_id']
            event = g.printing_session.query(Event).get(event_id)
        return {
            'event': event
        }