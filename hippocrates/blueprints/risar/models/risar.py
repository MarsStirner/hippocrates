# -*- coding: utf-8 -*-
import datetime

from blueprints.risar.models.vesta_props import VestaProperty
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class RisarRiskGroup(db.Model):
    __tablename__ = 'RisarRiskGroup'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    event_id = db.Column(db.ForeignKey('Event.id'))
    riskGroup_code = db.Column(db.String(250), index=True)

    event = db.relationship('Event', backref=db.backref(
        'risk_groups', primaryjoin='Event.id == RisarRiskGroup.event_id and RisarRiskGroup.deleted == 0'
    ))
    risk_group = VestaProperty('riskGroup_code', 'rbRisarRiskGroup')

