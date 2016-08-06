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
