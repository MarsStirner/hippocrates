# -*- coding: utf-8 -*-
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class UserMail(db.Model):
    __tablename__ = "UserMail"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.ForeignKey('Person.id'), nullable=True)
    recipient_id = db.Column(db.ForeignKey('Person.id'), nullable=True)
    subject = db.Column(db.String(256), nullable=False)
    text = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    read = db.Column(db.Integer, nullable=False)

    sender = db.relationship('Person', foreign_keys=[sender_id])
    recipient = db.relationship('Person', foreign_keys=[recipient_id])

    def __json__(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'text': self.text,
            'datetime': self.datetime,
            'read': bool(self.read),
        }
