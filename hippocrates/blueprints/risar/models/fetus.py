#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 25.03.2016

"""
import datetime

from blueprints.risar.models.vesta_props import VestaProperty
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


class FetusState(db.Model):
    __tablename__ = u'FetusState'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), index=True)
    action = db.relationship('Action')

    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    position_code = db.Column(db.String(250), index=True)
    position_2_code = db.Column(db.String(250), index=True)
    type_code = db.Column(db.String(250), index=True)
    presenting_part_code = db.Column(db.String(250), index=True)
    heartbeat_code = db.Column(db.String(250), index=True)
    delay_code = db.Column(db.String(250), index=True)
    basal_code = db.Column(db.String(250), index=True)
    variability_range_code = db.Column(db.String(250), index=True)
    frequency_per_minute_code = db.Column(db.String(250), index=True)
    acceleration_code = db.Column(db.String(250), index=True)
    deceleration_code = db.Column(db.String(250), index=True)

    position = VestaProperty('position_code', 'rbRisarFetus_Position')
    position_2 = VestaProperty('position_2_code', 'rbRisarFetus_Position_2')
    type = VestaProperty('type_code', 'rbRisarFetus_Type')
    presenting_part = VestaProperty('presenting_part_code', 'rbRisarPresenting_Part')
    heartbeat = VestaProperty('heartbeat_code', 'rbRisarFetus_Heartbeat')
    delay = VestaProperty('delay_code', 'rbRisarFetus_Delay')
    basal = VestaProperty('basal_code', 'rbRisarBasal')
    variability_range = VestaProperty('variability_range_code', 'rbRisarVariabilityRange')
    frequency_per_minute = VestaProperty('frequency_per_minute_code', 'rbRisarFrequencyPerMinute')
    acceleration = VestaProperty('acceleration_code', 'rbRisarAcceleration')
    deceleration = VestaProperty('deceleration_code', 'rbRisarDeceleration')

    heart_rate = db.Column(db.Integer, nullable=True)
    ktg_input = db.Column(db.Boolean, nullable=False, server_default=u"'0'", default=0)
