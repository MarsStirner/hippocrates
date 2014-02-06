# -*- coding: utf-8 -*-
from flask import g
from flask.ext.principal import identity_loaded, Principal, Permission, RoleNeed, UserNeed
from flask.ext.login import LoginManager, current_user
from ..database import db
from ..models import Users, Roles
from application.app import app
from pysimplelogs.logger import SimpleLogger


def public_endpoint(function):
    function.is_public = True
    return function

#
# def create_config_func(module_name, config_table):
#
#     def _config(code):
#         """Возвращает значение конфигурационной переменной, полученной из таблицы %module_name%_config"""
#         #Get app_settings
#         app_settings = dict()
#         try:
#             for item in db.session.query(Settings).all():
#                 app_settings.update({item.code: item.value})
#             # app_settings = {item.code: item.value for item in db.session.query(Settings).all()}
#         except Exception, e:
#             print e
#
#         config = getattr(g, '%s_config' % module_name, None)
#         if not config:
#             values = db.session.query(config_table).all()
#             config = dict()
#             for value in values:
#                 config[value.code] = value.value
#             setattr(g, '%s_config' % module_name, config)
#         config.update(app_settings)
#         return config.get(code, None)
#
#     return _config


with app.app_context():
    permissions = dict()
    login_manager = LoginManager()
    try:
        roles = db.session.query(Roles).all()
    except Exception, e:
        print e
        permissions['admin'] = Permission(RoleNeed('admin'))
    else:
        if roles:
            for role in roles:
                permissions[role.code] = Permission(RoleNeed(role.code))
                permissions[role.code].description = role.description
        else:
            permissions['admin'] = Permission(RoleNeed('admin'))

# TODO: разобраться как покрасивше сделать
admin_permission = permissions.get('admin')
user_permission = permissions.get('user')

# инициализация логгера
from config import DEBUG, PROJECT_NAME, SIMPLELOGS_URL
from version import version
logger = SimpleLogger.get_logger(SIMPLELOGS_URL,
                                 PROJECT_NAME,
                                 dict(name=PROJECT_NAME, version=version),
                                 DEBUG)