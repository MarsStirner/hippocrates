#! coding:utf-8
"""


@author: BARS Group
@date: 13.05.2016

"""
from sqlalchemy import Column, Integer, String, Text, Index, Enum
from nemesis.systemwide import db


class rbRisarPrintTemplateMeta(db.Model):
    __tablename__ = 'rbRisarPrintTemplateMeta'
    __table_args__ = (
        Index('template_uri_name', 'template_uri', 'name'),
    )

    id = Column(Integer, primary_key=True)
    template_uri = Column(String, nullable=False)
    type = Column(Enum(
        u'Integer', u'Float', u'String', u'Boolean', u'Date', u'Time',
        u'List', u'Multilist',
        u'RefBook', u'Organisation', u'OrgStructure', u'Person', u'Service', u'SpecialVariable'
    ), nullable=False)
    name = Column(String(128), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    arguments = Column(String)
    defaultValue = Column(Text)

    def __json__(self):
        import json
        if self.arguments:
            try:
                args = json.loads(self.arguments)
            except ValueError:
                args = []
        else:
            args = []
        if self.defaultValue:
            try:
                default = json.loads(self.defaultValue)
            except ValueError:
                default = None
        else:
            default = None
        return {
            'name': self.name,
            'type': self.type,
            'title': self.title,
            'descr': self.description,
            'arguments': args,
            'default': default,
        }
