# -*- encoding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from nemesis.utils import create_config_func
from .models import ConfigVariables
from .config import MODULE_NAME, LPU_DB_CONNECT_STRING

_config = create_config_func(MODULE_NAME, ConfigVariables)


def get_lpu_session():
    Session = None
    try:
        engine = create_engine(LPU_DB_CONNECT_STRING, convert_unicode=True, pool_recycle=600)
        Session = scoped_session(sessionmaker(bind=engine))
    except Exception, e:
        print e

    if Session is None:
        raise AttributeError(u'Не настроено подключение к БД ЛПУ')
    return Session()