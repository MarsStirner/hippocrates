# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
PROFILE = False
PROJECT_NAME = 'Hippocrates'

# DB connecting params
DB_DRIVER = 'mysql'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'db_user'
DB_PASSWORD = 'db_password'
DB_NAME = 'db_name'
DB_CONNECT_OPTIONS = ''

DB_CAESAR_NAME = 'caesar'
DB_KLADR_NAME = 'kladr'
DB_LPU_NAME = 'lpu_db_name'

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

SYSTEM_USER = 'hippo'

WTF_CSRF_ENABLED = True
SECRET_KEY = ''

BLUEPRINTS_DIR = 'blueprints'

BABEL_DEFAULT_LOCALE = 'ru_RU'

BEAKER_SESSION = {'session.type': 'file',
                  'session.data_dir': '/tmp/session/data',
                  'session.lock_dir': '/tmp/session/lock',
                  'session.key': '{0}.session.id'.format(os.path.basename(os.path.dirname(__file__)))}

TIME_ZONE = 'Europe/Moscow'

SIMPLELOGS_URL = 'http://127.0.0.1:8080'

SEARCHD_CONNECTION = {
    'host': '127.0.0.1',
    'port': 9306,
}

ORGANISATION_INFIS_CODE = 500
RISAR_REGIONS = []
PRINT_SUBSYSTEM_URL = ''
VESTA_URL = ''
TRFU_URL = ''
WEBMIS10_URL = ''
COLDSTAR_URL = ''
SIMARGL_URL = ''
CASTIEL_AUTH_TOKEN = 'CastielAuthToken'

TITLE = u'WebMIS 2.0'
COPYRIGHT_COMPANY = u'КОРУС Консалтинг ИТ'
LPU_STYLE = ''  #'FNKC'

INDEX_HTML = 'hippo_index.html'
SCANSERVER_URL = ''
FILE_STORAGE_PATH = ''

try:
    from config_local import *
except ImportError:
    print('no local config')
    # no local config found
    pass

db_uri_format = '{0}://{1}:{2}@{3}:{4}/{5}{6}'

SQLALCHEMY_DATABASE_URI = db_uri_format.format(DB_DRIVER,
                                                       DB_USER,
                                                       DB_PASSWORD,
                                                       DB_HOST,
                                                       DB_PORT,
                                                       DB_NAME,
                                                       DB_CONNECT_OPTIONS)

SQLALCHEMY_BINDS = {
    'kladr':        db_uri_format.format(DB_DRIVER,
                                                       DB_USER,
                                                       DB_PASSWORD,
                                                       DB_HOST,
                                                       DB_PORT,
                                                       DB_CAESAR_NAME,
                                                       DB_CONNECT_OPTIONS)
}
