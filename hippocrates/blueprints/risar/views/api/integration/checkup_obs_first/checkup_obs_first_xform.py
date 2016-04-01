#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging

import functools

import jsonschema
from abc import ABCMeta, abstractmethod
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.views.api.integration.checkup_obs_first_schemas import \
    CheckupObsFirstSchema
from nemesis.lib.apiutils import ApiException
from nemesis.models.actions import ActionType, Action
from nemesis.models.event import Event
from nemesis.systemwide import db
from sqlalchemy import literal

logger = logging.getLogger('simple')

INTERNAL_ERROR = 500
VALIDATION_ERROR = 406
NOT_FOUND_ERROR = 404
ALREADY_PRESENT_ERROR = 400


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
    __metaclass__ = ABCMeta

    version = 0
    schema = None
    new = False
    parent_obj_id = None
    target_obj_id = None
    parent_obj_class = None
    target_obj_class = None

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
            parent_obj_exists = db.session.query(
                literal(True)
            ).filter(q.exists()).scalar()
            if not parent_obj_exists:
                raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                   self.parent_obj_class.__name__)

    def check_target_obj(self, parent_obj_id, target_obj_id):
        self.parent_obj_id = parent_obj_id
        self.target_obj_id = target_obj_id
        if target_obj_id is None:
            self.new = True
            self.check_parent_obj(parent_obj_id)
        else:
            if parent_obj_id is None:
                # Ручная валидация
                raise ApiException(
                    VALIDATION_ERROR,
                    u'%s.check_target_obj called without "parent_obj_id"' %
                    self.__class__.__name__
                )

            q = self._find_target_obj_query()
            target_obj_exists = db.session.query(
                literal(True)
            ).filter(q.exists()).scalar()
            if not target_obj_exists:
                raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                   self.target_obj_class.__name__)

    def _find_parent_obj_query(self):
        return self.parent_obj_class.query.filter(
            self.parent_obj_class.id == self.parent_obj_id
        )

    @abstractmethod
    def _find_target_obj_query(self):
        pass


class CheckupObsFirstXForm(CheckupObsFirstSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        return self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == first_inspection_code,
        )

    def update_target_obj(self, data):
        # target_obj = self.target_obj_class()
        # # db.session.add(target_obj)
        # self.target_obj = target_obj
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
