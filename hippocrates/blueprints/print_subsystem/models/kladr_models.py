# -*- coding: utf-8 -*-
from sqlalchemy import Index, Unicode, String, Integer
from sqlalchemy import Column
from ..database import Base
from ..config import MODULE_NAME


TABLE_PREFIX = MODULE_NAME


class Kladr(Base):
    __bind_key__ = 'kladr'
    __tablename__ = 'KLADR'
    __table_args__ = (
        Index('long_name', 'prefix', 'NAME', 'SOCR', 'STATUS'),
        Index('NAME', 'NAME', 'SOCR'),
        Index('parent', 'parent', 'NAME', 'SOCR', 'CODE')
    )

    NAME = Column(Unicode(40), nullable=False)
    SOCR = Column(Unicode(10), nullable=False)
    CODE = Column(String(13), primary_key=True)
    INDEX = Column(String(6), nullable=False)
    GNINMB = Column(String(4), nullable=False)
    UNO = Column(String(4), nullable=False)
    OCATD = Column(String(11), nullable=False, index=True)
    STATUS = Column(String(1), nullable=False)
    parent = Column(String(13), nullable=False)
    infis = Column(String(5), nullable=False, index=True)
    prefix = Column(String(2), nullable=False)
    id = Column(Integer, nullable=False, unique=True)


class Street(Base):
    __bind_key__ = 'kladr'
    __tablename__ = 'STREET'
    __table_args__ = (
        Index('NAME_SOCR', 'NAME', 'SOCR', 'CODE'),
    )

    NAME = Column(Unicode(40), nullable=False)
    SOCR = Column(Unicode(10), nullable=False)
    CODE = Column(String(17), primary_key=True)
    INDEX = Column(String(6), nullable=False)
    GNINMB = Column(String(4), nullable=False)
    UNO = Column(String(4), nullable=False)
    OCATD = Column(String(11), nullable=False)
    infis = Column(String(5), nullable=False, index=True)