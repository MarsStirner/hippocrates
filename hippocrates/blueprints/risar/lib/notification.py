# coding: utf-8
import logging

from flask import url_for
from collections import deque
from abc import ABCMeta, abstractmethod

from nemesis.app import app
from nemesis.systemwide import db
from nemesis.models.person import Person, PersonCurationAssoc, rbOrgCurationLevel
from nemesis.models.organisation import Organisation, OrganisationCurationAssoc
from nemesis.models.enums import PerinatalRiskRate
from nemesis.lib.user_mail import send_usermail
from nemesis.lib.data_ctrl.utils import get_system_mail_person_id


logger = logging.getLogger('simple')


class NotificationQueue(object):
    _q = deque()

    @classmethod
    def add_events(cls, *events):
        for evt in events:
            cls._q.append(evt)

    @classmethod
    def process_events(cls):
        while len(cls._q):
            evt = cls._q.popleft()
            try:
                logger.debug(u'Processing notification {0}'.format(repr(evt)))
                evt.process()
            except Exception, e:
                logger.error(evt.get_err_msg(), exc_info=True)

    @classmethod
    def clear(cls):
        cls._q.clear()

    @classmethod
    def notify_checkup_changes(cls, card, action, new_preg_cont):
        if new_preg_cont is None:
            return
        cur_preg_cont_possibility = action['pregnancy_continuation'].value
        new_preg_cont_possibility = new_preg_cont

        if new_preg_cont_possibility != cur_preg_cont_possibility and not bool(new_preg_cont_possibility):
            event = PregContInabilityEvent(card, action)
            cls.add_events(event)

    @classmethod
    def notify_risk_rate_changes(cls, card, new_prr):
        current_rate = card.attrs['prenatal_risk_572'].value
        cur_prr = PerinatalRiskRate(current_rate.id) if current_rate is not None else None

        if new_prr.value not in (PerinatalRiskRate.undefined[0], PerinatalRiskRate.low[0]) and (
                cur_prr is None or cur_prr.order < new_prr.order):
            event = RiskRateRiseEvent(card, new_prr)
            cls.add_events(event)


@app.teardown_request
def clear_notifications_ateor(exception):
    # at the end of request
    NotificationQueue.clear()


class NotificationEvent(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def make_message(self):
        pass

    @abstractmethod
    def get_recipients(self):
        pass

    def send_email(self, recipient_id, subject, text, sender_id=None, parent_id=None):
        if sender_id is None:
            sender_id = get_system_mail_person_id()
        send_usermail(recipient_id, subject, text, sender_id, parent_id)

    def process(self):
        msg = self.make_message()
        recipients = self.get_recipients()
        for rec_id in recipients:
            self.send_email(rec_id, msg['subject'], msg['text'])

    def get_err_msg(self):
        return u'Ошибка отправки уведомлений'

    def __repr__(self):
        return u'{0}'.format(self.__class__.__name__)


class RiskRateRiseEvent(NotificationEvent):

    msg_template = u"""\
У пациентки {p_link} (карта {card_number})
изменилась степень риска на <b>{new_risk}</b>.<br><br>
-----<br>
Это письмо было сгенерировано автоматически
"""

    def __init__(self, card, new_risk):
        self.card = card
        self.card_id = card.event.id
        self.new_risk = new_risk

    def make_message(self):
        patient_name = self.card.event.client.nameText
        link = url_for('.html_pregnancy_chart', event_id=self.card.event.id)
        tag = u'<a href="{0}">{1}</a>'.format(link, patient_name)
        card_number = self.card.event.externalId

        text = self.msg_template.format(
            p_link=tag, card_number=card_number, new_risk=self.new_risk.name
        )
        subject = u'Изменение степени риска пациентки на более высокую'
        return {
            'text': text,
            'subject': subject
        }

    def get_recipients(self):
        recipients = []
        exec_person = self.card.event.execPerson
        recipients.append(exec_person.id)

        curators = db.session.query(Person.id).join(
            PersonCurationAssoc,
            rbOrgCurationLevel,
            OrganisationCurationAssoc,
            Organisation
        ).filter(
            rbOrgCurationLevel.code.in_(('1', '2', '3')),
            Organisation.id == exec_person.org_id
        ).all()
        recipients.extend([cur[0] for cur in curators])

        return list(set(recipients))

    def get_err_msg(self):
        return u'''\
Ошибка отправки уведомлений об изменении степени
риска в карте с id = {0}
'''.format(self.card_id)

    def __repr__(self):
        return u'{0} for card_id = {1}'.format(self.__class__.__name__, self.card_id)


class PregContInabilityEvent(NotificationEvent):

    msg_template = u"""\
Пациентке {p_link} (карта {card_number})
на последнем осмотре поставили невозможность сохранения беременности.<br><br>
-----<br>
Это письмо было сгенерировано автоматически
"""

    def __init__(self, card, action):
        self.card = card
        self.card_id = card.event.id
        self.action = action
        self.action_id = action.id

    def make_message(self):
        patient_name = self.card.event.client.nameText
        link = url_for('.html_pregnancy_chart', event_id=self.card.event.id)
        tag = u'<a href="{0}">{1}</a>'.format(link, patient_name)
        card_number = self.card.event.externalId

        text = self.msg_template.format(
            p_link=tag, card_number=card_number
        )
        subject = u'Указана невозможность сохранения беременности для пациентки'
        return {
            'text': text,
            'subject': subject
        }

    def get_recipients(self):
        recipients = []
        exec_person = self.card.event.execPerson

        curators = db.session.query(Person.id).join(
            PersonCurationAssoc,
            rbOrgCurationLevel,
            OrganisationCurationAssoc,
            Organisation
        ).filter(
            rbOrgCurationLevel.code.in_(('1', '2')),
            Organisation.id == exec_person.org_id
        ).all()
        recipients.extend([cur[0] for cur in curators])

        return list(set(recipients))

    def get_err_msg(self):
        return u'''\
Ошибка отправки уведомлений о невозможности сохранения
беременности после осмотра с id = {0} для карты с id = {1}
'''.format(self.action_id, self.card_id)

    def __repr__(self):
        return u'{0} for card_id = {1}, checkup_id = {2}'.format(
            self.__class__.__name__, self.card_id, self.action_id
        )