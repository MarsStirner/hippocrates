# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from datetime import datetime, timedelta
from decimal import Decimal
from abc import ABCMeta, abstractmethod

from blueprints.risar.lib.diagnosis import get_5_inspections_diagnoses, get_adjacent_inspections
from blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from blueprints.risar.models.risar import ActionIdentification

from nemesis.lib.data import create_action
from nemesis.views.rb import check_rb_value_exists
from nemesis.lib.vesta import Vesta, VestaNotFoundException
from nemesis.models.exists import rbAccountingSystem, MKB, rbBloodType
from nemesis.models.expert_protocol import EventMeasure, Measure, rbMeasureStatus
from nemesis.models.enums import MeasureStatus, MeasureType
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_dict, safe_int
from nemesis.lib.apiutils import ApiException
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
        if code is not None:
            if isinstance(rb_model, basestring):
                try:
                    rb = Vesta.get_rb(rb_model, code)
                except VestaNotFoundException:
                    row_id = None
                else:
                    row_id = rb and rb.get('_id')
                    if row_id == 'None':
                        row_id = None
            else:
                field = getattr(rb_model, rb_code_field)
                row_id = rb_model.query.filter(
                    field == code
                ).value(rb_model.id)
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


from nemesis.lib.diagnosis import create_or_update_diagnoses
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

    def _change_end_date(self, old_beg_date):
        if not self.new:
            if self.target_obj.endDate and self.target_obj.begDate != old_beg_date:
                left, cur, right = get_adjacent_inspections(self.target_obj)
                self.target_obj.endDate = max(
                    right.begDate - timedelta(seconds=1),
                    self.target_obj.begDate
                ) if right else None

    def _get_filtered_mis_diags(self, mis_diags):
        # filter mis diags
        # если в списке диагнозов из МИС придут дубли кодов МКБ - отсекать лишние
        # если код МКБ в основном заболевании - игнорировать (отсекать) его в осложнениях и сопутствующих
        # если код МКБ в осложнении - отсекать его в сопутствующих
        # если два раза в одной группе (в осложнениях, например) - оставлять один
        uniq_mis_diags = set()
        flt_mis_diags = []
        for diag_data in mis_diags:
            flt_mkbs = []
            for mkb in diag_data['mkbs']:
                if mkb not in uniq_mis_diags:
                    self.rb_validate(MKB, mkb, 'DiagID')
                    flt_mkbs.append(mkb)
                    uniq_mis_diags.add(mkb)
            if flt_mkbs:
                flt_mis_diags.append({
                    'kind': diag_data['kind'],
                    'mkbs': flt_mkbs
                })
        return flt_mis_diags

    def update_diagnoses_system(self, mis_diags, diag_type, old_action_data):
        """Из расчета, что на (пере)сохранение могут прийти данные с любыми изменениями,
        ломающими систему диагнозов (серьезная смена даты осмотра, изменение набора диагнозов),
        попытаться изменить состояние диагнозов в текущем, прошлом и следующем осмотрах.

        Редактирование осуществляется за 2 прохода: при первом проходе изменяется состояние
        диагнозов по данным осмотра с еще неизмененной датой начала, при втором - с уже обновленной.
        """
        with db.session.no_autoflush:
            mis_diags = self._get_filtered_mis_diags(mis_diags)

            if not self.new and self.target_obj.begDate != old_action_data['begDate']:
                t_beg_date = self.target_obj.begDate
                self.target_obj.begDate = old_action_data['begDate']
                t_person = self.target_obj.person
                self.target_obj.person = old_action_data['person']

                diag_sys = DiagnosesSystemManager.get_for_inspection(self.target_obj, diag_type)
                diag_sys.refresh_with_old_data(mis_diags, t_beg_date)
                new_diagnoses, changed_diagnoses = diag_sys.get_result()

                create_or_update_diagnoses(self.target_obj, new_diagnoses)
                db.session.add_all(changed_diagnoses)
                db.session.flush()
                self.target_obj.begDate = t_beg_date
                self.target_obj.person = t_person

            diag_sys = DiagnosesSystemManager.get_for_inspection(self.target_obj, diag_type)
            diag_sys.refresh_with(mis_diags)
            new_diagnoses, changed_diagnoses = diag_sys.get_result()
            create_or_update_diagnoses(self.target_obj, new_diagnoses)
            db.session.add_all(changed_diagnoses)

    def delete_diagnoses(self):
        """Изменить систему диагнозов после удаления осмотра
        """
        diag_sys = DiagnosesSystemManager.get_for_inspection(self.target_obj, None)
        diag_sys.refresh_with_deletion([])
        new_diagnoses, changed_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(self.target_obj, new_diagnoses)
        db.session.add_all(changed_diagnoses)


class DiagnosesSystemManager(object):
    """Класс, отвечающий за обновление диагнозов в существующей
    системе диагнозов в рамках карты пациентки РИСАР.
    """
    class InspectionSource(object):
        def __init__(self, action):
            self.action = action
        def get_date(self):
            return self.action.begDate
        def get_person(self):
            return self.action.person

    class MeasureResultSource(object):
        def __init__(self, action, measure_type):
            self.action = action
            self.measure_type = measure_type
        def get_date(self):
            if self.measure_type == MeasureType.checkup[0]:
                return self.action['CheckupDate'].value
            elif self.measure_type == MeasureType.hospitalization[0]:
                return self.action['IssueDate'].value
        def get_person(self):
            if self.measure_type == MeasureType.checkup[0]:
                return self.action['Doctor'].value
            elif self.measure_type == MeasureType.hospitalization[0]:
                return self.action['Doctor'].value

    @classmethod
    def get_for_inspection(cls, action, diag_type):
        return cls(cls.InspectionSource(action), diag_type)

    @classmethod
    def get_for_measure_result(cls, action, diag_type, measure_type):
        return cls(cls.MeasureResultSource(action, measure_type), diag_type)

    def __init__(self, source, diag_type):
        self.source = source
        # todo: считать для разных типов диагноза отдельно или объединить в единое поле расчетов?
        # Могут ли существовать одинаковые мкб, относящиеся к разным типам диагноза?
        # (отдельно диагноз предварительный с мкб1 и отдельно диагноз заключительный с мкб1 в одно и то же время)
        self.diag_type = diag_type
        self.existing_diags = get_5_inspections_diagnoses(self.source.action)
        self.to_create = []
        self.to_delete = []

    def add_diag_data(self, ds_id, mkb_code, diag_kind, ds_beg_date, ds_end_date,
                      dgn_beg_date, dgn_create_date, person,
                      diagnostic_changed=False, kind_changed=False):
        diagnosis_types = {
            self.diag_type: {'code': diag_kind}
        }
        self.to_create.append({
            'id': ds_id,
            'deleted': 0,
            'kind_changed': kind_changed,
            'diagnostic_changed': diagnostic_changed,
            'diagnostic': {
                'mkb': {'code': mkb_code},
                'set_date': dgn_beg_date,
                'create_datetime': dgn_create_date
            },
            'diagnosis_types': diagnosis_types,
            'person': {
                'id': person.id
            } if person else None,
            'set_date': ds_beg_date,
            'end_date': ds_end_date,
        })

    def get_result(self):
        return self.to_create, self.to_delete

    def refresh_with(self, mkb_data_list):
        """Рассчитать изменения в системе диагнозов на основе данных сохранения
        осмотра или результата мероприятия.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        """
        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']
        source_id = self.source.action.id
        action_date = self.source.get_date()
        new_person = self.source.get_person()

        for diag_data in mkb_data_list:
            new_kind = diag_data['kind']
            for mkb in diag_data['mkbs']:
                if mkb in by_mkb:
                    # mkb is in at least one of the inspections (previous, current, next)
                    insp_w_mkb = by_mkb[mkb]

                    # already exists in current action
                    if 'cur' in insp_w_mkb:
                        diag = by_inspection['cur'][mkb]

                        cur_diagn = diag['diagn']
                        diag_kind = diag['a_d'].diagnosisKind.code if diag['a_d'] else 'associated'
                        kind_changed = diag_kind != new_kind or not source_id
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = diag['ds'].endDate
                        diagnosis_id = diag['ds'].id
                        dgn_bd = cur_diagn.setDate if cur_diagn else None
                        dgn_cd = cur_diagn.createDatetime if cur_diagn else None
                        diagnostic_changed = dgn_bd != action_date or dgn_cd != action_date or not source_id
                        if 'left' not in insp_w_mkb:
                            # diag was created exactly in current action
                            ds_beg_date = action_date
                        if 'right' not in insp_w_mkb:
                            # close or open ds
                            ds_end_date = self.get_date_before(adj_inspections['right'])

                        if diagnostic_changed and source_id:
                            # need to delete dgn because it can have higher date than the date of 'cur' inspection
                            # TODO: test
                            cur_diagn.deleted = 1
                            self.to_delete.append(cur_diagn)

                    # not in current yet, but can be in one of adjacent:
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # todo: test
                        # diag is in the left and in the right -
                        # there are 2 different diagnoses, and left ds will be extended
                        # to include new diagn, right diagn will not be changed
                        diag_l = by_inspection['left'][mkb]
                        diagnosis_id = diag_l['ds'].id
                        ds_beg_date = diag_l['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'])
                        diagnostic_changed = kind_changed = True
                    elif 'left' in insp_w_mkb:
                        # ds from previous inspection that ends by the time of right inspection or remains opened
                        diag_l = by_inspection['left'][mkb]
                        diagnosis_id = diag_l['ds'].id
                        ds_beg_date = diag_l['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'])
                        diagnostic_changed = kind_changed = True
                    else:  # 'right' in insp_w_mkb:
                        # ds from next inspection now to start in current inspection
                        diag_r = by_inspection['right'][mkb]
                        diagnosis_id = diag_r['ds'].id
                        ds_beg_date = action_date
                        ds_end_date = diag_r['ds'].endDate
                        diagnostic_changed = kind_changed = True

                    dgn_beg_date = dgn_create_date = action_date
                    self.add_diag_data(diagnosis_id, mkb, new_kind, ds_beg_date, ds_end_date,
                                       dgn_beg_date, dgn_create_date, new_person, diagnostic_changed, kind_changed)
                else:
                    # is new mkb, not presented in any of 3 inspections
                    ds_beg_date = dgn_beg_date = dgn_create_date = action_date
                    ds_end_date = self.get_date_before(adj_inspections['right'])
                    self.add_diag_data(None, mkb, new_kind, ds_beg_date, ds_end_date,
                                       dgn_beg_date, dgn_create_date, new_person, True, True)

        # process existing diags, that were not sent from external source
        ext_mkbs = {mkb for diag_data in mkb_data_list for mkb in diag_data['mkbs']}
        self.refresh_with_deletion(ext_mkbs)

    def refresh_with_old_data(self, mkb_data_list, new_beg_date):
        """Рассчитать изменения в системе диагнозов на основе данных action с еще
        не измененной датой.

        Этот шаг требуется для обработки случаев, когда осмотр, который ранее являлся причиной
        появляения диагноза, а теперь оказывается сменил дату с перескоком через другие осмотры,
        мог либо унести свой диагноз с собой, либо оставить его в соседних осмотрах.
        Этот шаг может быть пропущен, если дата осмотра не изменилась. На этом шаге не могут быть
        созданы новые диагнозы и диагностики, а только изменены даты диагнозов или удалены
        диагнозы и диагностики.

        :param mkb_data_list: list of dicts with (diag_type, mkb_list) keys
        :param new_beg_date: datetime
        """

        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']

        old_action_date = self.source.get_date()
        if old_action_date == new_beg_date:
            return

        left_shift = old_action_date > new_beg_date and adj_inspections['left'] and \
            adj_inspections['left'].begDate > new_beg_date
        right_shift = old_action_date < new_beg_date and adj_inspections['right'] and \
            adj_inspections['right'].begDate < new_beg_date

        for diag_data in mkb_data_list:
            new_kind = diag_data['kind']
            for mkb in diag_data['mkbs']:
                if mkb in by_mkb:
                    # mkb is in at least one of the inspections (previous, current, next)
                    insp_w_mkb = by_mkb[mkb]

                    if 'cur' in insp_w_mkb and (left_shift or right_shift):
                        # exists in old action
                        diag = by_inspection['cur'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = diag['ds'].endDate

                        if 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                            # nothing changes in ds, diagn will be updated in next step
                            pass
                        elif right_shift and 'right' in insp_w_mkb:
                            # ds was in cur and in right - right is the new owner of ds
                            ds_beg_date = adj_inspections['right'].begDate
                        elif left_shift and 'left' in insp_w_mkb:
                            # ds was in left and in cur - left is the end of ds
                            ds_end_date = self.get_date_before(adj_inspections['cur'])
                        else:  # right_shift or left_shift:
                            # delete ds and it will be recreated in next step
                            # todo: test this case!
                            ds = diag['ds']
                            ds.deleted = 1
                            self.to_delete.append(ds)

                        # delete dgn
                        # todo: test
                        diag['diagn'].deleted = 1
                        self.to_delete.append(diag['diagn'])

                        self.add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)

        # process existing diags, that were not sent from external source
        ext_mkbs = {mkb for diag_data in mkb_data_list for mkb in diag_data['mkbs']}
        for mkb in by_mkb:
            if mkb not in ext_mkbs:
                insp_w_mkb = by_mkb[mkb]

                # if not shifted, then process in next step
                if 'cur' in insp_w_mkb and (left_shift or right_shift):
                    if 'left' not in insp_w_mkb and 'right' not in insp_w_mkb:
                        # diag was created only in this inspection and can be deleted
                        ds = by_inspection['cur'][mkb]['ds']
                        ds.deleted = 1
                        self.to_delete.append(ds)
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # diag is in the left and in the right
                        # if its is the same diagnosis, it will be splitted in 2 - left will be shrinked,
                        # right will be created new;
                        # else there are 2 different diagnoses, that will have their dates changed
                        diag_l = by_inspection['left'][mkb]
                        diag_r = by_inspection['right'][mkb]
                        if diag_l['ds'].id == diag_r['ds'].id:
                            # # no changes because without cur inspection ds would be continuous span
                            # from left to right inspection
                            pass
                        else:
                            # todo: ignore this case?
                            # left
                            ds_beg_date = diag_l['ds'].setDate
                            ds_end_date = self.get_date_before(adj_inspections['right'])
                            self.add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                            # right
                            ds_beg_date = adj_inspections['right'].begDate
                            ds_end_date = diag_r['ds'].endDate
                            self.add_diag_data(diag_r['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                    elif 'left' in insp_w_mkb:
                        # close diag from previous inspection
                        diag = by_inspection['left'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['right'])
                        self.add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)
                    elif 'right' in insp_w_mkb:
                        # move in future setDate of next inspection's diag
                        diag = by_inspection['right'][mkb]
                        ds_beg_date = adj_inspections['right'].begDate
                        ds_end_date = diag['ds'].endDate
                        self.add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)

                    # delete unneeded dgn from cur
                    # todo: test
                    diagn = by_inspection['cur'][mkb]['diagn']
                    diagn.deleted = 1
                    self.to_delete.append(diagn)

    def refresh_with_deletion(self, mkb_to_stay_list):
        """Рассчитать изменения в системе диагнозов на основе данных удаления
        всех МКБ, относящихся к текущему осмотру, кроме тех, что должны
        остаться - mkb_to_stay_list.

        :param mkb_to_stay_list: list of mkb codes
        """
        by_mkb = self.existing_diags['by_mkb']
        by_inspection = self.existing_diags['by_inspection']
        adj_inspections = self.existing_diags['inspections']
        source_id = self.source.action.id

        for mkb in by_mkb:
            if mkb not in mkb_to_stay_list:
                insp_w_mkb = by_mkb[mkb]
                # diags in current inspection, that should not be here according to new external data
                if 'cur' in insp_w_mkb:
                    if 'left' not in insp_w_mkb and 'right' not in insp_w_mkb:
                        # diag was created only in this inspection and can be deleted
                        ds = by_inspection['cur'][mkb]['ds']
                        ds.deleted = 1
                        self.to_delete.append(ds)
                    elif 'left' in insp_w_mkb and 'right' in insp_w_mkb:
                        # diag is in the left and in the right
                        # if its is the same diagnosis, it will be splitted in 2 - left will be shrinked,
                        # right will be created new;
                        # else there are 2 different diagnoses, that will have their dates changed
                        diag_l = by_inspection['left'][mkb]
                        diag_r = by_inspection['right'][mkb]
                        if diag_l['ds'].id == diag_r['ds'].id:
                            # left
                            ds_beg_date = diag_l['ds'].setDate
                            ds_end_date = self.get_date_before(adj_inspections['cur'])
                            self.add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                            # right
                            ds_beg_date = dgn_beg_date = dgn_create_date = adj_inspections['right'].begDate
                            ds_end_date = diag_r['ds'].endDate
                            diag_kind = diag_r['a_d'].diagnosisKind.code if diag_r['a_d'] else 'associated'
                            person = diag_r['diagn'].person
                            self.add_diag_data(None, mkb, diag_kind, ds_beg_date, ds_end_date,
                                               dgn_beg_date, dgn_create_date, person, True, True)
                        else:
                            # left
                            ds_beg_date = diag_l['ds'].setDate
                            ds_end_date = self.get_date_before(adj_inspections['cur'])
                            self.add_diag_data(diag_l['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                            # right
                            ds_beg_date = adj_inspections['right'].begDate
                            ds_end_date = diag_r['ds'].endDate
                            self.add_diag_data(diag_r['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                               None, None, None, False, False)
                    elif 'left' in insp_w_mkb:
                        # in previous but now not in current
                        diag = by_inspection['left'][mkb]
                        ds_beg_date = diag['ds'].setDate
                        ds_end_date = self.get_date_before(adj_inspections['cur'])
                        self.add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)
                    elif 'right' in insp_w_mkb:
                        # move in future setDate of next inspection's diag
                        diag = by_inspection['right'][mkb]
                        ds_beg_date = adj_inspections['right'].begDate
                        ds_end_date = diag['ds'].endDate
                        self.add_diag_data(diag['ds'].id, mkb, None, ds_beg_date, ds_end_date,
                                           None, None, None, False, False)

                    if source_id:
                        # delete unneeded dgn from cur
                        # dgn can be with higher date, delete just in case
                        # todo: test
                        diagn = by_inspection['cur'][mkb]['diagn']
                        if diagn:
                            diagn.deleted = 1
                            self.to_delete.append(diagn)
                # else:
                    # diags in 'left' and 'right' should be ok, no edit needed

    @staticmethod
    def get_date_before(action):
        return action.begDate - timedelta(seconds=1) if action else None


class MeasuresResultsXForm(ExternalXForm):
    __metaclass__ = ABCMeta

    diagnosis_codes = None

    def __init__(self, *args, **kwargs):
        super(MeasuresResultsXForm, self).__init__(*args, **kwargs)
        self.em = None
        self.person = None

    @abstractmethod
    def prepare_params(self, data):
        pass

    @abstractmethod
    def get_properties_data(self, data):
        return data

    def update_measure_data(self, data):
        status = data.get('status')
        if status:
            self.em.status = self.rb_validate(rbMeasureStatus, status, 'code')

    def changes_diagnoses_system(self):
        return bool(self.diagnosis_codes)

    def get_data_for_diags(self, data):
        pass

    def modify_target(self, new_date, new_person):
        return self.target_obj

    def get_measure_type(self):
        pass

    def update_target_obj(self, data):
        self.prepare_params(data)

        if self.new:
            self.create_action()
        else:
            self.find_target_obj(self.target_obj_id)

        mr_data = self.get_data_for_diags(data)

        properties_data = self.get_properties_data(data)
        self.set_properties(properties_data)
        self.update_measure_data(data)
        self.save_external_data()
        if self.changes_diagnoses_system():
            self.update_diagnoses_system(mr_data)

    def update_diagnoses_system(self, mr_data):
        with db.session.no_autoflush:
            new_mkbs = mr_data['new_mkbs']
            new_diags = [dict(diag_type='associated', mkb_list=new_mkbs)]
            if not self.new and mr_data['changed']:
                target = self.modify_target(mr_data['old_beg_date'], mr_data['old_person'])

                diag_sys = DiagnosesSystemManager.get_for_measure_result(
                    target, 'final', self.get_measure_type().value
                )
                diag_sys.refresh_with_old_data(new_diags, mr_data['new_beg_date'])
                new_diagnoses, changed_diagnoses = diag_sys.get_result()

                create_or_update_diagnoses(self.target_obj, new_diagnoses)
                db.session.add_all(changed_diagnoses)
                db.session.flush()
                self.modify_target(mr_data['new_beg_date'], mr_data['new_person'])

            diag_sys = DiagnosesSystemManager.get_for_measure_result(
                self.target_obj, 'final', self.get_measure_type().value
            )
            diag_sys.refresh_with(new_diags)
            new_diagnoses, changed_diagnoses = diag_sys.get_result()
            create_or_update_diagnoses(self.target_obj, new_diagnoses)
            db.session.add_all(changed_diagnoses)

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
