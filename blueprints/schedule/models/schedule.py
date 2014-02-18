# -*- coding: utf-8 -*-
from sqlalchemy.sql.elements import False_
from application.database import db
from exists import Person, Client, rbReasonOfAbsence, Organisation


class rbReceptionType(db.Model):
    __tablename__ = 'rbReceptionType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class rbAttendanceType(db.Model):
    __tablename__ = 'rbAttendanceType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class rbAppointmentType(db.Model):
    __tablename__ = 'rbAppointmentType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class Schedule(db.Model):
    __tablename__ = 'Schedule'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    begTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    numTickets = db.Column(db.Integer, doc=u'Запланированное количество талонов на данный день')
    office = db.Column(db.Unicode(64))
    reasonOfAbsence_id = db.Column(db.Integer, db.ForeignKey('rbReasonOfAbsence.id'))
    receptionType_id = db.Column(db.Integer, db.ForeignKey('rbReceptionType.id'))
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    person = db.relationship('Person', foreign_keys=person_id)
    reasonOfAbsence = db.relationship('rbReasonOfAbsence')
    receptionType = db.relationship('rbReceptionType')
    

class ScheduleTicket(db.Model):
    __tablename__ = 'ScheduleTicket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('Schedule.id'), nullable=False)
    begDateTime = db.Column(db.DateTime)
    endDateTime = db.Column(db.DateTime)
    attendanceType_id = db.Column(db.Integer, db.ForeignKey('rbAttendanceType.id'), nullable=False)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    schedule = db.relationship('Schedule', backref='tickets')
    attendanceType = db.relationship('rbAttendanceType')

    @property
    def client(self):
        ct = self.client_tickets.filter(ScheduleClientTicket.deleted == 0).first()
        return ct.client if ct else None

class ScheduleClientTicket(db.Model):
    __tablename__ = 'ScheduleClientTicket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ScheduleTicket.id'), nullable=False)
    isUrgent = db.Column(db.Boolean)
    note = db.Column(db.Unicode(256))
    appointmentType_id = db.Column(db.Integer, db.ForeignKey('rbAppointmentType.id'))
    orgFrom_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'))
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')
    
    client = db.relationship('Client', backref=db.backref('appointments', lazy='dynamic'))
    appointmentType = db.relationship('rbAppointmentType')
    orgFrom = db.relationship('Organisation')
    ticket = db.relationship('ScheduleTicket', backref=db.backref('client_tickets', lazy='dynamic'))
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])
