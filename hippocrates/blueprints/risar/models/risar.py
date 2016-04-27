# -*- coding: utf-8 -*-
import datetime

from sqlalchemy.dialects.mysql import LONGTEXT

from blueprints.risar.models.vesta_props import VestaProperty
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class RisarRiskGroup(db.Model):
    __tablename__ = 'RisarRiskGroup'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    event_id = db.Column(db.ForeignKey('Event.id'))
    riskGroup_code = db.Column(db.String(250), index=True)

    event = db.relationship('Event', backref=db.backref(
        'risk_groups', primaryjoin='and_(Event.id == RisarRiskGroup.event_id, RisarRiskGroup.deleted == 0)'
    ))
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])
    risk_group = VestaProperty('riskGroup_code', 'rbRisarRiskGroup')

    def __json__(self):
        return {
            'id': self.id,
            'create_datetime': self.createDatetime,
            'modify_datetime': self.modifyDatetime,
            'create_person': self.createPerson,
            'modify_person': self.modifyPerson,
            'risk_group': self.risk_group,
        }


class RisarPreviousPregnancy_Children(db.Model):
    __tablename__ = 'RisarPreviousPregnancy_Children'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    sex = db.Column(db.Integer)
    weight = db.Column(db.Float)
    length = db.Column(db.Float)
    maturity_rate_code = db.Column(db.String(250))
    apgar_score_1 = db.Column(db.Integer)
    apgar_score_5 = db.Column(db.Integer)
    apgar_score_10 = db.Column(db.Integer)
    alive = db.Column(db.Integer)
    death_reason = db.Column(db.String(50))
    died_at_code = db.Column(db.String(250))
    abnormal_development = db.Column(db.Integer)
    neurological_disorders = db.Column(db.Integer)

    action = db.relationship('Action')
    maturity_rate = VestaProperty('maturity_rate_code', 'rbRisarMaturity_Rate')
    died_at = VestaProperty('died_at_code', 'rbRisarDiedAt')

    def __json__(self):
        return {
            'id': self.id,
        }


class RisarEpicrisis_Children(db.Model):
    __tablename__ = 'RisarEpicrisis_Children'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    sex = db.Column(db.Integer)
    weight = db.Column(db.Float)
    length = db.Column(db.Float)
    maturity_rate_code = db.Column(db.String(250))
    apgar_score_1 = db.Column(db.Integer)
    apgar_score_5 = db.Column(db.Integer)
    apgar_score_10 = db.Column(db.Integer)
    alive = db.Column(db.Integer)
    death_reason = db.Column(db.String(50))
    action = db.relationship('Action')
    maturity_rate = VestaProperty('maturity_rate_code', 'rbRisarMaturity_Rate')

    def __json__(self):
        return {
            'id': self.id,
        }

    @property
    def diseases(self):
        q = RisarEpicrisis_Children_diseases.query.filter(
            RisarEpicrisis_Children_diseases.newborn == self,
        )
        return map(lambda x: x.mkb, list(q))

    @diseases.setter
    def diseases(self, values):
        RisarEpicrisis_Children_diseases.query.filter(
            RisarEpicrisis_Children_diseases.newborn_id == self.id,
            RisarEpicrisis_Children_diseases.newborn == self,
        ).delete()
        for v in values:
            obj = RisarEpicrisis_Children_diseases(newborn=self)
            obj.mkb_id = v['id']
            db.session.add(obj)


class RisarEpicrisis_Children_diseases(db.Model):
    __tablename__ = u'RisarEpicrisis_Children_diseases'

    id = db.Column(db.Integer, primary_key=True)
    newborn_id = db.Column(db.ForeignKey('RisarEpicrisis_Children.id'), index=True)
    newborn = db.relationship('RisarEpicrisis_Children')
    mkb_id = db.Column(db.Integer, db.ForeignKey('MKB.id'), nullable=False)
    mkb = db.relationship('MKB')


class ActionIdentification(db.Model):
    __tablename__ = 'ActionIdentification'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), index=True)
    action = db.relationship('Action')
    external_id = db.Column(db.String(250), index=True)
    external_system_id = db.Column(db.Integer, db.ForeignKey('rbAccountingSystem.id'), nullable=False)
    external_system = db.relationship(u'rbAccountingSystem')


class RisarConcilium(db.Model):
    __tablename__ = 'RisarConcilium'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hospital_id = db.Column(db.ForeignKey('Organisation.id'), nullable=False)
    doctor_id = db.Column(db.ForeignKey('Person.id'), nullable=False)
    patient_presence = db.Column(db.SmallInteger)
    mkb_id = db.Column(db.ForeignKey('MKB.id'), nullable=False)
    reason = db.Column(db.String(1024), nullable=False, server_default="''")
    patient_condition = db.Column(LONGTEXT)
    decision = db.Column(LONGTEXT, nullable=False)

    event = db.relationship('Event')
    hospital = db.relationship('Organisation')
    doctor = db.relationship('Person')
    mkb = db.relationship('MKB')
    members = db.relationship('RisarConcilium_Members', backref='concilium')


class RisarConcilium_Members(db.Model):
    __tablename__ = 'RisarConcilium_Members'

    id = db.Column(db.Integer, primary_key=True)
    concilium_id = db.Column(db.ForeignKey('RisarConcilium.id'), nullable=False)
    person_id = db.Column(db.ForeignKey('Person.id'), nullable=False)
    opinion = db.Column(LONGTEXT)

    person = db.relationship('Person')


class RisarConcilium_Identification(db.Model):
    __tablename__ = 'RisarConcilium_Identification'

    id = db.Column(db.Integer, primary_key=True)
    concilium_id = db.Column(db.ForeignKey('RisarConcilium.id'), nullable=False)
    external_id = db.Column(db.String(250), nullable=False)
    external_system_id = db.Column(db.ForeignKey('rbAccountingSystem.id'), nullable=False)

    concilium = db.relationship('RisarConcilium')
    external_system = db.relationship(u'rbAccountingSystem')