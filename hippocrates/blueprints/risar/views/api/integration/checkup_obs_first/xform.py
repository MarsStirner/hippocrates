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
from nemesis.lib.utils import safe_datetime
from nemesis.models.actions import ActionType, Action
from nemesis.models.diagnosis import Diagnosis
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

    def __init__(self, api_version):
        self.version = 0
        self.schema = None
        self.new = False
        self.parent_obj_id = None
        self.target_obj_id = None
        self.parent_obj = None
        self.target_obj = None
        self.parent_obj_class = None
        self.target_obj_class = None

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
            target_obj_exist = db.session.query(
                literal(True)
            ).filter(q.exists()).scalar()
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


class CheckupObsFirstXForm(CheckupObsFirstSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == first_inspection_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        form_data = self.mapping_as_form(data)
        self.delete_diags()
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
        general_info = data.get('general_info', None)
        if general_info:
            res.update({
                'beg_date': general_info.date,
                # 'person': general_info.hospital,
                # 'person': general_info.doctor,
                'height': general_info.height,
                'weight': general_info.weight,
            })

    def mapping_somatic_status(self, data, res):
        somatic_status = data.get('somatic_status', None)
        if somatic_status:
            res.update({
                'state': self.rb(somatic_status.state),
                'subcutaneous_fat': self.rb(somatic_status.subcutaneous_fat),
                'tongue': map(self.rb, somatic_status.tongue),
                'complaints': map(self.rb, somatic_status.complaints),
                'skin': map(self.rb, somatic_status.skin),
                'lymph': map(self.rb, somatic_status.lymph),
                'breast': map(self.rb, somatic_status.breast),
                'heart_tones': map(self.rb, somatic_status.heart_tones),
                'pulse': map(self.rb, somatic_status.pulse),
                'nipples': map(self.rb, somatic_status.nipples),
                'mouth': self.rb(somatic_status.mouth),
                'breathe': map(self.rb, somatic_status.respiratory),
                'stomach': map(self.rb, somatic_status.abdomen),
                'liver': map(self.rb, somatic_status.liver),
                'urinoexcretory': map(self.rb, somatic_status.urinoexcretory),
                'ad_right_high': somatic_status.ad_right_high,
                'ad_left_high': somatic_status.ad_left_high,
                'ad_right_low': somatic_status.ad_right_low,
                'ad_left_low': somatic_status.ad_left_low,
                'edema': somatic_status.edema,
                'vein': somatic_status.veins,
                'bowel_and_bladder_habits': self.rb(somatic_status.bowel_and_bladder_habits),
                'heart_rate': somatic_status.heart_rate,
            })

    def mapping_obstetric_status(self, data, res):
        obstetric_status = data.get('obstetric_status', None)
        if obstetric_status:
            res.update({
                'MikHHor': obstetric_status.horiz_diagonal,
                'MikhVert': obstetric_status.vert_diagonal,
                'abdominal': obstetric_status.abdominal_circumference,
                'fundal_height': obstetric_status.fundal_height,
                'metra_state': self.rb(obstetric_status.uterus_state),
                'DsSP': obstetric_status.dssp,
                'DsCr': obstetric_status.dscr,
                'DsTr': obstetric_status.dstr,
                'CExt': obstetric_status.cext,
                'CDiag': obstetric_status.cdiag,
                'CVera': obstetric_status.cvera,
                'soloviev_index': obstetric_status.soloviev_index,
                'pelvis_narrowness': self.rb(obstetric_status.pelvis_narrowness),
                'pelvis_form': self.rb(obstetric_status.pelvis_form),
            })

    def mapping_fetus(self, data, res):
        fetus_list = data.get('fetus', None)
        fetus_q = FetusState.query.filter(FetusState.action == self.target_obj)
        fetus_ids = fetus_q.values(FetusState.id)
        # Обновляем записи как попало (нет ID), лишние удаляем, новые создаем
        for i in xrange(max(len(fetus_ids), len(fetus_list))):
            deleted = 1
            fetus = None
            fetus_id = None
            if i < len(fetus_ids):
                deleted = 0
                fetus_id = fetus_ids[i]
            if i < len(fetus_list):
                fetus = fetus_list[i]
            res.setdefault('fetuses', []).append({
                'deleted': deleted,
                'state': {
                    'id': fetus_id,
                    'position': fetus and self.rb(fetus.fetus_lie),
                    'position_2': fetus and self.rb(fetus.fetus_position),
                    'type': fetus and self.rb(fetus.fetus_type),
                    'presenting_part': fetus and self.rb(fetus.fetus_presentation),
                    'heartbeat': fetus and map(self.rb, fetus.fetus_heartbeat),
                    'heart_rate': fetus and fetus.fetus_heart_rate,
                },
            })

    def mapping_vaginal_examination(self, data, res):
        vaginal_examination = data.get('vaginal_examination', None)
        if vaginal_examination:
            res.update({
                'vagina': self.rb(vaginal_examination.vagina),
                'cervix': self.rb(vaginal_examination.cervix),
                'cervix_length': self.rb(vaginal_examination.cervix_length),
                'cervical_canal': self.rb(vaginal_examination.cervical_canal),
                'cervix_consistency': self.rb(vaginal_examination.cervix_consistency),
                'cervix_position': self.rb(vaginal_examination.cervix_position),
                'cervix_maturity': self.rb(vaginal_examination.cervix_maturity),
                'body_of_womb': map(self.rb, vaginal_examination.body_of_uterus),
                'appendages': self.rb(vaginal_examination.adnexa),
                'features': vaginal_examination.specialities,
                'externalia': vaginal_examination.vulva,
                'parametrium': vaginal_examination.parametrium,
                'vagina_secretion': vaginal_examination.vaginal_smear,
                'cervical_canal_secretion': vaginal_examination.cervical_canal_smear,
                'onco_smear': vaginal_examination.onco_smear,
                'urethra_secretion': vaginal_examination.urethra_smear,
            })

    def mapping_medical_report(self, data, res):
        medical_report = data.get('medical_report', None)
        if medical_report:
            res.update({
                'pregnancy_week': medical_report.pregnancy_week,
                'next_date': medical_report.next_visit_date,
                'pregnancy_continuation': medical_report.pregnancy_continuation,
                'pregnancy_continuation_refusal': medical_report.abortion_refusal,
                'craft': self.rb(medical_report.working_conditions),
                'recommendations': medical_report.recommendations,
                'notes': medical_report.notes,
            })
        for risar_key, mis_key, is_array in (
            ('main', 'diagnosis_osn', False),
            ('associated', 'diagnosis_sop', True),
            ('complication', 'diagnosis_osl', True),
        ):
            mkb = getattr(medical_report, mis_key)
            if mkb:
                res.setdefault('diagnoses', []).append({
                    'diagnostic': {
                        'mkb': mkb,
                        'kind_changed': True,
                        'set_date': res.beg_date,
                    },
                    'diagnosis_types': {
                        'final': is_array and map(self.rb, risar_key) or
                                 self.rb(risar_key),
                    },
                })

    @staticmethod
    def rb(code):
        return {'code': code}

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups.api_0_checkup

        event_id = self.parent_obj_id
        checkup_id = self.target_obj_id
        flat_code = first_inspection_code

        beg_date = safe_datetime(data.pop('beg_date', None))
        person = data.pop('person', None)
        diagnoses = data.pop('diagnoses', None)
        fetuses = data.pop('fetuses', None)

        event = Event.query.get(event_id)
        card = PregnancyCard.get_for_event(event)
        action = get_action_by_id(checkup_id, event, flat_code, True)

        if not checkup_id:
            close_open_checkups(event_id)

        action.begDate = beg_date

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        create_or_update_diagnoses(action, diagnoses)
        create_or_update_fetuses(action, fetuses)

        card.reevaluate_card_attrs()

        self.target_obj = action

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
