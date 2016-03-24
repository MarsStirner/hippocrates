#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging

import functools

import jsonschema
from blueprints.risar.views.api.integration.checkup_obs_first_schemas import \
    CheckupObsFirstSchema
from nemesis.lib.apiutils import ApiException
from nemesis.models.exists import rbAccountingSystem
from nemesis.systemwide import db

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


class XForm(object):
    version = 0
    rbAccountingSystem = None
    external_system_id = None
    schema = None
    new = False
    parent_obj = None
    target_obj = None
    _parent_obj_id = None
    _target_obj_id = None

    def __init__(self, api_version):
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

    def set_external_system(self, external_system_id):
        self.external_system_id = external_system_id
        self.rbAccountingSystem = rbAS = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == external_system_id
        ).first()
        if not rbAS:
            raise ApiException(404, 'External system not found')

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
                406,
                'Validation error',
                errors=errors,
            )

    @property
    def parent_obj_id(self):
        if self.rbAccountingSystem:
            return self._parent_obj_id
        return self.parent_obj.id

    @parent_obj_id.setter
    def parent_obj_id(self, value):
        self._parent_obj_id = value

    @property
    def target_obj_id(self):
        if self.rbAccountingSystem:
            return self._target_obj_id
        return self.target_obj.id

    @target_obj_id.setter
    def target_obj_id(self, value):
        self._target_obj_id = value

    def find_parent_obj(self, parent_obj_id):
        self.parent_obj_id = parent_obj_id
        if parent_obj_id is None:
            # Ручная валидация
            raise Exception(
                u'%s.find_parent_obj called without "parent_obj_id"' %
                self.__class__.__name__
            )
        else:
            parent_obj = self._find_parent_obj_query(parent_obj_id).first()
            if not parent_obj:
                raise ApiException(404, u'Card not found')
        self.parent_obj = parent_obj

    def find_target_obj(self, parent_id, target_obj_id):
        self.find_parent_obj(parent_id)
        self.target_obj_id = target_obj_id
        if target_obj_id is None:
            target_obj = self.target_obj_class()
            db.session.add(target_obj)
            self.new = True
        else:
            target_obj = self._find_target_obj_query(target_obj_id).first()
            if not target_obj:
                raise ApiException(404, u'Client not found')
        self.target_obj = target_obj


class CheckupObsFirstXForm(CheckupObsFirstSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Client

    def _find_parent_obj_query(self, parent_obj_id):
        if not self.rbAccountingSystem:
            return Client.query.filter(Client.id == parent_obj_id)
        return Client.query.join(ClientIdentification).filter(
            ClientIdentification.identifier == parent_obj_id,
            ClientIdentification.accountingSystems == self.rbAccountingSystem,
        )

    def _find_target_obj_query(self, target_obj_id):
        if not self.rbAccountingSystem:
            return self.target_obj_class.query.filter(
                self.target_obj_class.id == target_obj_id
            )
        return self.target_obj_class.query.join(ClientIdentification).filter(
            ClientIdentification.identifier == target_obj_id,
            ClientIdentification.accountingSystems == self.rbAccountingSystem,
        )

    def update_target_obj(self, data):
        with db.session.no_autoflush:
            self._update_general_info(data.get('general_info', None))
            self._update_somatic_status(data.get('somatic_status', None))
            self._update_obstetric_status(data.get('obstetric_status', None))
            self._update_medical_report(data.get('medical_report', None))

    def as_json(self):
        target_obj = self.target_obj
        return {
            "exam_obs_id": self.target_obj_id,
            "general_info": self._represent_general_info(target_obj.general_info),
            "somatic_status": self._represent_somatic_status(target_obj.somatic_status),
            "obstetric_status": self._represent_obstetric_status(target_obj.obstetric_status),
            "medical_report": self._represent_medical_report(target_obj.medical_report),
        }

    @none_default
    def _represent_general_info(self, general_info):
        return {
            "date": "2011-11-11",
            "time": "18:00",
            "doctor": "Иванов И.И.",
            "height": 175,
            "weight": 70
        }

    @none_default
    def _represent_somatic_status(self, somatic_status):
        return {
            "state": "udovletvoritel_noe",
            "subcutaneous_fat": "izbytocnorazvita",
            "tongue": "01",
            "complaints": "oteki",
            "skin": "suhaa",
            "lymph": "boleznennye",
            "breast": "nagrubanie",
            "heart_tones": "akzentIItona",
            "pulse": "defizitpul_sa",
            "nipples": "norma",
            "mouth": "sanirovana",
            "respiratory": "hripyotsutstvuut",
            "abdomen": "jivotnaprajennyj",
            "liver": "nepal_piruetsa",
            "urinoexcretory": "СindromПasternazkogo",
            "ad_right_high": 120,
            "ad_left_high": 120,
            "ad_right_low": 80,
            "ad_left_low": 80,
            "veins": "noma",
            "heart_rate": 80
        }

    @none_default
    def _represent_obstetric_status(self, obstetric_status):
        return {
            "uterus_state": "normal_nyjtonus",
            "dssp": 1,
            "dscr": 1,
            "dstr": 1,
            "cext": 1,
            "soloviev_index": 1
        }

    @none_default
    def _represent_medical_report(self, medical_report):
        return {
            "pregnancy_week": 42,
            "next_visit_date": "2011-11-12",
            "pregnancy_continuation": true,
            "abortion_refusal": true,
            "diagnosis_osn": "Q00.0",
            "recommendations": "улыбаться",
            "notes": "мало улыбается"
        }

    def _update_general_info(self, general_info):
        pass

    def _update_somatic_status(self, somatic_status):
        pass

    def _update_obstetric_status(self, obstetric_status):
        pass

    def _update_medical_report(self, medical_report):
        pass
