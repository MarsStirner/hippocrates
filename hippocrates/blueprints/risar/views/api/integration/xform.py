# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema

from nemesis.lib.apiutils import ApiException
from nemesis.models.client import Client
from .utils import get_org_by_tfoms_code, get_person_by_code


__author__ = 'viruzzz-kun'

logger = logging.getLogger('simple')


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
