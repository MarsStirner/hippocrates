# -*- coding: utf-8 -*-
from application.systemwide import db
from config import MODULE_NAME

TABLE_PREFIX = MODULE_NAME


class ConfigVariables(db.Model):
    __tablename__ = '%s_config' % TABLE_PREFIX

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(25), unique=True, nullable=False)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)
    value = db.Column(db.Unicode(100))
    value_type = db.Column(db.String(30))

    def __unicode__(self):
        return self.code