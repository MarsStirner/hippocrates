# -*- coding: utf-8 -*-
import functools
import logging
import jsonschema
from datetime import datetime
from decimal import Decimal
from abc import ABCMeta, abstractmethod

from hippocrates.blueprints.risar.lib.diagnosis import DiagnosesSystemManager, AdjasentInspectionsState
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.datetime_interval import DateTimeInterval
from hippocrates.blueprints.risar.models.risar import ActionIdentification
from hippocrates.blueprints.risar.risar_config import inspections_span_flatcodes, risar_gyn_checkup_flat_code
from hippocrates.blueprints.risar.lib.card import PregnancyCard, GynecologicCard
from hippocrates.blueprints.risar.lib.notification import NotificationQueue

from nemesis.lib.data import create_action
from nemesis.views.rb import check_rb_value_exists
from nemesis.lib.vesta import Vesta, VestaNotFoundException
from nemesis.models.exists import rbAccountingSystem, MKB, rbBloodType
from nemesis.models.expert_protocol import EventMeasure, Measure, rbMeasureStatus
from nemesis.models.enums import MeasureStatus
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_dict, safe_int
from nemesis.lib.apiutils import ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from .utils import get_org_by_org_code, get_person_by_codes, get_client_query, get_event_query, \
    get_org_structure_by_code

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
                raise ApiException(VALIDATION_ERROR, u'Версия %i API не поддерживается' % (version, ))
            else:
                method()
        self.version = version

    def validate(self, data):
        if data is None:
            raise ApiException(VALIDATION_ERROR, u'Нет данных')
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
                u'Ошибка валидации',
                errors=errors,
            )

    def find_parent_obj(self, parent_obj_id):
        self.parent_obj_id = parent_obj_id
        if parent_obj_id is None:
            # Ручная валидация
            raise Exception(
                u'%s.find_parent_obj вызван без "parent_obj_id"' %
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
                u'%s.find_target_obj вызван без "target_obj_id"' %
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
                    u'%s.check_parent_obj вызван без "parent_obj_id"' %
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
                    u'%s.check_target_obj вызван с пустой "data"' %
                    self.__class__.__name__
                )

            self.check_parent_obj(parent_obj_id)
            self.check_duplicate(data)
        else:
            if self.parent_id_required and parent_obj_id is None:
                # Ручная валидация
                raise ApiException(
                    VALIDATION_ERROR,
                    u'%s.check_target_obj вызван без "parent_obj_id"' %
                    self.__class__.__name__
                )

            if self.target_id_required:
                q = self._find_target_obj_query()
                target_obj_exist = db.session.query(q.exists()).scalar()
                if not target_obj_exist:
                    raise ApiException(NOT_FOUND_ERROR, u'%s не найден' %
                                       self.target_obj_class.__name__)
            elif self.parent_id_required:
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
        NotificationQueue.process_events()

        self._changed = []
        self._deleted = []

    def get_target_nf_msg(self):
        return u'Не найден {0} с id = {1}'.format(self.target_obj_class.__name__, self.target_obj_id)

    def get_parent_nf_msg(self):
        return u'Не найден {0} с id = {1}'.format(self.parent_obj_class.__name__, self.parent_obj_id)

    def set_properties(self, action, data, check_val=True):
        for code, value in data.iteritems():
            if action.has_property(code, True):
                prop = action.get_property(code, True)
                try:
                    if check_val:
                        self.check_prop_value(prop, value)
                    action.set_prop_value(code, value)
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise

    # -----

    def find_org(self, org_code):
        org = get_org_by_org_code(org_code)
        if not org:
            raise ApiException(
                NOT_FOUND_ERROR,
                u'Не найдена организация по коду {0}'.format(org_code)
            )
        return org

    def find_org_structure(self, org_str_code):
        if org_str_code is None:
            return None
        org_str = get_org_structure_by_code(org_str_code)
        if not org_str:
            raise ApiException(
                NOT_FOUND_ERROR,
                u'Не найдено подразделение по коду {0}'.format(org_str_code)
            )
        return org_str

    @staticmethod
    def from_org_rb(org):
        if org is None:
            return None
        return org.regionalCode

    @staticmethod
    def from_org_struct_rb(os):
        if os is None:
            return None
        return os.regionalCode

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
        mkb = db.session.query(MKB).filter(MKB.regionalCode == code, MKB.deleted == 0).first()
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
            # if rb_name not in ('rbBloodType', 'rbDocumentType', 'rbPolicyType'):
            self._check_rb_value(rb_name, value['code'])

    def _check_rb_value(self, rb_name, value_code, field_name='regionalCode'):
        # if rb_name == 'rbBloodType':
        #     field_name = 'code'
        # elif rb_name in ('rbDocumentType', 'rbPolicyType'):
        #     field_name = 'TFOMSCode'
        if not check_rb_value_exists(rb_name, value_code, field_name):
            raise ApiException(
                VALIDATION_ERROR,
                u'Не найдено значение по коду `{0}` в справочнике {1}'.format(value_code, rb_name)
            )

    @staticmethod
    def to_rb(code):  # vesta
        return {
            'code': code
        } if code is not None else None

    @staticmethod
    def from_rb(rb):
        if rb is None:
            return None
        return rb.regionalCode if hasattr(rb, 'regionalCode') else rb['code']  # vesta

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
        return rb.regionalCode if hasattr(rb, 'regionalCode') else rb['code']  # vesta

    @staticmethod
    def to_blood_type_rb(code):
        if code is None:
            return None
        bt = db.session.query(rbBloodType).filter(rbBloodType.regionalCode == code).first()
        if not bt:
            raise ApiException(400, u'Не найдена группа крови по коду "{0}"'.format(code))
        return safe_dict(bt)

    @staticmethod
    def from_blood_type_rb(rb):
        if rb is None:
            return None
        return rb.regionalCode if hasattr(rb, 'regionalCode') else rb['code']  # vesta

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
        if not enum.is_valid():
            raise ApiException(
                NOT_FOUND_ERROR,
                u'В справочнике "%s" запись с кодом "%s" не найдена' % (
                    enum_model.__name__, value)
            )
        return enum if enum.is_valid() else None

    def rb(self, regionalCode, rb_model, rb_code_field='regionalCode'):
        id_, code, name = self.rb_validate(rb_model, regionalCode, rb_code_field)
        return code and {'code': code, 'id': id_, 'name': name} or None

    @staticmethod
    def arr(rb_func, codes, rb_name, rb_code_field='regionalCode'):
        return map(lambda code: rb_func(code, rb_name, rb_code_field), codes)

    @staticmethod
    def rb_validate(rb_model, code, rb_code_field):
        row_id = row_code = name = None
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
                    name = rb.get('name')
                    row_code = rb.get('code')
            else:
                field = getattr(rb_model, rb_code_field)
                rb = rb_model.query.filter(
                    field == code
                ).first()
                row_id = rb.id if rb else None
                name = getattr(rb, 'name', None) if rb else None
                row_code = getattr(rb, 'code', None) if rb else None
            if not row_id:
                raise ApiException(
                    NOT_FOUND_ERROR,
                    u'В справочнике "%s" запись с кодом "%s" не найдена' % (
                        rb_model if isinstance(rb_model, basestring) else rb_model.__name__,
                        code,
                    )
                )
        return row_id, row_code, name

    def mapping_part(self, part_map, data, res):
        if not data:
            return
        for k, v in part_map.items():
            val = data.get(v['attr'], v.get('default'))
            if v['rb']:
                rb_code_field = v.get('rb_code_field', 'regionalCode')
                if v['is_vector']:
                    res[k] = self.arr(self.rb, val, v['rb'], rb_code_field)
                else:
                    res[k] = self.rb(val, v['rb'], rb_code_field)
            else:
                res[k] = val

    def _represent_part(self, part, data):
        res = {}
        for k, v in part.items():
            if k not in data:
                # поле удалено в БД
                continue
            if v['rb']:
                rb_code_field = v.get('rb_code_field', 'regionalCode')
                vesta_rb_code_field = v.get('rb_code_field', 'code')  # vesta
                if v['is_vector']:
                    if isinstance(v['rb'], basestring):
                        val = map(lambda x: x[vesta_rb_code_field], data[k])
                    else:
                        val = map(lambda x: getattr(x, rb_code_field), data[k])
                else:
                    if isinstance(v['rb'], basestring):
                        val = data[k] and data[k][vesta_rb_code_field]
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
                u'check_duplicate нужно использовать вместе с "external_id"'
            )
        q = self._find_target_obj_query().join(
            ActionIdentification
        ).join(rbAccountingSystem).filter(
            ActionIdentification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if target_obj_exist:
            raise ApiException(ALREADY_PRESENT_ERROR, u'%s уже существует' %
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
            ActionIdentification.external_system_id == self.external_system.id,
        ).delete()


class CheckupsXForm(ExternalXForm):

    @abstractmethod
    def set_pcard(self):
        pass

    def reevaluate_data(self):
        pass

    @abstractmethod
    def generate_measures(self):
        pass

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
                    'mkbs': flt_mkbs,
                    'additional_info': diag_data.get('additional_info')
                })
        return flt_mis_diags

    def update_diagnoses_system(self, diags_list, old_action_data):
        """Из расчета, что на (пере)сохранение могут прийти данные с любыми изменениями,
        ломающими систему диагнозов (серьезная смена даты осмотра, изменение набора диагнозов),
        попытаться изменить состояние диагнозов в текущем, прошлом и следующем осмотрах.

        Редактирование осуществляется за 2 прохода: при первом проходе изменяется состояние
        диагнозов по данным осмотра с еще неизмененной датой начала, при втором - с уже обновленной.
        """
        series_len = len(diags_list)
        for series_number, diag_group in enumerate(diags_list):
            refresh_in_series = series_number != series_len - 1

            diag_type = diag_group['diag_type']
            diag_data = diag_group['diag_data']
            mis_diags = self._get_filtered_mis_diags(diag_data)

            # recalc for previous state
            if not self.new and self.target_obj.begDate != old_action_data['begDate']:
                t_beg_date = self.target_obj.begDate
                self.target_obj.begDate = old_action_data['begDate']
                t_end_date = self.target_obj.endDate
                self.target_obj.endDate = old_action_data['endDate']
                t_person = self.target_obj.person
                self.target_obj.person = old_action_data['person']
                self.ais.refresh(self.target_obj)
                self.ais.close_previous()
                self.ais.flush()

                diag_sys = DiagnosesSystemManager.get_for_inspection(
                    self.target_obj, diag_type, self.ais, refresh_in_series)
                fut_interval = DateTimeInterval(t_beg_date, t_end_date)
                diag_sys.refresh_with_old_state(mis_diags, fut_interval)
                new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()

                create_or_update_diagnoses(self.target_obj, new_diagnoses)
                for d in new_oa_diagnoses:
                    create_or_update_diagnoses(d['action'], [d['data']])
                db.session.add_all(changed_diagnoses)
                db.session.flush()
                self.target_obj.begDate = t_beg_date
                self.target_obj.endDate = t_end_date
                self.target_obj.person = t_person

            self.ais.refresh(self.target_obj)
            self.ais.close_previous()
            self.ais.flush()

            diag_sys = DiagnosesSystemManager.get_for_inspection(
                self.target_obj, diag_type, self.ais, refresh_in_series)
            diag_sys.refresh_with(mis_diags)
            new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()
            create_or_update_diagnoses(self.target_obj, new_diagnoses)
            for d in new_oa_diagnoses:
                create_or_update_diagnoses(d['action'], [d['data']])
            db.session.add_all(changed_diagnoses)

            db.session.flush()

    def delete_diagnoses(self):
        """Изменить систему диагнозов после удаления осмотра
        """
        diag_sys = DiagnosesSystemManager.get_for_inspection(
            self.target_obj, None, self.ais)
        diag_sys.refresh_with_deletion()
        new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(self.target_obj, new_diagnoses)
        for d in new_oa_diagnoses:
            create_or_update_diagnoses(d['action'], [d['data']])
        db.session.add_all(changed_diagnoses)


class PregnancyCheckupsXForm(CheckupsXForm):

    def __init__(self, *args, **kwargs):
        super(PregnancyCheckupsXForm, self).__init__(*args, **kwargs)
        self.ais = AdjasentInspectionsState(inspections_span_flatcodes, self.new)

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

    @staticmethod
    def get_mkb_list(diagnosis_list):
        return map(lambda x: x['MKB'], diagnosis_list)

    @staticmethod
    def get_diagnosis_additional_info(diagnosis_list):
        return {d.pop('MKB'): d for d in diagnosis_list}


class GynecologyCheckupsXForm(CheckupsXForm):

    def __init__(self, *args, **kwargs):
        super(GynecologyCheckupsXForm, self).__init__(*args, **kwargs)
        self.ais = AdjasentInspectionsState((risar_gyn_checkup_flat_code,), self.new)

    def set_pcard(self):
        if not self.pcard:
            if not self.parent_obj:
                self.find_parent_obj(self.parent_obj_id)
            event = self.parent_obj
            self.pcard = GynecologicCard.get_for_event(event)

    def generate_measures(self):
        em_ctrl = EventMeasureController()
        em_ctrl.regenerate_gyn(self.target_obj)


class MeasuresResultsXForm(ExternalXForm):
    __metaclass__ = ABCMeta

    diagnosis_codes = None

    def __init__(self, *args, **kwargs):
        super(MeasuresResultsXForm, self).__init__(*args, **kwargs)
        self.em = None
        self.person = None
        self.organisation = None
        self.ais = AdjasentInspectionsState(inspections_span_flatcodes, self.new)

    @abstractmethod
    def prepare_params(self, data):
        pass

    @abstractmethod
    def get_properties_data(self, data):
        return data

    def get_em(self):
        return self.em

    def set_pcard(self):
        if not self.pcard:
            if not self.parent_obj:
                self.find_parent_obj(self.parent_obj_id)
            event = self.parent_obj
            self.pcard = PregnancyCard.get_for_event(event)

    def reevaluate_data(self):
        self.set_pcard()
        self.pcard.reevaluate_card_attrs()

    def update_measure_data(self, data):
        status = data.get('status')
        if status:
            self.em.status = self.rb_validate(rbMeasureStatus, status, 'regionalCode')[0]

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
            self.em = self.get_event_measure(
                data.get('measure_id'),
                data['measure_type_code'],
                data.get('checkup_date'),
                data.get('checkup_date'),
            )
            self.create_action()
        else:
            self.find_target_obj(self.target_obj_id)
            self.em = EventMeasure.query.filter(
                EventMeasure.resultAction_id == self.target_obj_id
            ).one()

        mr_data = self.get_data_for_diags(data)

        properties_data = self.get_properties_data(data)
        self.set_result_action_data(properties_data)
        self.set_properties(self.target_obj, properties_data)
        self.update_measure_data(data)
        self.save_external_data()
        if self.changes_diagnoses_system():
            self.update_diagnoses_system(mr_data)

    def update_diagnoses_system(self, mr_data):
        """
        См. CheckupsXForm.update_diagnoses_system
        """
        measure_mkbs = mr_data['new_mkbs']
        new_diags = [dict(kind='associated', mkbs=measure_mkbs)]

        # recalc for previous state
        if not self.new and mr_data['changed']:
            target = self.modify_target(mr_data['old_beg_date'], mr_data['old_person'])
            self.ais.refresh(self.target_obj)

            diag_sys = DiagnosesSystemManager.get_for_measure_result(
                target, 'final', self.get_measure_type().value, self.ais)
            fut_interval = DateTimeInterval(mr_data['new_beg_date'], mr_data['new_beg_date'])
            diag_sys.refresh_with_measure_result_old_state(new_diags, fut_interval)
            new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()

            create_or_update_diagnoses(self.target_obj, new_diagnoses)
            for d in new_oa_diagnoses:
                create_or_update_diagnoses(d['action'], [d['data']])
            db.session.add_all(changed_diagnoses)
            db.session.flush()
            self.modify_target(mr_data['new_beg_date'], mr_data['new_person'])

        self.ais.refresh(self.target_obj)

        diag_sys = DiagnosesSystemManager.get_for_measure_result(
            self.target_obj, 'final', self.get_measure_type().value, self.ais)
        diag_sys.refresh_with_measure_result(new_diags)
        new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(self.target_obj, new_diagnoses)
        for d in new_oa_diagnoses:
            create_or_update_diagnoses(d['action'], [d['data']])
        db.session.add_all(changed_diagnoses)
        db.session.flush()

    def delete_diagnoses(self):
        """Изменить систему диагнозов после удаления результата мероприятия
        """
        diag_sys = DiagnosesSystemManager.get_for_measure_result(
            self.target_obj, None, self.get_measure_type().value, self.ais)
        diag_sys.refresh_with_deletion()
        new_diagnoses, changed_diagnoses, new_oa_diagnoses = diag_sys.get_result()
        create_or_update_diagnoses(self.target_obj, new_diagnoses)
        for d in new_oa_diagnoses:
            create_or_update_diagnoses(d['action'], [d['data']])

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
        measure = Measure.query.filter(Measure.regionalCode == measure_code).first()
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

    def set_result_action_data(self, data):
        pass

    def delete_target_obj(self):
        self.find_target_obj(self.target_obj_id)
        self.ais.refresh(self.target_obj)
        self.delete_diagnoses()

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
