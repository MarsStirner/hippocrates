# -*- coding: utf-8 -*-
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache

db = SQLAlchemy()

cache = Cache(config={'CACHE_TYPE': 'simple'})
