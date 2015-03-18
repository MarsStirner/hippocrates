# -*- coding: utf-8 -*-
import datetime
from flask import g
from sqlalchemy import Column, Unicode, ForeignKey, Date, Time, DateTime, SmallInteger, Boolean
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from ..database import Base

from models_all import Person, Client, Rbreasonofabsence, Organisation, Orgstructure


class rbReceptionType(Base):
    __tablename__ = 'rbReceptionType'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Unicode(32), nullable=False)
    name = Column(Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }


class rbAttendanceType(Base):
    __tablename__ = 'rbAttendanceType'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Unicode(32), nullable=False)
    name = Column(Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }


class Office(Base):
    __tablename__ = 'Office'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Unicode(32), nullable=False)
    name = Column(Unicode(64), nullable=False)
    orgStructure_id = Column(ForeignKey('OrgStructure.id'))

    orgStructure = relationship('Orgstructure')

    def __unicode__(self):
        return self.code

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
            'org_structure': self.orgStructure
        }


class rbAppointmentType(Base):
    __tablename__ = 'rbAppointmentType'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Unicode(32), nullable=False)
    name = Column(Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }


class Schedule(Base):
    __tablename__ = 'Schedule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('Person.id'), nullable=False)
    date = Column(Date, nullable=False)
    begTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    numTickets = Column(Integer, doc=u'Запланированное количество талонов на данный день')
    office_id = Column(ForeignKey('Office.id'))
    reasonOfAbsence_id = Column(Integer, ForeignKey('rbReasonOfAbsence.id'))
    receptionType_id = Column(Integer, ForeignKey('rbReceptionType.id'))
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    deleted = Column(SmallInteger, nullable=False, server_default='0')

    person = relationship('Person', foreign_keys=person_id)
    reasonOfAbsence = relationship('Rbreasonofabsence', lazy='joined')
    receptionType = relationship('rbReceptionType', lazy='joined')
    tickets = relationship(
        'ScheduleTicket', lazy=False, primaryjoin=
        "and_(ScheduleTicket.schedule_id == Schedule.id, ScheduleTicket.deleted == 0)")
    office = relationship('Office', lazy='joined')
    

class ScheduleTicket(Base):
    __tablename__ = 'ScheduleTicket'

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey('Schedule.id'), nullable=False)
    begTime = Column(Time)
    endTime = Column(Time)
    attendanceType_id = Column(Integer, ForeignKey('rbAttendanceType.id'), nullable=False)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    deleted = Column(SmallInteger, nullable=False, server_default='0')

    attendanceType = relationship('rbAttendanceType', lazy=False)
    client_ticket = relationship(
        'ScheduleClientTicket', lazy=False, primaryjoin=
        "and_(ScheduleClientTicket.ticket_id == ScheduleTicket.id, ScheduleClientTicket.deleted == 0)",
        uselist=False)

    schedule = relationship(
        'Schedule', lazy="joined", innerjoin=True, uselist=False,
        primaryjoin='and_('
                    'Schedule.deleted == 0, ScheduleTicket.deleted == 0, ScheduleTicket.schedule_id == Schedule.id)'
    )

    @property
    def client(self):
        ct = self.client_ticket
        return ct.client if ct else None

    @property
    def begDateTime(self):
        return datetime.datetime.combine(self.schedule.date, self.begTime) if self.begTime is not None else None

    @property
    def endDateTime(self):
        return datetime.datetime.combine(self.schedule.date, self.endTime) if self.endTime is not None else None


class ScheduleClientTicket(Base):
    __tablename__ = 'ScheduleClientTicket'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('Client.id'), nullable=False)
    ticket_id = Column(Integer, ForeignKey('ScheduleTicket.id'), nullable=False)
    isUrgent = Column(Boolean)
    note = Column(Unicode(256))
    appointmentType_id = Column(Integer, ForeignKey('rbAppointmentType.id'))
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    deleted = Column(SmallInteger, nullable=False, server_default='0')
    event_id = Column(ForeignKey('Event.id'))
    
    client = relationship('Client', lazy='joined', uselist=False)
    appointmentType = relationship('rbAppointmentType', lazy=False, innerjoin=True)
    createPerson = relationship('Person', foreign_keys=[createPerson_id])
    event = relationship('Event')

    ticket = relationship(
        'ScheduleTicket', lazy="joined", innerjoin=True, uselist=False,
        primaryjoin='and_('
                    'ScheduleClientTicket.deleted == 0, '
                    'ScheduleTicket.deleted == 0, '
                    'ScheduleClientTicket.ticket_id == ScheduleTicket.id)'
    )


    @property
    def org_from(self):
        if not self.infisFrom:
            return
        from models_all import Organisation
        org = g.printing_session.query(Organisation).filter(Organisation.infisCode == self.infisFrom).first()
        if not org:
            return self.infisFrom
        return org.title

    @property
    def date(self):
        return self.ticket.schedule.date

    @property
    def time(self):
        attendance_type_code = self.ticket.attendanceType.code
        if attendance_type_code == 'planned':
            time = self.ticket.begDateTime.time()
        elif attendance_type_code == 'CITO':
            time = "CITO"
        elif attendance_type_code == 'extra':
            time = u"сверх очереди"
        else:
            time = '--:--'

        return time

    @property
    def typeText(self):
        toHome = self.ticket.schedule.receptionType.code == 'home'
        if toHome:
            typeText = u'Вызов на дом'
        else:
            typeText = u'Направление на приём к врачу'
        return typeText