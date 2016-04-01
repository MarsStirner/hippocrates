# -*- coding: utf-8 -*-
import datetime
import json

from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class ActionAutoSave(db.Model):
    __tablename__ = 'ActionAutoSave'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False)
    user_id = db.Column(db.ForeignKey('Person.id'), nullable=False, default=safe_current_user_id)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    data_ = db.Column('data', db.Text, nullable=False)

    action = db.relationship('Action')
    user = db.relationship('Person')

    @property
    def data(self):
        try:
            return json.loads(self.data_)
        except (ValueError, TypeError):
            return None

    @data.setter
    def data(self, value):
        self.data_ = json.dumps(value)


class ActionAutoSaveUnsaved(db.Model):
    __tablename__ = 'ActionAutoSaveUnsaved'

    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    user_id = db.Column(db.ForeignKey('Person.id'), nullable=False, default=safe_current_user_id)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    data_ = db.Column('data', db.Text, nullable=False)

    action_type = db.relationship('ActionType')
    event = db.relationship('Event')
    user = db.relationship('Person')

    @property
    def data(self):
        try:
            return json.loads(self.data_)
        except (ValueError, TypeError):
            return None

    @data.setter
    def data(self, value):
        self.data_ = json.dumps(value)
