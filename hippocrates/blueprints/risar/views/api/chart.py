# -*- coding: utf-8 -*-
from datetime import datetime

from flask import request
from flask.ext.login import current_user
from nemesis.models.organisation import OrganisationBirthCareLevel
from nemesis.models.risar import rbPerinatalRiskRate

from blueprints.risar.app import module
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.card_attrs import default_AT_Heuristic, get_all_diagnoses, check_card_attrs_action_integrity, \
    reevaluate_dates
from blueprints.risar.lib.represent import represent_event, represent_chart_for_routing, represent_header, \
    group_orgs_for_routing, represent_checkups, represent_card_attributes, \
    represent_chart_for_epicrisis, represent_chart_for_card_fill_rate_history, \
    represent_chart_for_close_event
from blueprints.risar.lib.utils import get_last_checkup_date
from blueprints.risar.risar_config import attach_codes, request_type_pregnancy
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action
from nemesis.lib.diagnosis import create_or_update_diagnosis
from nemesis.lib.utils import get_new_event_ext_id, safe_traverse, safe_datetime
from nemesis.models.actions import Action
from nemesis.models.client import Client, ClientAttach
from nemesis.models.enums import EventPrimary, EventOrder, PerinatalRiskRate
from nemesis.models.event import Event, EventType
from nemesis.models.exists import Organisation, Person, rbAttachType, rbRequestType, rbFinance, MKB
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db


__author__ = 'mmalkov'


@module.route('/api/0/chart/ticket/', methods=['DELETE'])
@module.route('/api/0/chart/ticket/<int:ticket_id>', methods=['DELETE'])
@api_method
def api_0_chart_delete(ticket_id):
    # TODO: Security
    ticket = ScheduleClientTicket.query.get(ticket_id)
    if not ticket:
        raise ApiException(404, 'Ticket not found')
    if not ticket.event:
        raise ApiException(404, 'Event not found')
    if ticket.event.deleted:
        raise ApiException(400, 'Event already deleted')
    ticket.event.deleted = 1
    ticket.event = None
    db.session.commit()


def default_ET_Heuristic():
    return EventType.query \
        .join(rbRequestType, rbFinance) \
        .filter(
            rbRequestType.code == request_type_pregnancy,  # Случай беременности
            rbFinance.code == '2',  # ОМС
            EventType.deleted == 0,
        ) \
        .order_by(EventType.createDatetime.desc())\
        .first()


@module.route('/api/0/chart/')
@module.route('/api/0/chart/<int:event_id>')
@api_method
def api_0_chart(event_id=None):
    automagic = False
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')
    if not event_id and not (ticket_id or client_id):
        raise ApiException(400, u'Должен быть указан параметр event_id или (ticket_id или client_id)')

    if event_id:
        event = Event.query.filter(Event.id == event_id, Event.deleted == 0).first()
        if not event:
            raise ApiException(404, u'Обращение не найдено')
        card = PregnancyCard.get_for_event(event)
        action = card.attrs
        if not action:
            action = card.get_card_attrs_action(True)
        check_card_attrs_action_integrity(action)
    else:
        ext = None
        if ticket_id:
            ticket = ScheduleClientTicket.query.get(ticket_id)
            if not ticket:
                raise ApiException(404, u'Талончик на приём не найден')
            event = ticket.event
            client_id = ticket.client_id
            if not event or event.deleted:
                # проверка наличия у пациентки открытого обращения, созданного по одному из прошлых записей на приём
                event = Event.query.join(EventType, rbRequestType).filter(
                    Event.client_id == client_id,
                    Event.deleted == 0,
                    rbRequestType.code == request_type_pregnancy,
                    Event.execDate.is_(None)
                ).order_by(Event.setDate.desc()).first()
        else:  # client_id is not None
            event = None
            ticket = None
        if not event:
            event = Event()
            at = default_AT_Heuristic()
            if not at:
                raise ApiException(500, u'Нет типа действия с flatCode = cardAttributes')
            ET = default_ET_Heuristic()
            if ET is None:
                raise ApiException(500, u'Не настроен тип события - Случай беременности ОМС')
            event.eventType = ET

            exec_person_id = ticket.ticket.schedule.person_id if ticket else current_user.get_main_user().id
            exec_person = Person.query.get(exec_person_id)
            event.execPerson = exec_person
            event.orgStructure = exec_person.org_structure
            event.organisation = exec_person.organisation

            event.isPrimaryCode = EventPrimary.primary[0]
            event.order = EventOrder.planned[0]

            note = ticket.note if ticket else ''
            event.client = Client.query.get(client_id)
            event.setDate = datetime.now()
            event.note = note
            event.externalId = get_new_event_ext_id(event.eventType.id, client_id)
            event.payStatus = 0
            db.session.add(event)
            ext = create_action(at.id, event)
            db.session.add(ext)
            automagic = True
        if ticket:
            ticket.event = event
            db.session.add(ticket)
        db.session.commit()
        card = PregnancyCard.get_for_event(event)
        if ext:
            card._card_attrs_action = ext
        card.reevaluate_card_attrs()
        db.session.commit()

    if event.eventType.requestType.code != request_type_pregnancy:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'event': represent_event(event),
        'automagic': automagic
    }


@module.route('/api/0/save_diagnoses/', methods=['POST'])
@module.route('/api/0/save_diagnoses/<int:event_id>', methods=['POST'])
@api_method
def api_0_save_diagnoses(event_id=None):
    diagnoses = request.get_json()
    if not event_id:
        raise ApiException(400, u'Должен быть указан параметр event_id')
    event = Event.query.get(event_id)
    card = PregnancyCard(event)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    for diagnosis in diagnoses:
        diag = create_or_update_diagnosis(event, diagnosis)
        if diagnosis['deleted']:
            action = Action.query.get(diagnosis['action_id'])
            property_code = diagnosis['action_property']['code']
            action[property_code].value = [diag for diag in action[property_code].value if diag.id != diagnosis['id']]
        db.session.add(diag)
    db.session.commit()
    card.reevaluate_card_attrs()
    db.session.commit()
    return list(get_all_diagnoses(event))


@module.route('/api/0/mini_chart/')
@module.route('/api/0/mini_chart/<int:event_id>')
@api_method
def api_0_mini_chart(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != request_type_pregnancy:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'header': represent_header(event),
        'chart': represent_chart_for_routing(event)
    }


@module.route('/api/0/chart_measure_list/')
@module.route('/api/0/chart_measure_list/<int:event_id>')
@api_method
def api_0_chart_measure_list(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != request_type_pregnancy:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'last_inspection_date': get_last_checkup_date(event_id)
    }


@module.route('/api/0/chart_card_fill_history/')
@module.route('/api/0/chart_card_fill_history/<int:event_id>')
@api_method
def api_0_chart_card_fill_history(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != request_type_pregnancy:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return represent_chart_for_card_fill_rate_history(event)


@module.route('/api/0/chart_header/')
@module.route('/api/0/chart_header/<int:event_id>')
@api_method
def api_0_chart_header(event_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    if event.eventType.requestType.code != request_type_pregnancy:
        raise ApiException(400, u'Обращение не является случаем беременности')
    return {
        'header': represent_header(event),
    }


@module.route('/api/0/event_routing', methods=['POST'])
@api_method
def api_0_event_routing():
    j = request.get_json()
    diagnoses = j.get('diagnoses', None)
    client_id = j.get('client_id')
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            raise ApiException(404, u'Не найден пациент с id = {0}'.format(client_id))
    else:
        client = None

    query = Organisation.query.filter(Organisation.isLPU == 1)
    if diagnoses:
        max_risk = diagnoses[0]['risk_rate']['value']
        if max_risk > rbPerinatalRiskRate.query.get(PerinatalRiskRate.undefined[0]).value:
            suit_orgs_q = db.session.query(
                Organisation.id.distinct().label('organisation_id')
            ).join(
                OrganisationBirthCareLevel.orgs
            ).filter(
                OrganisationBirthCareLevel.perinatalRiskRate_id == max_risk
            ).subquery('suitableOrgs')
            query = query.join(suit_orgs_q, Organisation.id == suit_orgs_q.c.organisation_id)
    suitable_orgs = query.all()
    orgs = group_orgs_for_routing(suitable_orgs, client)
    return orgs


@module.route('/api/0/chart_close/')
@module.route('/api/0/chart_close/<int:event_id>', methods=['POST'])
@api_method
def api_0_chart_close(event_id=None):
    if not event_id:
        raise ApiException(400, u'Either event_id must be provided')
    else:
        event = Event.query.get(event_id)
        data = request.get_json()
        if data.get('cancel'):
            event.execDate = None
            event.manager_id = None
        else:
            event.execDate = safe_datetime(data['exec_date'])
            event.manager_id = data['manager']['id']
        db.session.commit()
    return represent_chart_for_close_event(event)


@module.route('/api/0/chart/attach_lpu/', methods=['POST'])
@api_method
def api_0_attach_lpu():
    client_id = request.args.get('client_id', None)
    if client_id is None:
        raise ApiException(400, 'Client is not set')
    data = request.get_json()

    result = {}
    for attach_type in data:
        attach_lpu = data[attach_type]
        if attach_lpu:
            if attach_lpu.get('id') is None:
                obj = ClientAttach()
            else:
                obj = ClientAttach.query.get(attach_lpu['id'])
                if obj is None:
                    raise ApiException(404, 'Attach not found')

            obj.client_id = client_id
            obj.attachType = rbAttachType.query.filter(rbAttachType.code == attach_codes[attach_type]).first()
            obj.org = Organisation.query.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.begDate = datetime.now()
            db.session.add(obj)
            result[attach_type] = obj
    db.session.commit()
    return result


@module.route('/api/1/chart/attach_lpu/', methods=['POST'])
@api_method
def api_1_attach_lpu():
    # Оптимизированная версия
    # TODO: проверить работоспособность
    client_id = request.args.get('client_id', None)
    if client_id is None:
        raise ApiException(400, 'Client is not set')
    data = request.get_json()
    now = datetime.now()

    result = {}
    if not data:
        return {}
    orgs = dict(
        (org.id, org)
        for org in Organisation.query.filter(Organisation.id.in_(
            set(safe_traverse(attach_lpu, 'org', 'id') for attach_lpu in data.itervalues())
        ))
    )
    attach_types = dict(
        (at.code, at)
        for at in rbAttachType.query.filter(rbAttachType.code.in_(attach_codes.values()))
    )

    for attach_type, attach_lpu in data.iteritems():
        if attach_lpu:
            if attach_lpu.get('id') is None:
                obj = ClientAttach()
            else:
                obj = ClientAttach.query.get(attach_lpu['id'])
                if obj is None:
                    raise ApiException(404, 'Attach not found')

            obj.client_id = client_id
            # rbAttachType.query.filter(rbAttachType.code == attach_codes[attach_type]).first()
            obj.attachType = attach_types.get(attach_codes[attach_type])
            # Organisation.query.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.org = orgs.get(safe_traverse(attach_lpu, 'org', 'id'))
            obj.begDate = now
            db.session.add(obj)
            result[attach_type] = obj
    db.session.commit()
    return result


@module.route('/api/0/client/<int:client_id>/attach_lpu', methods=['POST'])
@api_method
def api_0_mini_attach_lpu(client_id):
    data = request.get_json()
    event = Event.query.get(data['event_id'])
    card = PregnancyCard.get_for_event(event)
    now = datetime.now()
    attach_type = data['attach_type']
    attach_type_code = attach_codes.get(attach_type, str(attach_type))
    org_id = data.get('org_id', None)
    if not org_id:  # значит сохраняют без изменений привязки
        db.session.rollback()
        return False
    attach = ClientAttach.query.join(rbAttachType).filter(
        rbAttachType.code == attach_type_code,
        ClientAttach.endDate.is_(None),
        ClientAttach.client_id == client_id,
    ).order_by(ClientAttach.modifyDatetime.desc()).first()
    if not attach:
        attach = ClientAttach()
        attach.begDate = now
        attach.attachType = rbAttachType.query.filter(rbAttachType.code == attach_type_code).first()
        attach.client_id = client_id
        db.session.add(attach)
    if attach.LPU_id != org_id:
        attach.LPU_id = org_id
        db.session.commit()
        reevaluate_dates(card)
        db.session.commit()
        return True
    else:
        db.session.rollback()
        return False


@module.route('/api/0/gravidograma/')
@module.route('/api/0/gravidograma/<int:event_id>')
@api_method
def api_0_gravidograma(event_id):
    event = Event.query.get(event_id)
    return {
        'checkups': represent_checkups(event),
        'card_attributes': represent_card_attributes(event)
    }