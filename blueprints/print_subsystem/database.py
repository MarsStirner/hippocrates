# -*- coding: utf-8 -*-
import sqlalchemy
import sqlalchemy.orm.session
from sqlalchemy.ext.declarative import declarative_base

__author__ = 'viruzzz-kun'


db = sqlalchemy.create_engine('mysql://tmis:q1w2e3r4t5@10.1.2.11/hospital1?charset=utf8')
session_maker = sqlalchemy.orm.session.sessionmaker(bind=db)

Base = declarative_base()
metadata = Base.metadata
