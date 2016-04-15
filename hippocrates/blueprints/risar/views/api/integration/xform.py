# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from datetime import datetime
from decimal import Decimal
from abc import ABCMeta, abstractmethod

from nemesis.lib.apiutils import ApiException
from nemesis.views.rb import check_rb_value_exists
from nemesis.lib.vesta import Vesta
from nemesis.models.exists import rbAccountingSystem, MKB, rbBloodType
from blueprints.risar.models.risar import ActionIdentification
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_dict
from .utils import get_org_by_tfoms_code, get_person_by_codes, get_client_query, get_event_query


__author__ = 'viruzzz-kun'

logger = logging.getLogger('simple')


INTERNAL_ERROR = 500
VALIDATION_ERROR = 400
NOT_FOUND_ERROR = 404
ALREADY_PRESENT_ERROR = 409
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
        simplify(item)
        for item in l
        if item is not Undefined
    ]


class XForm(object):
    __metaclass__ = ABCMeta
    schema = None
    parent_obj_class = None
    target_obj_class = None
    parent_id_required = True
    target_id_required = True

    def __init__(self, api_version, is_create=False):
        self.version = 0
        self.new = is_create
        self.parent_obj_id = None
        self.target_obj_id = None
        self.parent_obj = None
        self.target_obj = None
        self.pcard = None
        self._changed = []
        self._deleted = []

        self.set_version(api_version)

    def set_version(self, version):
        for v in xrange(self.version + 1, version + 1):
            method = getattr(self, 'set_version_%i' % v, None)
            if method is None:
                raise ApiException(VALIDATION_ERROR, 'Version %i of API is unsupported' % (version, ))
            else:
                method()
        self.version = version

    def validate(self, data):
        if data is None:
            raise ApiException(VALIDATION_ERROR, 'No JSON body')
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
                raise ApiException(NOT_FOUND_ERROR, self.get_parent_nf_msg())
        self.parent_obj = parent_obj

    def find_target_obj(self, target_obj_id):
        self.target_obj_id = target_obj_id
        if target_obj_id is None:
            # Ручная валидация
            raise Exception(
                u'%s.find_target_obj called without "target_obj_id"' %
                self.__class__.__name__
            )
        else:
            target_obj = self._find_target_obj_query().first()
            if not target_obj:
                raise ApiException(NOT_FOUND_ERROR, self.get_target_nf_msg())
        self.target_obj = target_obj

    def check_parent_obj(self, parent_obj_id):
        self.parent_obj_id = parent_obj_id
        if self.parent_id_required or parent_obj_id:
            if parent_obj_id is None:
                # Ручная валидация
                raise ApiException(
                    VALIDATION_ERROR,
                    u'%s.check_parent_obj called without "parent_obj_id"' %
                    self.__class__.__name__
                )
            else:
                q = self._find_parent_obj_query()
                parent_obj_exists = db.session.query(q.exists()).scalar()
                if not parent_obj_exists:
                    raise ApiException(NOT_FOUND_ERROR, self.get_parent_nf_msg())

    def check_params(self, target_obj_id, parent_obj_id=None, data=None):
        self.parent_obj_id = parent_obj_id
        self.target_obj_id = target_obj_id
        if self.target_id_required and bool(self.new) ^ (target_obj_id is None):
            raise ApiException(
                VALIDATION_ERROR,
                u'Метод запроса не соответствует пути API'
            )
        if self.new:
            if not data:
                raise ApiException(
                    INTERNAL_ERROR,
                    u'%s.check_target_obj called without "data"' %
                    self.__class__.__name__
                )

            self.check_parent_obj(parent_obj_id)
            self.check_duplicate(data)
        else:
            if self.parent_id_required and parent_obj_id is None:
                # Ручная валидация
                raise ApiException(
                    VALIDATION_ERROR,
                    u'%s.check_target_obj called without "parent_obj_id"' %
                    self.__class__.__name__
                )

            if self.target_id_required:
                q = self._find_target_obj_query()
                target_obj_exist = db.session.query(q.exists()).scalar()
                if not target_obj_exist:
                    raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                                       self.target_obj_class.__name__)
            else:
                self.check_parent_obj(parent_obj_id)

            if data:
                self.check_external_id(data)

    def check_external_id(self, data):
        pass

    def _find_parent_obj_query(self):
        q = self.parent_obj_class.query.filter(
            self.parent_obj_class.id == self.parent_obj_id
        )
        if hasattr(self.parent_obj_class, 'deleted'):
            q = q.filter(self.parent_obj_class.deleted == 0)
        return q

    @abstractmethod
    def _find_target_obj_query(self):
        pass

    @abstractmethod
    def check_duplicate(self, data):
        pass

    def update_target_obj(self, data):
        pass

    def delete_target_obj(self):
        pass

    def store(self):
        db.session.add_all(self._changed)
        for d in self._deleted:
            db.session.delete(d)
        db.session.commit()

        self._changed = []
        self._deleted = []

    def get_target_nf_msg(self):
        return u'Не найден {0} с id = {1}'.format(self.target_obj_class.__name__, self.target_obj_id)

    def get_parent_nf_msg(self):
        return u'Не найден {0} с id = {1}'.format(self.parent_obj_class.__name__, self.parent_obj_id)

    # -----

    def find_org(self, tfoms_code):
        org = get_org_by_tfoms_code(tfoms_code)
        if not org:
            raise ApiException(NOT_FOUND_ERROR, u'Не найдена организация по коду {0}'.format(tfoms_code))
        return org

    @staticmethod
    def find_doctor(person_code, org_code):
        person = get_person_by_codes(person_code, org_code)
        if not person:
            raise ApiException(NOT_FOUND_ERROR, u'Не найден врач по коду {0} и коду ЛПУ {1}'.format(person_code, org_code))
        return person

    def find_client(self, client_id):
        client = get_client_query(client_id).first()
        if not client:
            raise ApiException(NOT_FOUND_ERROR, u'Не найден пациент с id = {0}'.format(client_id))
        return client

    def find_event(self, event_id):
        event = get_event_query(event_id).first()
        if not event:
            raise ApiException(NOT_FOUND_ERROR, u'Не найдена карта с id = {0}'.format(event_id))
        return event

    def check_prop_value(self, prop, value):
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            for val in value:
                self.check_prop_value(prop, val)
        elif prop.type.typeName in ('ReferenceRb', 'ExtReferenceRb'):
            rb_name = prop.type.valueDomain.split(';')[0]
            if (rb_name != 'rbBloodType'  # code in name field, see to_blood_type_rb()
                    and not check_rb_value_exists(rb_name, value['code'])):
                raise ApiException(VALIDATION_ERROR, u'Не найдено значение по коду {0} в справочнике {1}'.format(
                    value['code'], rb_name))

    @staticmethod
    def to_rb(code):
        return {
            'code': code
        } if code is not None else None

    @staticmethod
    def from_rb(rb):
        if rb is None:
            return None
        return rb.code if hasattr(rb, 'code') else rb['code']

    @staticmethod
    def to_mkb_rb(code):
        if code is None:
            return None
        mkb = db.session.query(MKB).filter(MKB.DiagID == code, MKB.deleted == 0).first()
        if not mkb:
            raise ApiException(400, u'Не найден МКБ по коду "{0}"'.format(code))
        return {
            'id': mkb.id,
            'code': code
        }

    @staticmethod
    def from_mkb_rb(rb):
        if rb is None:
            return None
        return rb.DiagID if hasattr(rb, 'DiagID') else rb['code']

    @staticmethod
    def to_blood_type_rb(code):
        if code is None:
            return None
        bt = db.session.query(rbBloodType).filter(rbBloodType.name == code).first()
        if not bt:
            raise ApiException(400, u'Не найдена группа крови по коду "{0}"'.format(code))
        return safe_dict(bt)

    @staticmethod
    def from_blood_type_rb(rb):
        if rb is None:
            return None
        return rb.name if hasattr(rb, 'name') else rb['name']

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
                row_id = rb and rb.get('_id')
            else:
                field = getattr(rb_model, code_field_name)
                res_list = list(rb_model.query.filter(
                    field == code
                ).values(rb_model.id))[0]
                row_id = res_list and res_list[0] or None
            if not row_id:
                raise ApiException(
                    NOT_FOUND_ERROR,
                    u'В справочнике "%s" запись с кодом "%s" не найдена' % (
                        rb_model.__name__,
                        code,
                    )
                )
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


from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind
from blueprints.risar.lib.card import PregnancyCard

class CheckupsXForm(XForm):
    __metaclass__ = ABCMeta

    def __init__(self, *a, **kw):
        super(CheckupsXForm, self).__init__(*a, **kw)
        self.external_id = None
        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).first()

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

    def set_pcard(self):
        event = self.parent_obj
        self.pcard = PregnancyCard.get_for_event(event)

    def get_diags_data(self, data):
        return data.get('medical_report', {})

    def get_diagnoses(self, data, form_data):
        # Прислали новый код МКБ, и не прислали старый - старый диагноз закрыли, новый открыли.
        # если тот же МКБ пришел не как осложнение, а как сопутствующий, это смена вида
        # если в списке диагнозов из МИС придут дубли кодов МКБ - отсекать лишние
        # Если код МКБ в основном заболевании - игнорировать (отсекать) его в осложнениях и сопутствующих.
        # Если код МКБ в осложнении - отсекать его в сопутствующих
        # если два раза в одной группе (в осложнениях, например) - оставлять один

        diags_data = self.get_diags_data(data)
        action = self.target_obj
        diagnostics = self.pcard.get_client_diagnostics(action.begDate,
                                                        action.endDate)
        db_diags = {}
        for diagnostic in diagnostics:
            diagnosis = diagnostic.diagnosis
            if diagnosis.endDate:
                continue
            q_list = list(Action_Diagnosis.query.join(
                rbDiagnosisKind,
            ).filter(
                Action_Diagnosis.action == action,
                Action_Diagnosis.diagnosis == diagnosis,
                Action_Diagnosis.deleted == 0,
            ).values(rbDiagnosisKind.code))
            diag_kind_code = 'associated'
            if q_list:
                diag_kind_code = q_list[0][0]
            db_diags[diagnostic.MKB] = {
                'diagnosis_id': diagnosis.id,
                'diagKind_code': diag_kind_code,
            }

        mis_diags = {}
        for risar_key, v in sorted(self.DIAG_KINDS_MAP.items(),
                                   key=lambda x: x[1]['level']):
            mis_key, is_vector, default = v['attr'], v['is_vector'], v['default']
            mkb_list = diags_data.get(mis_key, default)
            if not is_vector:
                mkb_list = mkb_list and [mkb_list] or []
            for mkb in mkb_list:
                if mkb not in mis_diags:
                    mis_diags[mkb] = {
                        'diagKind_code': risar_key,
                    }

        def add_diag_data():
            res.append({
                'id': db_diag.get('diagnosis_id'),
                'deleted': 0,
                'kind_changed': kind_changed,
                'diagnostic_changed': diagnostic_changed,
                'diagnostic': {
                    'mkb': self.rb(mkb, MKB, 'DiagID'),
                },
                'diagnosis_types': {
                    'final': diagnosis_type,
                },
                'person': form_data.get('person'),
                'set_date': form_data.get('beg_date'),
                'end_date': end_date,
            })

        res = []
        for mkb in set(db_diags.keys() + mis_diags.keys()):
            db_diag = db_diags.get(mkb, {})
            mis_diag = mis_diags.get(mkb, {})
            if db_diag and mis_diag:
                # сменить тип
                diagnostic_changed = False
                kind_changed = mis_diag.get('diagKind_code') != db_diag.get('diagKind_code')
                diagnosis_type = self.rb(mis_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = None
                add_diag_data()
            elif not db_diag and mis_diag:
                # открыть
                diagnostic_changed = False
                kind_changed = True
                diagnosis_type = self.rb(mis_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = None
                add_diag_data()
            elif db_diag and not mis_diag:
                # закрыть
                # нельзя закрывать, если используется в документах своего типа с бОльшей датой
                if self.is_using_by_next_checkups(db_diag['diagnosis_id'], action):
                    continue
                diagnostic_changed = True
                kind_changed = False
                diagnosis_type = self.rb(db_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = form_data.get('beg_date')
                add_diag_data()
        return res

    @classmethod
    def is_using_by_next_checkups(cls, diagnosis_id, action):
        q = Action_Diagnosis.query.join(cls.target_obj_class).filter(
            Action_Diagnosis.diagnosis_id == diagnosis_id,
            cls.target_obj_class.begDate >= action.begDate,
            cls.target_obj_class.actionType == action.actionType,
            cls.target_obj_class.id != action.id,
            cls.target_obj_class.deleted == 0,
        )
        return db.session.query(q.exists()).scalar()
