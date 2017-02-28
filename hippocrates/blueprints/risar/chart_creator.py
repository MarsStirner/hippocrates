# -*- coding: utf-8 -*-
# TODO: Refactor me
from datetime import datetime

from flask_login import current_user
from hippocrates.blueprints.risar.lib import sirius
from hippocrates.blueprints.risar.lib.card import PregnancyCard, GynecologicCard
from hippocrates.blueprints.risar.lib.card_attrs import default_AT_Heuristic, default_ET_Heuristic
from hippocrates.blueprints.risar.lib.chart import transfer_to_person, \
    copy_prev_pregs_on_pregcard_creating, copy_prev_pregs_on_gyncard_creating
from hippocrates.blueprints.risar.lib.notification import NotificationQueue
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy, request_type_gynecological
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data import create_action
from nemesis.lib.utils import get_new_event_ext_id, bail_out
from nemesis.models.client import Client
from nemesis.models.enums import EventPrimary, EventOrder
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.person import Person
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class ChartCreator(object):
    class DoNotCreate(Exception):
        pass

    def __init__(self, client_id=None, ticket_id=None, event_id=None):
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
        right_now = datetime.now()
        self.event.setDate = right_now
        self.event.note = note
        self.event.externalId = get_new_event_ext_id(self.event.eventType.id, self.client_id)
        self.event.payStatus = 0
        db.session.add(self.event)
        self.action = create_action(at, self.event)
        db.session.add(self.action)
        transfer_to_person(self.event, exec_person, right_now)

    def __call__(self, create=False):
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
                if not create:
                    raise self.DoNotCreate()
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

            if self.automagic:
                sirius.send_to_mis(
                    sirius.RisarEvents.CREATE_CARD,
                    sirius.RisarEntityCode.CARD,
                    sirius.OperationCode.READ_ONE,
                    'risar.api_card_get',
                    obj=('card_id', self.event.id),
                    params={'client_id': self.client_id},
                    is_create=self.automagic,
                )

            self._perform_post_create_event_checks()
        return self.event

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

    def _perform_post_create_event_checks(self):
        card = PregnancyCard.get_for_event(self.event)
        if self.action:
            card._card_attrs_action = self.action
        card.reevaluate_card_attrs()
        db.session.commit()
        NotificationQueue.process_events()

    def _fill_new_event(self):
        super(PregnancyChartCreator, self)._fill_new_event()
        copy_prev_pregs_on_pregcard_creating(self.event)


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
        card = GynecologicCard.get_for_event(self.event)
        self.action = card.attrs

    def _perform_post_create_event_checks(self):
        card = GynecologicCard.get_for_event(self.event)
        if self.action:
            card._card_attrs_action = self.action
        card.reevaluate_card_attrs()
        db.session.commit()
        NotificationQueue.process_events()

    def _fill_new_event(self):
        super(GynecologicCardCreator, self)._fill_new_event()
        copy_prev_pregs_on_gyncard_creating(self.event)
