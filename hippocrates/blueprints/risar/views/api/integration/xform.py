# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from datetime import datetime
from decimal import Decimal
from abc import ABCMeta, abstractmethod

from nemesis.lib.apiutils import ApiException
from nemesis.models.client import Client
from nemesis.models.organisation import Organisation
from nemesis.models.person import Person
from .utils import get_org_by_tfoms_code, get_person_by_code
from nemesis.lib.vesta import Vesta
from nemesis.models.exists import rbAccountingSystem
from blueprints.risar.models.risar import ActionIdentification
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date


__author__ = 'viruzzz-kun'

logger = logging.getLogger('simple')


INTERNAL_ERROR = 500
VALIDATION_ERROR = 406
NOT_FOUND_ERROR = 404
ALREADY_PRESENT_ERROR = 400
MIS_BARS_CODE = 'Mis-Bars'


def none_default(function=None, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 0 and args[-1] is None:
                if callable(default):
                    return default()
            else:
                return func(*args, **kwargs)
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


class Undefined(object):
    pass


def wrap_simplify(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return simplify(func(*args, **kwargs))
    return wrapper


def simplify(o):
    if isinstance(o, dict):
        return simplify_dict(o)
    elif isinstance(o, list):
        return simplify_list(o)
    return o


def simplify_dict(d):
    return {
        key: simplify(value)
        for key, value in d.iteritems()
        if value is not Undefined
    }


def simplify_list(l):
    return [
        item
        for item in l
        if item is not Undefined
    ]


class XForm(object):
    version = 0

    def set_version(self, version):
        for v in xrange(self.version + 1, version + 1):
            method = getattr(self, 'set_version_%i' % v, None)
            if method is None:
                raise ApiException(400, 'Version %i of API is unsupported' % (version, ))
            else:
                method()
        self.version = version

    def validate(self, data):
        if data is None:
            raise ApiException(400, 'No JSON body')
        schema = self.schema[self.version]
        cls = jsonschema.validators.validator_for(schema)
        val = cls(schema)
        errors = [{
            'error': error.message,
            'instance': error.instance,
            'path': '/' + '/'.join(map(unicode, error.absolute_path)),
        } for error in val.iter_errors(data)]
        if errors:
            logger.error(u'Ошибка валидации данных', extra={'errors': errors})
            raise ApiException(
                400,
                'Validation error',
                errors=errors,
            )

    def find_org(self, tfoms_code):
        org = get_org_by_tfoms_code(tfoms_code)
        if not org:
            raise ApiException(400, u'Не найдена организация по коду {0}'.format(tfoms_code))
        return org

    def find_doctor(self, code):
        org = get_person_by_code(code)
        if not org:
            raise ApiException(400, u'Не найден врач по коду {0}'.format(code))
        return org

    def find_client(self, client_id):
        client = Client.query.filter(Client.id == client_id).first()
        if not client:
            raise ApiException(400, u'Не найден пациент с id = {0}'.format(client_id))
        return client


class CheckupsXForm(object):
    __metaclass__ = ABCMeta
    schema = None
    parent_obj_class = None
    target_obj_class = None

    def __init__(self, api_version):
        self.version = 0
        self.new = False
        self.parent_obj_id = None
        self.target_obj_id = None
        self.parent_obj = None
        self.target_obj = None
        self.external_id = None

        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).first()

        self.set_version(api_version)

    def set_version(self, version):
        for v in xrange(self.version + 1, version + 1):
            method = getattr(self, 'set_version_%i' % v, None)
            if method is None:
                raise ApiException(
                    400, 'Version %i of API is unsupported' % (version, )
                )
            else:
                method()
        self.version = version

    def validate(self, data):
        if data is None:
            raise ApiException(400, 'No JSON body')
        schema = self.schema[self.version]
        cls = jsonschema.validators.validator_for(schema)
        val = cls(schema)
        errors = [{'error': error.message,
                   'instance': error.instance,
                   'path': '/' + '/'.join(map(unicode, error.absolute_path))}
                  for error in val.iter_errors(data)]
        if errors:
            logger.error(u'Ошибка валидации данных', extra={'errors': errors})
            raise ApiException(
                VALIDATION_ERROR,
                'Validation error',
                errors=errors,
            )

    def find_parent_obj(self, parent_obj_id):
        self.parent_obj_id = parent_obj_id
        if parent_obj_id is None:
            # Ручная валидация
            raise Exception(
                u'%s.find_parent_obj called without "parent_obj_id"' %
                self.__class__.__name__
            )
        else:
            parent_obj = self._find_parent_obj_query().first()
            if not parent_obj:
                raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                   self.parent_obj_class.__name__)
        self.parent_obj = parent_obj

    def check_parent_obj(self, parent_obj_id):
        self.parent_obj_id = parent_obj_id
        if parent_obj_id is None:
            # Ручная валидация
            raise ApiException(
                VALIDATION_ERROR,
                u'%s.find_parent_obj called without "parent_obj_id"' %
                self.__class__.__name__
            )
        else:
            q = self._find_parent_obj_query()
            parent_obj_exists = db.session.query(q.exists()).scalar()
            if not parent_obj_exists:
                raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                   self.parent_obj_class.__name__)

    def check_target_obj(self, parent_obj_id, target_obj_id, data=None):
        self.parent_obj_id = parent_obj_id
        self.target_obj_id = target_obj_id
        if target_obj_id is None:
            if not data:
                raise ApiException(
                    INTERNAL_ERROR,
                    u'%s.check_target_obj called without "data"' %
                    self.__class__.__name__
                )

            self.new = True
            self.check_parent_obj(parent_obj_id)
            self.check_duplicate(data)
        else:
            if parent_obj_id is None:
                # Ручная валидация
                raise ApiException(
                    VALIDATION_ERROR,
                    u'%s.check_target_obj called without "parent_obj_id"' %
                    self.__class__.__name__
                )

            q = self._find_target_obj_query()
            target_obj_exist = db.session.query(q.exists()).scalar()
            if not target_obj_exist:
                raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                   self.target_obj_class.__name__)
            if data:
                self.check_external_id(data)

    def _find_parent_obj_query(self):
        return self.parent_obj_class.query.filter(
            self.parent_obj_class.id == self.parent_obj_id
        )

    @abstractmethod
    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'api_checkup_obs_first_save used without "external_id"' %
                self.target_obj_class.__name__
            )
        q = self._find_target_obj_query().join(
            ActionIdentification
        ).join(rbAccountingSystem).filter(
            ActionIdentification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if target_obj_exist:
            raise ApiException(ALREADY_PRESENT_ERROR, u'%s already exist' %
                               self.target_obj_class.__name__)

    def check_external_id(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'api_checkup_obs_first_save used without "external_id"' %
                self.target_obj_class.__name__
            )
        q = ActionIdentification.query.join(rbAccountingSystem).filter(
            ActionIdentification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
            ActionIdentification.action_id == self.target_obj_id,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if not target_obj_exist:
            raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                               self.target_obj_class.__name__)

    def rb(self, code, rb_model, code_field_name='code'):
        id_ = self.rb_validate(rb_model, code, code_field_name)
        return code and {'code': code, 'id': id_} or None

    @staticmethod
    def arr(rb_func, codes, rb_name):
        return map(lambda code: rb_func(code, rb_name), codes)

    @staticmethod
    def rb_validate(rb_model, code, code_field_name):
        row_id = None
        if code:
            if isinstance(rb_model, basestring):
                rb = Vesta.get_rb(rb_model, code)
                row_id = rb['_id']
            else:
                field = getattr(rb_model, code_field_name)
                row_id = list(rb_model.query.filter(
                    field == code
                ).values(rb_model.id))[0][0]
        return row_id

    def mapping_part(self, part, data, res):
        for k, v in part.items():
            if v['rb']:
                if v['is_vector']:
                    res[k] = self.arr(
                        self.rb,
                        data.get(v['attr'], v.get('default')),
                        v['rb']
                    )
                else:
                    res[k] = self.rb(
                        data.get(v['attr'], v.get('default')),
                        v['rb']
                    )
            else:
                res[k] = data.get(v['attr'], v.get('default'))

    def _represent_part(self, part, data):
        res = {}
        for k, v in part.items():
            if v['rb']:
                if v['is_vector']:
                    rb_code_field = v.get('rb_code_field', 'code')
                    val = map(lambda x: x[rb_code_field], data[k])
                else:
                    val = data[k] and data[k][v.get('rb_code_field', 'code')]
            else:
                val = data[k]
            res[v['attr']] = self.safe_represent_val(val)
        return res

    @staticmethod
    def safe_represent_val(v):
        res = v
        if isinstance(v, datetime):
            res = safe_date(v)
        elif isinstance(v, Decimal):
            res = int(v)
        return res

    def save_external_data(self):
        if self.new:
            external_action = ActionIdentification(
                action=self.target_obj,
                action_id=self.target_obj_id,
                external_id=self.external_id,
                external_system=self.external_system,
                external_system_id=self.external_system.id,
            )
            db.session.add(external_action)

    @staticmethod
    def get_person_id(regional_code, tfoms_code):
        res = list(Person.query.join(Organisation).filter(
            Person.regionalCode == regional_code,
            Organisation.TFOMSCode == tfoms_code,
        ).values(Person.id))[0][0]
        return res
