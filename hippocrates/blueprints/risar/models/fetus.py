#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 25.03.2016

"""
import datetime

from blueprints.risar.models.vesta_props import VestaProperty
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


class RisarFetusState(db.Model):
    __tablename__ = u'RisarFetusState'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), index=True)
    action = db.relationship('Action')

    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    position_code = db.Column(db.String(250))
    position_2_code = db.Column(db.String(250))
    type_code = db.Column(db.String(250))
    presenting_part_code = db.Column(db.String(250))
    delay_code = db.Column(db.String(250))
    basal_code = db.Column(db.String(250))
    variability_range_code = db.Column(db.String(250))
    frequency_per_minute_code = db.Column(db.String(250))
    acceleration_code = db.Column(db.String(250))
    deceleration_code = db.Column(db.String(250))

    position = VestaProperty('position_code', 'rbRisarFetus_Position')
    position_2 = VestaProperty('position_2_code', 'rbRisarFetus_Position_2')
    type = VestaProperty('type_code', 'rbRisarFetus_Type')
    presenting_part = VestaProperty('presenting_part_code', 'rbRisarPresenting_Part')
    delay = VestaProperty('delay_code', 'rbRisarFetus_Delay')
    basal = VestaProperty('basal_code', 'rbRisarBasal')
    variability_range = VestaProperty('variability_range_code', 'rbRisarVariabilityRange')
    frequency_per_minute = VestaProperty('frequency_per_minute_code', 'rbRisarFrequencyPerMinute')
    acceleration = VestaProperty('acceleration_code', 'rbRisarAcceleration')
    deceleration = VestaProperty('deceleration_code', 'rbRisarDeceleration')

    heart_rate = db.Column(db.Integer, nullable=True)
    ktg_input = db.Column(db.Boolean, nullable=False, server_default=u"'0'", default=0)
    fisher_ktg_points = db.Column(db.Integer)
    fisher_ktg_rate_id = db.Column(db.ForeignKey('rbFisherKTGRate.id'))

    fisher_ktg_rate = db.relationship('rbFisherKTGRate')

    @property
    def heartbeat(self):
        q = RisarFetusState_heartbeats.query.filter(
            RisarFetusState_heartbeats.fetus_state == self,
        )
        return map(lambda x: x.heartbeat, list(q))

    @heartbeat.setter
    def heartbeat(self, values):
        RisarFetusState_heartbeats.query.filter(
            RisarFetusState_heartbeats.fetus_state_id == self.id,
            RisarFetusState_heartbeats.fetus_state == self,
        ).delete()
        for v in values:
            obj = RisarFetusState_heartbeats(fetus_state=self)
            obj.heartbeat = v
            db.session.add(obj)


class RisarFetusState_heartbeats(db.Model):
    __tablename__ = u'RisarFetusState_heartbeats'

    id = db.Column(db.Integer, primary_key=True)
    fetus_state_id = db.Column(db.ForeignKey('RisarFetusState.id'), index=True)
    fetus_state = db.relationship('RisarFetusState')
    heartbeat_code = db.Column(db.String(250))
    heartbeat = VestaProperty('heartbeat_code', 'rbRisarFetus_Heartbeat')
