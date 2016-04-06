#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging

import functools

import jsonschema
from abc import ABCMeta, abstractmethod

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.fetus import create_or_update_fetuses
from blueprints.risar.lib.utils import get_action_by_id, close_open_checkups
from blueprints.risar.models.fetus import FetusState
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.views.api.integration.checkup_obs_first.schemas import \
    CheckupObsFirstSchema
from nemesis.lib.apiutils import ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.actions import ActionType, Action
from nemesis.models.diagnosis import Diagnosis, Action_Diagnosis, \
    rbDiagnosisKind
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

    def _find_parent_obj_query(self):
        return self.parent_obj_class.query.filter(
            self.parent_obj_class.id == self.parent_obj_id
        )

    @abstractmethod
    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        external_id = data.get('external_id', None)
        q = self._find_target_obj_query().filter(
            self.target_obj_class.external_id == external_id
        )
        target_obj_exist = db.session.query(
            literal(True)
        ).filter(q.exists()).scalar()
        if not target_obj_exist:
            raise ApiException(ALREADY_PRESENT_ERROR, u'%s already exist' %
                               self.target_obj_class.__name__)

    def rb(self, code, rb_name):
        self.rb_validate(rb_name, code)
        return code and {'code': code} or None

    @staticmethod
    def arr(rb_func, codes, rb_name):
        return map(lambda code: rb_func(code, rb_name), codes)

    def rb_validate(self, rb_name, param):
        pass


class CheckupObsFirstXForm(CheckupObsFirstSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == first_inspection_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        form_data = self.mapping_as_form(data)
        self.update_form(form_data)

    def mapping_as_form(self, data):
        res = {}
        self.mapping_general_info(data, res)
        self.mapping_somatic_status(data, res)
        self.mapping_obstetric_status(data, res)
        self.mapping_fetus(data, res)
        self.mapping_vaginal_examination(data, res)
        self.mapping_medical_report(data, res)
        return res

    def mapping_general_info(self, data, res):
        general_info = data.get('general_info', {})
        res.update({
            'beg_date': general_info.get('date', None),
            'person': {
                'id': None,
                'hospital': general_info.get('hospital', None),
                'doctor': general_info.get('doctor', None),
            },
            'height': general_info.get('height', None),
            'weight': general_info.get('weight', None),
        })

    def mapping_somatic_status(self, data, res):
        somatic_status = data.get('somatic_status', {})
        res.update({
            'state': self.rb(somatic_status.get('state', None), 'rbRisarState'),
            'subcutaneous_fat': self.rb(somatic_status.get('subcutaneous_fat', None), 'rbRisarSubcutaneous_Fat'),
            'tongue': self.arr(self.rb, somatic_status.get('tongue', None), 'rbRisarTongue'),
            'complaints': self.arr(self.rb, somatic_status.get('complaints', None), 'rbRisarComplaints'),
            'skin': self.arr(self.rb, somatic_status.get('skin', None), 'rbRisarSkin'),
            'lymph': self.arr(self.rb, somatic_status.get('lymph', None), 'rbRisarLymph'),
            'breast': self.arr(self.rb, somatic_status.get('breast', None), 'rbRisarBreast'),
            'heart_tones': self.arr(self.rb, somatic_status.get('heart_tones', None), 'rbRisarHeart_Tones'),
            'pulse': self.arr(self.rb, somatic_status.get('pulse', None), 'rbRisarPulse'),
            'nipples': self.arr(self.rb, somatic_status.get('nipples', None), 'rbRisarNipples'),
            'mouth': self.rb(somatic_status.get('mouth', None), 'rbRisarMouth'),
            'breathe': self.arr(self.rb, somatic_status.get('respiratory', None), 'rbRisarBreathe'),
            'stomach': self.arr(self.rb, somatic_status.get('abdomen', None), 'rbRisarStomach'),
            'liver': self.arr(self.rb, somatic_status.get('liver', None), 'rbRisarLiver'),
            'urinoexcretory': self.arr(self.rb, somatic_status.get('urinoexcretory', None), 'rbRisarUrinoexcretory'),
            'ad_right_high': somatic_status.get('ad_right_high', None),
            'ad_left_high': somatic_status.get('ad_left_high', None),
            'ad_right_low': somatic_status.get('ad_right_low', None),
            'ad_left_low': somatic_status.get('ad_left_low', None),
            'edema': somatic_status.get('edema', None),
            'vein': self.rb(somatic_status.get('veins', None), 'rbRisarVein'),
            'bowel_and_bladder_habits': somatic_status.get('bowel_and_bladder_habits', None),
            'heart_rate': somatic_status.get('heart_rate', None),
        })

    def mapping_obstetric_status(self, data, res):
        obstetric_status = data.get('obstetric_status', {})
        res.update({
            'MikHHor': obstetric_status.get('horiz_diagonal', None),
            'MikhVert': obstetric_status.get('vert_diagonal', None),
            'abdominal': obstetric_status.get('abdominal_circumference', None),
            'fundal_height': obstetric_status.get('fundal_height', None),
            'metra_state': self.rb(obstetric_status.get('uterus_state', None), 'rbRisarMetra_State'),
            'DsSP': obstetric_status.get('dssp', None),
            'DsCr': obstetric_status.get('dscr', None),
            'DsTr': obstetric_status.get('dstr', None),
            'CExt': obstetric_status.get('cext', None),
            'CDiag': obstetric_status.get('cdiag', None),
            'CVera': obstetric_status.get('cvera', None),
            'soloviev_index': obstetric_status.get('soloviev_index', None),
            'pelvis_narrowness': self.rb(obstetric_status.get('pelvis_narrowness', None), 'rbRisarPelvis_Narrowness'),
            'pelvis_form': self.rb(obstetric_status.get('pelvis_form', None), 'rbRisarPelvis_Form'),
        })

    def mapping_fetus(self, data, res):
        fetus_list = data.get('fetus', [])
        fetus_q = FetusState.query.filter(FetusState.action_id == self.target_obj_id)
        fetus_ids = tuple(fetus_q.values(FetusState.id))
        # Обновляем записи как попало (нет ID), лишние удаляем, новые создаем
        for i in xrange(max(len(fetus_ids), len(fetus_list))):
            deleted = 1
            fetus = {}
            fetus_id = None
            if i < len(fetus_ids):
                fetus_id = fetus_ids[i][0]
            if i < len(fetus_list):
                deleted = 0
                fetus = fetus_list[i]
            res.setdefault('fetuses', []).append({
                'deleted': deleted,
                'state': {
                    'id': fetus_id,
                    'position': self.rb(fetus.get('fetus_lie', None), 'rbRisarFetus_Position'),
                    'position_2': self.rb(fetus.get('fetus_position', None), 'rbRisarFetus_Position_2'),
                    'type': self.rb(fetus.get('fetus_type', None), 'rbRisarFetus_Type'),
                    'presenting_part': self.rb(fetus.get('fetus_presentation', None), 'rbRisarPresenting_Part'),
                    'heartbeat': self.arr(self.rb, fetus.get('fetus_heartbeat', None), 'rbRisarFetus_Heartbeat'),
                    'heart_rate': fetus.get('fetus_heart_rate', None),
                },
            })

    def mapping_vaginal_examination(self, data, res):
        vaginal_examination = data.get('vaginal_examination', {})
        res.update({
            'vagina': self.rb(vaginal_examination.get('vagina', None), 'rbRisarVagina'),
            'cervix': self.rb(vaginal_examination.get('cervix', None), 'rbRisarCervix'),
            'cervix_length': self.rb(vaginal_examination.get('cervix_length', None), 'rbRisarCervix_Length'),
            'cervical_canal': self.rb(vaginal_examination.get('cervical_canal', None), 'rbRisarCervical_Canal'),
            'cervix_consistency': self.rb(vaginal_examination.get('cervix_consistency', None), 'rbRisarCervix_Consistency'),
            'cervix_position': self.rb(vaginal_examination.get('cervix_position', None), 'rbRisarCervix_Position'),
            'cervix_maturity': self.rb(vaginal_examination.get('cervix_maturity', None), 'rbRisarCervix_Maturity'),
            'body_of_womb': self.arr(self.rb, vaginal_examination.get('body_of_uterus', []), 'rbRisarBody_Of_Womb'),
            'appendages': self.rb(vaginal_examination.get('adnexa', None), 'rbRisarAppendages'),
            'features': vaginal_examination.get('specialities', None),
            'externalia': vaginal_examination.get('vulva', None),
            # 'parametrium': self.arr(self.rb, vaginal_examination.get('parametrium', []), '...'),
            'parametrium': self.rb(vaginal_examination.get('parametrium', None), '...'),
            'vagina_secretion': vaginal_examination.get('vaginal_smear', None),
            'cervical_canal_secretion': vaginal_examination.get('cervical_canal_smear', None),
            'onco_smear': vaginal_examination.get('onco_smear', None),
            'urethra_secretion': vaginal_examination.get('urethra_smear', None),
        })

    def mapping_medical_report(self, data, res):
        medical_report = data.get('medical_report', {})
        res.update({
            'pregnancy_week': medical_report.get('pregnancy_week', None),
            'next_date': medical_report.get('next_visit_date', None),
            'pregnancy_continuation': medical_report.get('pregnancy_continuation', None),
            'pregnancy_continuation_refusal': medical_report.get('abortion_refusal', None),
            'craft': self.rb(medical_report.get('working_conditions', None), 'rbRisarCraft'),
            'recommendations': medical_report.get('recommendations', None),
            'notes': medical_report.get('notes', None),
            'get_diagnoses_func': lambda: self.get_diagnoses(data, res),
        })

    def get_diagnoses(self, data, data_res):
        medical_report = data.get('medical_report', {})
        action = self.target_obj
        card = PregnancyCard.get_for_event(action.event)
        diagnostics = card.get_client_diagnostics(action.begDate,
                                                  action.endDate)
        db_diags = []
        for diagnostic in diagnostics:
            diagnosis = diagnostic.diagnosis
            diagKind_code = list(Action_Diagnosis.query.join(rbDiagnosisKind).filter(
                Action_Diagnosis.action == action,
                Action_Diagnosis.diagnosis == diagnosis,
            ).values(rbDiagnosisKind.code))[0]
            db_diags.append({
                'diagnosis_id': diagnosis.id,
                'diagKind_code': diagKind_code,
                'mkb_code': diagnostic.MKB,
            })

        mis_diags = []
        for risar_key, mis_key, is_array, default in (
            ('main', 'diagnosis_osn', False, None),
            ('associated', 'diagnosis_sop', True, []),
            ('complication', 'diagnosis_osl', True, []),
        ):
            mkb_list = medical_report.get(mis_key, default)
            if not is_array:
                mkb_list = mkb_list and [mkb_list] or []
            for mkb in mkb_list:
                mis_diags.append({
                    'diagKind_code': risar_key,
                    'mkb_code': mkb,
                })

        res = []
        # todo: удаление должно быть реализовано для интерфеса
        for i in xrange(max(len(db_diags), len(mis_diags))):
            deleted = 1
            db_diag = None
            mis_diag = None
            if i < len(db_diags):
                db_diag = db_diags[i]
            if i < len(mis_diags):
                deleted = 0
                mis_diag = mis_diags[i]

            res.append({
                'id': db_diag.get('diagnosis_id'),
                'deleted': deleted,
                'kind_changed': mis_diag.get('diagKind_code') != db_diag.get('diagKind_code'),
                'diagnostic_changed': mis_diag.get('mkb_code') != db_diag.get('mkb_code'),
                'diagnostic': {
                    'mkb': self.rb(mis_diag.get('mkb_code'), 'MKB'),
                },
                'diagnosis_types': {
                    'final': self.rb(mis_diag.get('diagKind_code'), 'rbDiagnosisKind'),
                },
                'person': data_res.get('person'),
                'set_date': data_res.get('beg_date'),
                'end_date': None,
            })
        return res

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups.api_0_checkup

        event_id = self.parent_obj_id
        checkup_id = self.target_obj_id
        flat_code = first_inspection_code

        beg_date = safe_datetime(safe_date(data.get('beg_date', None)))
        person = data.pop('person', None)
        get_diagnoses_func = data.pop('get_diagnoses_func')
        fetuses = data.pop('fetuses', None)

        event = Event.query.get(event_id)
        card = PregnancyCard.get_for_event(event)
        action = get_action_by_id(checkup_id, event, flat_code, True)

        self.target_obj = action
        diagnoses = get_diagnoses_func()

        if not checkup_id:
            close_open_checkups(event_id)

        action.begDate = beg_date

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        create_or_update_diagnoses(action, diagnoses)
        create_or_update_fetuses(action, fetuses)

        card.reevaluate_card_attrs()

    def delete_diags(self):
        # нужно сначала разобраться с диагнозами и их проблемами.

        # Роман:
        # сначала найти открытые диагнозы пациента (это будут просто диагнозы без типа), затем среди них определить какие являются основными,
        # осложнениями и пр. - это значит, что Diagnosis связывается с осмотром через Action_Diagnosis, где указывается его тип, т.е. диагноз
        # пациента в рамках какого-то осмотра будет иметь определенный тип. *Все открытые диагнозы пациента, для которых не указан тип в связке
        # с экшеном являются сопотствующими неявно*.
        # тут надо понять логику работы с диагнозами (четкого описания нет), после этого нужно доработать механизм диагнозов - из того, что я знаю,
        # сейчас проблема как раз с определением тех диагнозов пациента, которые относятся к текущему случаю. Для этого нужно исправлять запрос,
        # выбирающий диагнозы по датам с учетом дат Event'а. После этого уже интегрировать.

        # Action_Diagnosis
        # Diagnostic.filter(Diagnosis.id == diagnosis)
        # q = Diagnosis.query.filter(Diagnosis.client == self.parent_obj.client)
        # q.update({'deleted': 1})
        raise

    def as_json(self):
        return {
            "exam_obs_id": self.target_obj.id,
        }

    def delete_target_obj(self):
        self.delete_diags()
        self.delete_fetuses()

        self.target_obj_class.query.filter(
            self.target_obj_class.event == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

    def delete_fetuses(self):
        FetusState.query.filter(
            FetusState.delete == 0,
            FetusState.action_id == self.target_obj_id
        ).update({'deleted': 1})
