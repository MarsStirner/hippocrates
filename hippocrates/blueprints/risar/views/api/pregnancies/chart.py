# -*- coding: utf-8 -*-
from datetime import datetime

from flask import request
from flask_login import current_user
from nemesis.models.organisation import OrganisationBirthCareLevel
from nemesis.models.risar import rbPerinatalRiskRate

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import default_AT_Heuristic, check_card_attrs_action_integrity, \
    reevaluate_dates, default_ET_Heuristic
from hippocrates.blueprints.risar.lib.represent import represent_event, represent_chart_for_routing, represent_header, \
    group_orgs_for_routing, represent_checkups, represent_card_attributes, \
    represent_chart_for_epicrisis, represent_chart_for_card_fill_rate_history, \
    represent_chart_for_close_event
from hippocrates.blueprints.risar.lib.utils import get_last_checkup_date, bail_out
from hippocrates.blueprints.risar.risar_config import attach_codes, request_type_pregnancy, request_type_gynecological
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.data import create_action
from nemesis.lib.utils import get_new_event_ext_id, safe_traverse, safe_datetime
from nemesis.models.client import Client, ClientAttach
from nemesis.models.enums import EventPrimary, EventOrder, PerinatalRiskRate
from nemesis.models.event import Event, EventType
from nemesis.models.exists import Organisation, Person, rbAttachType, rbRequestType, MKB
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


class ChartCreator(object):
    def __init__(self, client_id, ticket_id, event_id):
        self.automagic = False
        self.event = None
        self.ticket = None
        self.action = None
        self.client = None
        self.ticket_id = ticket_id
        self.client_id = client_id
        self.event_id = event_id

    def _fill_new_event(self):
        at = default_AT_Heuristic(self.event.eventType) or bail_out(
            ApiException(500, u'Не найден подходящий тип действия для типа обращения %s' % self.event.eventType.name)
        )

        exec_person_id = self.ticket.ticket.schedule.person_id if self.ticket else current_user.get_main_user().id
        exec_person = Person.query.get(exec_person_id)
        self.event.execPerson = exec_person
        self.event.orgStructure = exec_person.org_structure
        self.event.organisation = exec_person.organisation

        self.event.isPrimaryCode = EventPrimary.primary[0]
        self.event.order = EventOrder.planned[0]

        note = self.ticket.note if self.ticket else ''
        self.event.client = self.client
        self.event.setDate = datetime.now()
        self.event.note = note
        self.event.externalId = get_new_event_ext_id(self.event.eventType.id, self.client_id)
        self.event.payStatus = 0
        db.session.add(self.event)
        self.action = create_action(at, self.event)
        db.session.add(self.action)

    def __call__(self):
        if not self.event_id and not (self.ticket_id or self.client_id):
            raise ApiException(400, u'Должен быть указан параметр event_id или (ticket_id или client_id)')

        if self.event_id:
            # Вариант 1: к нам пришли с event_id - мы точно знаем, какой Event от нас хотят
            self.event = Event.query.filter(Event.id == self.event_id, Event.deleted == 0).first() or bail_out(ApiException(404, u'Обращение не найдено'))
            self._perform_stored_event_checks()

        else:
            if self.ticket_id:
                # Вариант 2: К нам пришли с ticket_id. есть талончик на приём, по которому можно точно определить
                # Client.id и, возможно, вытащить Event. Он у нас главный в этом плане.
                self.ticket = ScheduleClientTicket.query.get(self.ticket_id) or bail_out(ApiException(404, u'Талончик на приём не найден'))
                self.event = self.ticket.event
                self.client_id = self.ticket.client_id

            if not self.event or self.event.deleted:
                # Вариант 3 или 2.1: к нам пришли без ticket_id, либо ScheduleClientTicket ещё не связан с Event.
                # Мы надеемся, что к нам пришли с client_id, если пришли без ticket_id
                # Если это повторный приём по нашему типу обращения, то мы его найдём следующей функцией. Если нет, то
                # сработает последний вариант - далее
                self._find_appropriate_event()

            if not self.event:
                # Вариант 4 или 2.2: Мы так и не нашли подходящего обращения, и пытаемся его создать.
                self.event = Event()
                self.client = Client.query.get(self.client_id)
                self._create_appropriate_event()
                self._fill_new_event()
                self.automagic = True

            if self.ticket:
                # Аппендикс к варианту 2: К нам пришли с тикетом, и нам надо его связать с обращением.
                self.ticket.event = self.event
                db.session.add(self.ticket)

            db.session.commit()
            self._perform_post_create_event_checks()

    def _perform_stored_event_checks(self):
        pass

    def _find_appropriate_event(self):
        pass

    def _create_appropriate_event(self):
        pass

    def _perform_post_create_event_checks(self):
        pass


class PregnancyChartCreator(ChartCreator):
    def _find_appropriate_event(self):
        # проверка наличия у пациентки открытого обращения, созданного по одному из прошлых записей на приём
        self.event = Event.query.join(EventType, rbRequestType).filter(
            Event.client_id == self.client_id,
            Event.deleted == 0,
            rbRequestType.code == request_type_pregnancy,
            Event.execDate.is_(None)
        ).order_by(Event.setDate.desc()).first()

    def _create_appropriate_event(self):
        event_type = default_ET_Heuristic(request_type_pregnancy) or bail_out(
            ApiException(500, u'Не настроен тип события - Случай беременности ОМС')
        )
        self.event.eventType = event_type

    def _perform_stored_event_checks(self):
        if self.event.eventType.requestType.code != request_type_pregnancy:
            raise ApiException(400, u'Обращение не является случаем беременности')
        card = PregnancyCard.get_for_event(self.event)
        self.action = card.attrs
        check_card_attrs_action_integrity(self.action)

    def _perform_post_create_event_checks(self):
        card = PregnancyCard.get_for_event(self.event)
        if self.action:
            card._card_attrs_action = self.action
        card.reevaluate_card_attrs()
        db.session.commit()


class GynecologicCardCreator(ChartCreator):
    def _find_appropriate_event(self):
        # проверка наличия у пациентки открытого обращения, созданного по одному из прошлых записей на приём
        self.event = Event.query.join(EventType, rbRequestType).filter(
            Event.client_id == self.client_id,
            Event.deleted == 0,
            rbRequestType.code == request_type_gynecological,
            Event.execDate.is_(None)
        ).order_by(Event.setDate.desc()).first()

    def _create_appropriate_event(self):
        event_type = default_ET_Heuristic(request_type_gynecological) or bail_out(
            ApiException(500, u'Не настроен тип события - Гинекологический Приём ОМС')
        )
        self.event.eventType = event_type

    def _perform_stored_event_checks(self):
        if self.event.eventType.requestType.code != request_type_gynecological:
            raise ApiException(400, u'Обращение не является гинекологиечским приёмом')
        card = PregnancyCard.get_for_event(self.event)
        self.action = card.attrs
        check_card_attrs_action_integrity(self.action)

    def _perform_post_create_event_checks(self):
        card = PregnancyCard.get_for_event(self.event)
        if self.action:
            card._card_attrs_action = self.action
        card.reevaluate_card_attrs()
        db.session.commit()


@module.route('/api/0/chart/')
@module.route('/api/0/chart/<int:event_id>')
@api_method
def api_0_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = PregnancyChartCreator(client_id, ticket_id, event_id)
    chart_creator()

    return {
        'event': represent_event(chart_creator.event),
        'automagic': chart_creator.automagic
    }


@module.route('/api/0/gyn-chart/')
@module.route('/api/0/gyn-chart/<int:event_id>')
@api_method
def api_0_gyn_chart(event_id=None):
    ticket_id = request.args.get('ticket_id')
    client_id = request.args.get('client_id')

    chart_creator = GynecologicCardCreator(client_id, ticket_id, event_id)
    chart_creator()

    return {
        'event': represent_event(chart_creator.event),
        'automagic': chart_creator.automagic,
    }


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