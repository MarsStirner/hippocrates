# -*- coding: utf-8 -*-
import datetime
import json
import uuid
from decimal import Decimal
from flask import g, current_app, request
from flask.ext.principal import Permission, RoleNeed, ActionNeed
from application.database import db
from application.models.exists import rbUserProfile, UUID, rbCounter, EventType, ClientIdentification, \
    rbAccountingSystem
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


class Bunch:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


with app.app_context():
    _roles = dict()
    _permissions = dict()
    user_roles = db.session.query(rbUserProfile).all()
    if user_roles:
        for role in user_roles:
            _roles[role.code] = Permission(RoleNeed(role.code))
            # _roles[role.code].name = role.name
            for right in getattr(role, 'rights', []):
                if right.code not in _permissions:
                    _permissions[right.code] = Permission(ActionNeed(right.code))
                    # _permissions[right.code].name = right.name
    roles = Bunch(**_roles)
    permissions = Bunch(**_permissions)

# инициализация логгера
from config import DEBUG, PROJECT_NAME, SIMPLELOGS_URL
from version import version
logger = SimpleLogger.get_logger(SIMPLELOGS_URL,
                                 PROJECT_NAME,
                                 dict(name=PROJECT_NAME, version=version),
                                 DEBUG)


class WebMisJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return o.isoformat()
        elif isinstance(o, Decimal):
            return float(o)
        elif hasattr(o, '__json__'):
            return o.__json__()
        elif isinstance(o, db.Model) and hasattr(o, '__unicode__'):
            return unicode(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = WebMisJsonEncoder


def jsonify(obj, result_code=200, result_name='OK'):
    """Creates a :class:`~flask.Response` with the JSON representation of
    the given arguments with an `application/json` mimetype.  The arguments
    to this function are the same as to the :class:`dict` constructor.

    Example usage::

        from flask import jsonify

        @app.route('/_get_current_user')
        def get_current_user():
            return jsonify(username=g.user.username,
                           email=g.user.email,
                           id=g.user.id)

    This will send a JSON response like this to the browser::

        {
            "username": "admin",
            "email": "admin@localhost",
            "id": 42
        }

    For security reasons only objects are supported toplevel.  For more
    information about this, have a look at :ref:`json-security`.

    This function's response will be pretty printed if it was not requested
    with ``X-Requested-With: XMLHttpRequest`` to simplify debugging unless
    the ``JSONIFY_PRETTYPRINT_REGULAR`` config parameter is set to false.

    .. versionadded:: 0.2
    """
    indent = None
    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
    return (
        json.dumps({
            'result': obj,
            'meta': {
                'code': result_code,
                'name': result_name,
            }
        }, indent=indent, cls=WebMisJsonEncoder, encoding='utf-8', ensure_ascii=False),
        200,
        [('content-type', 'application/json; charset=utf-8'),
         ('Expires', 'Thu, 20 Mar 2014 23:59:58 GMT'),
            ('Cache-Control', 'max-age=43200')
        ]
    )


def safe_unicode(obj):
    if obj is None:
        return None
    return unicode(obj)


def safe_int(obj):
    if obj is None:
        return None
    return int(obj)


def safe_traverse(obj, *args, **kwargs):
    """Безопасное копание вглубь dict'а
    @param obj: точка входя для копания
    @param *args: ключи, по которым надо проходить
    @param default=None: возвращаемое значение, если раскопки не удались
    @rtype: any
    """
    default = kwargs.get('default', None)
    if obj is None:
        return default
    if len(args) == 0:
        raise ValueError(u'len(args) must be > 0')
    elif len(args) == 1:
        return obj.get(args[0], default)
    else:
        return safe_traverse(obj.get(args[0]), *args[1:], **kwargs)


def get_new_uuid():
    """Сгенерировать новый uuid уникальный в пределах бд.
    @rtype: application.models.exist.UUID
    """
    uuid_model = UUID()
    # paranoia mode on
    unique = False
    while not unique:
        new_uuid = str(uuid.uuid4())
        unique = uuid_model.query.filter_by(uuid=new_uuid).count() == 0
    uuid_model.uuid = new_uuid

    return uuid_model


def get_new_event_ext_id(event_type_id, client_id):
    """Формирование externalId (номер обращения/истории болезни)."""
    et = EventType.query.get(event_type_id)
    if not et.counter_id:
        return ''

    counter = rbCounter.query.filter_by(id=et.counter_id).with_for_update().first()
    # todo: check for update
    if not counter:
        return ''
    external_id = _get_external_id_from_counter(counter.prefix,
                                                counter.value + 1,
                                                counter.separator,
                                                client_id)
    counter.value += 1
    db.session.add(counter)
    return external_id


def _get_external_id_from_counter(prefix, value, separator, client_id):
    def get_date_prefix(val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in [0, 2, 4] or val.count('M') > 2 or val.count('d') > 2:
            return None
        # qt -> python date format
        _map = {'yyyy': '%Y', 'yy': '%y', 'mm': '%m', 'dd': '%d'}
        try:
            format_ = _map.get(val, '%Y')
            date_val = datetime.date.today().strftime(format_)
            check = datetime.datetime.strptime(date_val, format_)
        except ValueError, e:
            print e
            return None
        return date_val

    def get_id_prefix(val):
        if val == '':
            return str(client_id)
        ext_val = ClientIdentification.query.join(rbAccountingSystem).filter(
            ClientIdentification.client_id == client_id, rbAccountingSystem.code == val).first()
        return ext_val.identifier if ext_val else None

    prefix_types = {'date': get_date_prefix, 'id': get_id_prefix}

    prefix_parts = prefix.split(';')
    prefix = []
    for p in prefix_parts:
        for t in prefix_types:
            pos = p.find(t)
            if pos == 0:
                val = p[len(t):]
                if val.startswith('(') and val.endswith(')'):
                    val = prefix_types[t](val[1:-1])
                    if val:
                        prefix.append(val)
    return separator.join(prefix + ['%d' % value])