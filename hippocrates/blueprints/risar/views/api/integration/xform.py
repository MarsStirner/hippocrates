# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from datetime import datetime
from decimal import Decimal
from abc import ABCMeta, abstractmethod
from blueprints.risar.lib.expert.em_diagnosis import update_patient_diagnoses, \
    get_event_measure_diag

from nemesis.lib.apiutils import ApiException
from nemesis.lib.data import create_action
from nemesis.lib.diagnosis import diagnosis_using_by_next_checkups
from nemesis.views.rb import check_rb_value_exists
from nemesis.lib.vesta import Vesta
from nemesis.models.exists import rbAccountingSystem, MKB, rbBloodType
from blueprints.risar.models.risar import ActionIdentification
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_dict, safe_int
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
        if self.target_id_required and target_obj_id is None:
            # Ручная валидация
            raise Exception(
                u'%s.find_target_obj called without "target_obj_id"' %
                self.__class__.__name__
            )
        else:
            target_obj = self._find_target_obj_query().first()
            if not target_obj:
                raise ApiException(NOT_FOUND_ERROR, self.get_target_nf_msg())
        self.target_obj_id = target_obj.id
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
        self.parent_obj_id = safe_int(parent_obj_id)
        self.target_obj_id = safe_int(target_obj_id)
        if self.target_id_required and (bool(self.new) ^ (target_obj_id is None)):
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
            raise ApiException(
                NOT_FOUND_ERROR,
                u'Не найдена организация по коду {0}'.format(tfoms_code)
            )
        return org

    @staticmethod
    def from_org_rb(org):
        if org is None:
            return None
        return org.TFOMSCode

    @staticmethod
    def find_doctor(person_code, org_code):
        person = get_person_by_codes(person_code, org_code)
        if not person:
            raise ApiException(
                NOT_FOUND_ERROR,
                u'Не найден врач по коду {0} и коду ЛПУ {1}'.format(person_code, org_code)
            )
        return person

    @staticmethod
    def from_person_rb(person):
        if person is None:
            return None
        return person.regionalCode

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

    @staticmethod
    def find_mkb(code):
        mkb = db.session.query(MKB).filter(MKB.DiagID == code, MKB.deleted == 0).first()
        if not mkb:
            raise ApiException(400, u'Не найден МКБ по коду "{0}"'.format(code))
        return mkb

    def check_prop_value(self, prop, value):
        if value is None:
            return
        if isinstance(value, (list, tuple)):
            for val in value:
                self.check_prop_value(prop, val)
        elif prop.type.typeName in ('ReferenceRb', 'ExtReferenceRb'):
            rb_name = prop.type.valueDomain.split(';')[0]
            if rb_name not in ('rbBloodType', 'rbDocumentType', 'rbPolicyType'):
                self._check_rb_value(rb_name, value['code'])

    def _check_rb_value(self, rb_name, value_code):
        field_name = None
        if rb_name == 'rbBloodType':
            field_name = 'name'
        elif rb_name in ('rbDocumentType', 'rbPolicyType'):
            field_name = 'TFOMSCode'
        if not check_rb_value_exists(rb_name, value_code, field_name):
            raise ApiException(
                VALIDATION_ERROR,
                u'Не найдено значение по коду `{0}` в справочнике {1}'.format(value_code, rb_name)
            )

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
        mkb = XForm.find_mkb(code)
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

    @staticmethod
    def to_enum(value, enum_model):
        """
        :param value: int | None
        :param enum_model: nemesis.lib.enum.EnumBase class
        :return nemesis.lib.enum.EnumBase instance | None:
        """
        if value is None:
            return None
        enum = enum_model(value)
        return enum if enum.is_valid() else None

    def rb(self, code, rb_model, rb_code_field='code'):
        id_ = self.rb_validate(rb_model, code, rb_code_field)
        return code and {'code': code, 'id': id_} or None

    @staticmethod
    def arr(rb_func, codes, rb_name, rb_code_field='code'):
        return map(lambda code: rb_func(code, rb_name, rb_code_field), codes)

    @staticmethod
    def rb_validate(rb_model, code, rb_code_field):
        row_id = None
        if code:
            if isinstance(rb_model, basestring):
                rb = Vesta.get_rb(rb_model, code)
                row_id = rb and rb.get('_id')
            else:
                field = getattr(rb_model, rb_code_field)
                res_list = list(rb_model.query.filter(
                    field == code
                ).values(rb_model.id))[0]
                row_id = res_list and res_list[0] or None
            if not row_id:
                raise ApiException(
                    NOT_FOUND_ERROR,
                    u'В справочнике "%s" запись с кодом "%s" не найдена' % (
                        rb_model,
                        code,
                    )
                )
        return row_id

    def mapping_part(self, part_map, data, res):
        if not data:
            return
        for k, v in part_map.items():
            val = data.get(v['attr'], v.get('default'))
            if v['rb']:
                rb_code_field = v.get('rb_code_field', 'code')
                if v['is_vector']:
                    res[k] = self.arr(self.rb, val, v['rb'], rb_code_field)
                else:
                    res[k] = self.rb(val, v['rb'], rb_code_field)
            else:
                res[k] = val

    def _represent_part(self, part, data):
        res = {}
        for k, v in part.items():
            if v['rb']:
                rb_code_field = v.get('rb_code_field', 'code')
                if v['is_vector']:
                    if isinstance(v['rb'], basestring):
                        val = map(lambda x: x[rb_code_field], data[k])
                    else:
                        val = map(lambda x: getattr(x, rb_code_field), data[k])
                else:
                    if isinstance(v['rb'], basestring):
                        val = data[k] and data[k][rb_code_field]
                    else:
                        val = data[k] and getattr(data[k], rb_code_field)
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

    def safe_time_format(self, val, format):
        if val:
            return val.strftime(format)

    @staticmethod
    def or_undefined(value):
        return value if value in ('', False, 0) or bool(value) else Undefined


class ExternalXForm(XForm):
    __metaclass__ = ABCMeta

    def __init__(self, *a, **kw):
        super(ExternalXForm, self).__init__(*a, **kw)
        self.external_id = None
        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).first()

    def check_duplicate(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'check_duplicate used without "external_id"'
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
                u'check_external_id used without "external_id"'
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

    def delete_external_data(self):
        ActionIdentification.query.filter(
            ActionIdentification.action_id == self.target_obj_id,
            ActionIdentification.external_id == self.external_id,
            ActionIdentification.external_system_id == self.external_system.id,
        ).delete()


from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind, \
    rbDiagnosisTypeN
from blueprints.risar.lib.card import PregnancyCard

class CheckupsXForm(ExternalXForm):
    __metaclass__ = ABCMeta

    def set_pcard(self):
        if not self.pcard:
            if not self.parent_obj:
                self.find_parent_obj(self.parent_obj_id)
            event = self.parent_obj
            self.pcard = PregnancyCard.get_for_event(event)

    def reevaluate_data(self):
        self.set_pcard()
        self.pcard.reevaluate_card_attrs()

    def generate_measures(self):
        em_ctrl = EventMeasureController()
        em_ctrl.regenerate(self.target_obj)

    def get_diagnoses(self, diags_data_list, person, set_date):
        # Прислали новый код МКБ, и не прислали старый - старый диагноз закрыли, новый открыли.
        # если тот же МКБ пришел не как осложнение, а как сопутствующий, это смена вида
        # если в списке диагнозов из МИС придут дубли кодов МКБ - отсекать лишние
        # Если код МКБ в основном заболевании - игнорировать (отсекать) его в осложнениях и сопутствующих.
        # Если код МКБ в осложнении - отсекать его в сопутствующих
        # если два раза в одной группе (в осложнениях, например) - оставлять один

        action = self.target_obj
        diagnostics = self.pcard.get_client_diagnostics(action.begDate,
                                                        action.endDate)
        db_diags = {}
        default_kind_codes = dict((x[2], 'associated') for x in diags_data_list)
        for diagnostic in diagnostics:
            diagnosis = diagnostic.diagnosis
            if diagnosis.endDate:
                continue
            q_dict = dict(Action_Diagnosis.query.join(
                rbDiagnosisKind, rbDiagnosisTypeN,
            ).filter(
                Action_Diagnosis.action == action,
                Action_Diagnosis.diagnosis == diagnosis,
                Action_Diagnosis.deleted == 0,
            ).values(rbDiagnosisTypeN.code, rbDiagnosisKind.code))
            diag_kind_codes = default_kind_codes.copy()
            diag_kind_codes.update(q_dict)
            db_diags[diagnostic.MKB] = {
                'diagnosis_id': diagnosis.id,
                'diagKind_codes': diag_kind_codes,
            }

        mis_diags = {}
        for diags_data, diag_kinds_map, diag_type in diags_data_list:
            mis_diags_uniq = set()
            for mis_diag_kind, v in sorted(diag_kinds_map.items(),
                                           key=lambda x: x[1]['level']):
                mis_key, is_vector, default = v['attr'], v['is_vector'], v['default']
                mkb_list = diags_data.get(mis_key, default)
                if not is_vector:
                    mkb_list = mkb_list and [mkb_list] or []
                for mkb in mkb_list:
                    if mkb not in mis_diags_uniq:
                        mis_diags_uniq.add(mkb)
                        mis_diags.setdefault(
                            mkb, {}
                        ).setdefault(
                            'diagKind_codes', {}
                        ).update(
                            {diag_type: mis_diag_kind}
                        )

        def add_diag_data():
            res.append({
                'id': db_diag.get('diagnosis_id'),
                'deleted': 0,
                'kind_changed': kind_changed,
                'diagnostic_changed': diagnostic_changed,
                'diagnostic': {
                    'mkb': self.rb(mkb, MKB, 'DiagID'),
                },
                'diagnosis_types': diagnosis_types,
                'person': person,
                'set_date': set_date,
                'end_date': end_date,
            })

        res = []
        for mkb in set(db_diags.keys() + mis_diags.keys()):
            db_diag = db_diags.get(mkb, {})
            mis_diag = mis_diags.get(mkb, {})
            db_diagnosis_types = dict(
                (k, self.rb(v, rbDiagnosisKind)) for k, v in db_diag.get('diagKind_codes', {}).items()
            )
            mis_diagnosis_types = dict(
                (k, self.rb(v, rbDiagnosisKind)) for k, v in mis_diag.get('diagKind_codes', {}).items()
            )
            if db_diag and mis_diag:
                # сменить тип
                diagnostic_changed = False
                kind_changed = mis_diag.get('diagKind_codes') != db_diag.get('diagKind_codes')
                diagnosis_types = mis_diagnosis_types
                end_date = None
                add_diag_data()
            elif not db_diag and mis_diag:
                # открыть
                diagnostic_changed = False
                kind_changed = True
                diagnosis_types = mis_diagnosis_types
                end_date = None
                add_diag_data()
            elif db_diag and not mis_diag:
                # закрыть
                # нельзя закрывать, если используется в документах своего типа с бОльшей датой
                if diagnosis_using_by_next_checkups(action):
                    continue
                diagnostic_changed = True
                kind_changed = False
                diagnosis_types = db_diagnosis_types
                end_date = set_date
                add_diag_data()
        return res


from nemesis.models.expert_protocol import EventMeasure, Measure
from blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from nemesis.models.enums import MeasureStatus

class MeasuresResultsXForm(ExternalXForm):
    __metaclass__ = ABCMeta

    @abstractmethod
    def prepare_params(self, data):
        self.em = None
        self.person = None

    @abstractmethod
    def get_properties_data(self, data):
        return data

    def update_target_obj(self, data):
        self.prepare_params(data)

        if self.new:
            self.create_action()
            old_event_measure_diag = None
        else:
            self.find_target_obj(self.target_obj_id)
            old_event_measure_diag = get_event_measure_diag(self.target_obj, raw=True)

        properties_data = self.get_properties_data(data)
        self.set_properties(properties_data)
        update_patient_diagnoses(old_event_measure_diag, self.target_obj)
        self.save_external_data()

    def get_event_measure(self, event_measure_id, measure_code, beg_date, end_date):
        if event_measure_id:
            em = EventMeasure.query.get(event_measure_id)
            if not em:
                raise ApiException(NOT_FOUND_ERROR,
                                   u'Не найдено EM с id = '.format(event_measure_id))
        else:
            em = self.create_hand_event_measure(measure_code, beg_date, end_date)
        return em

    def create_hand_event_measure(self, measure_code, beg_date, end_date):
        status = MeasureStatus.performed[0]
        measure = Measure.query.filter(Measure.code == measure_code).first()
        today = datetime.today()

        em = EventMeasure()
        em.manual_measure = measure
        em.measure_id = measure.id
        em.begDateTime, em.endDateTime = (beg_date, end_date) if all((beg_date, end_date)) else (today, today)
        em.status = status
        # em.event = self.parent_obj
        em.event_id = self.parent_obj_id
        return em

    def create_action(self):
        # by blueprints.risar.views.api.measure.api_0_event_measure_result_save

        em_ctrl = EventMeasureController()
        event_id = self.em.event_id
        action_type_id = self.em.measure.resultAt_id
        em_result = create_action(action_type_id, event_id)
        self.em.result_action = em_result
        em_ctrl.make_assigned(self.em)
        db.session.add_all((self.em, em_result))

        self.target_obj = em_result

    def set_properties(self, data):
        for code, value in data.iteritems():
            if code in self.target_obj.propsByCode:
                try:
                    prop = self.target_obj.propsByCode[code]
                    self.check_prop_value(prop, value)
                    prop.value = value
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise

    def delete_target_obj(self):
        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0
        ).update({'deleted': 1})

        self.delete_external_data()

        status = MeasureStatus.cancelled[0]
        EventMeasure.query.filter(
            EventMeasure.resultAction_id == self.target_obj_id
        ).update({
            'resultAction_id': None,
            'status': status,
        })
