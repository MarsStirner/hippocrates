# -*- coding: utf-8 -*-
import datetime

from hippocrates.blueprints.risar.models.vesta_props import VestaProperty
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
