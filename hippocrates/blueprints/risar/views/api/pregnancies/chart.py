# -*- coding: utf-8 -*-
from datetime import datetime

from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.chart_creator import PregnancyChartCreator
from hippocrates.blueprints.risar.lib.card import PregnancyCard, GynecologicCard
from hippocrates.blueprints.risar.lib.card_attrs import reevaluate_dates
from hippocrates.blueprints.risar.lib.anamnesis import copy_anamnesis_from_gyn_card
from hippocrates.blueprints.risar.lib.represent.common import represent_header, represent_chart_for_close_event
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_event, group_orgs_for_routing, \
    represent_pregnancy_card_attributes, represent_pregnancy_checkup_wm, represent_chart_for_routing, \
    represent_chart_for_card_fill_rate_history, represent_event_for_ambulance
from hippocrates.blueprints.risar.lib.utils import get_last_checkup_date
from hippocrates.blueprints.risar.risar_config import attach_codes, request_type_pregnancy
from hippocrates.blueprints.risar.lib import sirius
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_traverse, safe_datetime
from nemesis.models.client import Client, ClientAttach
from nemesis.models.enums import PerinatalRiskRate
from nemesis.models.event import Event
from nemesis.models.exists import Organisation, rbAttachType
from nemesis.models.organisation import OrganisationBirthCareLevel
from nemesis.models.risar import rbPerinatalRiskRate
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db

__author__ = 'mmalkov'


@module.route('/api/0/pregnancy/chart/ticket/', methods=['DELETE'])
@module.route('/api/0/pregnancy/chart/ticket/<int:ticket_id>', methods=['DELETE'])
@api_method
def api_0_chart_delete(ticket_id):
    # TODO: Security
    ticket = ScheduleClientTicket.query.get(ticket_id)
    if not ticket:
        raise ApiException(404, u'Ticket не найден')
    if not ticket.event:
        raise ApiException(404, u'Event не найден')
    if ticket.event.deleted:
        raise ApiException(400, u'Event уже был удален')
    ticket.event.deleted = 1
    ticket.event = None
    db.session.commit()


@module.route('/api/0/chart/', methods=['GET'])
@module.route('/api/0/chart/<int:event_id>', methods=['GET'])
@api_method
def api_0_pregnancy_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = PregnancyChartCreator(client_id, ticket_id, event_id)
    chart_creator(create=True)
    return {
        'event': represent_pregnancy_event(chart_creator.event),
        'automagic': chart_creator.automagic,
    }


@module.route('/api/1/pregnancy/chart/', methods=['GET'])
@module.route('/api/1/pregnancy/chart/<int:event_id>', methods=['GET'])
@api_method
def api_1_pregnancy_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = PregnancyChartCreator(client_id, ticket_id, event_id)
    try:
        chart_creator()
        return represent_pregnancy_event(chart_creator.event)
    except PregnancyChartCreator.DoNotCreate:
        raise ApiException(201, u'Сначала создайте Event')\


@module.route('/api/0/ambulance/', methods=['GET'])
@module.route('/api/0/ambulance/<int:event_id>', methods=['GET'])
@api_method
def api_0_pregnancy_for_ambulance(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = PregnancyChartCreator(client_id, ticket_id, event_id)
    try:
        chart_creator()
        return represent_event_for_ambulance(chart_creator.event)
    except PregnancyChartCreator.DoNotCreate:
        raise ApiException(201, u'Сначала создайте Event')


@module.route('/api/1/pregnancy/chart/', methods=['POST'])
@module.route('/api/1/pregnancy/chart/<int:event_id>', methods=['PATCH'])
@api_method
def api_1_pregnancy_chart_create(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')
    gyn_event_id = request.args.get('gyn_event_id')

    chart_creator = PregnancyChartCreator(client_id, ticket_id, event_id)
    chart_creator(create=True)

    if request.method == 'PATCH' and request.json:
        chart_creator.event.setDate = safe_datetime(request.json['beg_date'])
        chart_creator.event.execPerson_id = request.json['person']['id']
        db.session.commit()

    if gyn_event_id:
        pc = PregnancyCard.get_for_event(chart_creator.event)
        gc = GynecologicCard.get_by_id(gyn_event_id)
        if pc and gc:
            copy_anamnesis_from_gyn_card(gc, pc)
            db.session.commit()

    return dict(
        represent_pregnancy_event(chart_creator.event),
        automagic=chart_creator.automagic,
    )


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
    # if event.eventType.requestType.code != request_type_pregnancy:
    #     raise ApiException(400, u'Обращение не является случаем беременности')
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
        raise ApiException(400, u'event_id не найден')
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

        sirius.send_to_mis(
            sirius.RisarEvents.CLOSE_CARD,
            sirius.RisarEntityCode.EPICRISIS,
            sirius.OperationCode.READ_ONE,
            'risar.api_integr_epicrisis_get',
            obj=('card_id', event_id),
            params={'card_id': event_id},
            is_create=False,
        )

    return represent_chart_for_close_event(event)


@module.route('/api/0/pregnancy/chart/attach_lpu/', methods=['POST'])
@api_method
def api_0_attach_lpu():
    client_id = request.args.get('client_id', None)
    if client_id is None:
        raise ApiException(400, u'Client не определен')
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
                    raise ApiException(404, u'Attach не найден')

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
        raise ApiException(400, u'Клиент не определен')
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
                    raise ApiException(404, u'Приложение не найдено')

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
    card = PregnancyCard.get_for_event(event)
    return {
        'checkups': map(represent_pregnancy_checkup_wm, card.checkups),
        'card_attributes': represent_pregnancy_card_attributes(card.attrs)
    }