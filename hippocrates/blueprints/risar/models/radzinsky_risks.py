# -*- coding: utf-8 -*-
import datetime

from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


class RisarRadzinskyRisks(db.Model):
    __tablename__ = 'RisarRadzinskyRisks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id, onupdate=safe_current_user_id)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    anamnestic_points = db.Column(db.Integer)
    before32week_points = db.Column(db.Integer)
    after33week_points = db.Column(db.Integer)
    intranatal_points = db.Column(db.Integer)
    before32week_totalpoints = db.Column(db.Integer)
    after33week_totalpoints = db.Column(db.Integer)
    intranatal_totalpoints = db.Column(db.Integer)
    intranatal_growth = db.Column(db.Float(asdecimal=True))
    risk_rate_id = db.Column(db.ForeignKey('rbRadzinskyRiskRate.id'))

    event = db.relationship('Event')
    risk_rate = db.relationship('rbRadzinskyRiskRate')
    factors_assoc = db.relationship('RisarRadzinskyRisks_FactorsAssoc', backref='radz_risk')

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'anamnestic_points': self.anamnestic_points,
            'before32week_points': self.before32week_points,
            'after33week_points': self.after33week_points,
            'intranatal_points': self.intranatal_points,
            'before32week_totalpoints': self.before32week_totalpoints,
            'after33week_totalpoints': self.after33week_totalpoints,
            'intranatal_totalpoints': self.intranatal_totalpoints,
            'intranatal_growth': self.intranatal_growth,
            'risk_rate_id': self.risk_rate_id,
            'risk_rate': self.risk_rate
        }

    def __int__(self):
        return self.id


class RisarRadzinskyRisks_FactorsAssoc(db.Model):
    __tablename__ = u'RisarRadzinskyRisks_Factors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_id = db.Column(db.ForeignKey('RisarRadzinskyRisks.id'), nullable=False)
    risk_factor_id = db.Column(db.ForeignKey('rbRadzRiskFactor.id'), nullable=False)
    stage_id = db.Column(db.ForeignKey('rbRadzStage.id'), nullable=False)

    risk_factor = db.relationship('rbRadzRiskFactor')


class RisarRegionalRiskRate(db.Model):
    __tablename__ = 'RisarRegionalRiskRate'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    risk_rate_id = db.Column(db.ForeignKey('rbRisarRegionalRiskRate.id'))

    event = db.relationship('Event')
    risk_rate = db.relationship('rbRisarRegionalRiskRate')

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'risk_rate_id': self.risk_rate_id,
            'risk_rate': self.risk_rate
        }

    def __int__(self):
        return self.id


class RisarTomskRegionalRisks(db.Model):
    __tablename__ = 'RisarTomskRegionalRisks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id, onupdate=safe_current_user_id)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    initial_points = db.Column(db.Integer)
    before21week_points = db.Column(db.Integer)
    from21to30week_points = db.Column(db.Integer)
    from31to36week_points = db.Column(db.Integer)

    event = db.relationship('Event')
    factors_assoc = db.relationship('RisarTomskRegionalRisks_FactorsAssoc', backref='risk')

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'initial_points': self.initial_points,
            'before21week_points': self.before21week_points,
            'from21to30week_points': self.from21to30week_points,
            'from31to36week_points': self.from31to36week_points,
        }

    def __int__(self):
        return self.id


class RisarTomskRegionalRisks_FactorsAssoc(db.Model):
    __tablename__ = u'RisarTomskRegionalRisks_Factors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_id = db.Column(db.ForeignKey('RisarTomskRegionalRisks.id'), nullable=False)
    risk_factor_id = db.Column(db.ForeignKey('rbRadzRiskFactor.id'), nullable=False)
    stage_id = db.Column(db.ForeignKey('rbRegionalRiskStage.id'), nullable=False)

    risk_factor = db.relationship('rbRadzRiskFactor')


class RisarSaratovRegionalRisks(db.Model):
    __tablename__ = 'RisarSaratovRegionalRisks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), default=safe_current_user_id, onupdate=safe_current_user_id)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    anamnestic_points = db.Column(db.Integer)
    before35week_points = db.Column(db.Integer)
    after36week_points = db.Column(db.Integer)
    intranatal_points = db.Column(db.Integer)
    before35week_totalpoints = db.Column(db.Integer)
    after36week_totalpoints = db.Column(db.Integer)
    intranatal_totalpoints = db.Column(db.Integer)
    intranatal_growth = db.Column(db.Float(asdecimal=True))

    event = db.relationship('Event')
    factors_assoc = db.relationship('RisarSaratovRegionalRisks_FactorsAssoc', backref='risk')

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'anamnestic_points': self.anamnestic_points,
            'before35week_points': self.before35week_points,
            'after36week_points': self.after36week_points,
            'intranatal_points': self.intranatal_points,
            'before35week_totalpoints': self.before35week_totalpoints,
            'after36week_totalpoints': self.after36week_totalpoints,
            'intranatal_totalpoints': self.intranatal_totalpoints,
            'intranatal_growth': self.intranatal_growth,
        }

    def __int__(self):
        return self.id


class RisarSaratovRegionalRisks_FactorsAssoc(db.Model):
    __tablename__ = u'RisarSaratovRegionalRisks_Factors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_id = db.Column(db.ForeignKey('RisarSaratovRegionalRisks.id'), nullable=False)
    risk_factor_id = db.Column(db.ForeignKey('rbRadzRiskFactor.id'), nullable=False)
    stage_id = db.Column(db.ForeignKey('rbRegionalRiskStage.id'), nullable=False)

    risk_factor = db.relationship('rbRadzRiskFactor')
