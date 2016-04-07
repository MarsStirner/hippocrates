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
from blueprints.risar.models.risar import ExternalAction
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.views.api.integration.checkup_obs_first.schemas import \
    CheckupObsFirstSchema
from nemesis.lib.apiutils import ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.lib.vesta import Vesta
from nemesis.models.actions import ActionType, Action
from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind
from nemesis.models.event import Event
from nemesis.models.exists import MKB, rbAccountingSystem
from nemesis.systemwide import db

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
        self.external_id = None

        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).get()

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
            ExternalAction
        ).join(rbAccountingSystem).filter(
            ExternalAction.external_id == self.external_id,
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
        q = ExternalAction.query.join(rbAccountingSystem).filter(
            ExternalAction.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
            ExternalAction.action_id == self.target_obj_id,
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
        self.save_external_data()

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
        gi = data.get('general_info', {})
        res.update({
            'beg_date': gi.get('date', None),
            'person': {
                'id': None,
                'hospital': gi.get('hospital', None),
                'doctor': gi.get('doctor', None),
            },
            'height': gi.get('height', None),
            'weight': gi.get('weight', None),
        })

    def mapping_somatic_status(self, data, res):
        ss = data.get('somatic_status', {})
        res.update({
            'state': self.rb(ss.get('state', None), 'rbRisarState'),
            'subcutaneous_fat': self.rb(ss.get('subcutaneous_fat', None), 'rbRisarSubcutaneous_Fat'),
            # 'tongue': self.arr(self.rb, somatic_status.get('tongue', None), 'rbRisarTongue'),
            'tongue': self.rb(ss.get('tongue', None), 'rbRisarTongue'),
            'complaints': self.arr(self.rb, ss.get('complaints', None), 'rbRisarComplaints'),
            'skin': self.arr(self.rb, ss.get('skin', None), 'rbRisarSkin'),
            'lymph': self.arr(self.rb, ss.get('lymph', None), 'rbRisarLymph'),
            'breast': self.arr(self.rb, ss.get('breast', None), 'rbRisarBreast'),
            'heart_tones': self.arr(self.rb, ss.get('heart_tones', None), 'rbRisarHeart_Tones'),
            'pulse': self.arr(self.rb, ss.get('pulse', None), 'rbRisarPulse'),
            'nipples': self.arr(self.rb, ss.get('nipples', None), 'rbRisarNipples'),
            'mouth': self.rb(ss.get('mouth', None), 'rbRisarMouth'),
            'breathe': self.arr(self.rb, ss.get('respiratory', None), 'rbRisarBreathe'),
            'stomach': self.arr(self.rb, ss.get('abdomen', None), 'rbRisarStomach'),
            'liver': self.arr(self.rb, ss.get('liver', None), 'rbRisarLiver'),
            'urinoexcretory': self.arr(self.rb, ss.get('urinoexcretory', None), 'rbRisarUrinoexcretory'),
            'ad_right_high': ss.get('ad_right_high', None),
            'ad_left_high': ss.get('ad_left_high', None),
            'ad_right_low': ss.get('ad_right_low', None),
            'ad_left_low': ss.get('ad_left_low', None),
            'edema': ss.get('edema', None),
            'vein': self.rb(ss.get('veins', None), 'rbRisarVein'),
            'bowel_and_bladder_habits': ss.get('bowel_and_bladder_habits', None),
            'heart_rate': ss.get('heart_rate', None),
        })

    def mapping_obstetric_status(self, data, res):
        os = data.get('obstetric_status', {})
        res.update({
            'MikHHor': os.get('horiz_diagonal', None),
            'MikhVert': os.get('vert_diagonal', None),
            'abdominal': os.get('abdominal_circumference', None),
            'fundal_height': os.get('fundal_height', None),
            'metra_state': self.rb(os.get('uterus_state', None), 'rbRisarMetra_State'),
            'DsSP': os.get('dssp', None),
            'DsCr': os.get('dscr', None),
            'DsTr': os.get('dstr', None),
            'CExt': os.get('cext', None),
            'CDiag': os.get('cdiag', None),
            'CVera': os.get('cvera', None),
            'soloviev_index': os.get('soloviev_index', None),
            'pelvis_narrowness': self.rb(os.get('pelvis_narrowness', None), 'rbRisarPelvis_Narrowness'),
            'pelvis_form': self.rb(os.get('pelvis_form', None), 'rbRisarPelvis_Form'),
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
                    # 'heartbeat': self.arr(self.rb, fetus.get('fetus_heartbeat', []), 'rbRisarFetus_Heartbeat'),
                    'heartbeat': self.rb(fetus.get('fetus_heartbeat', None), 'rbRisarFetus_Heartbeat'),
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

    def get_diagnoses(self, data, form_data):
        # Прислали новый код МКБ, и не прислали старый - старый диагноз закрыли, новый открыли.
        # если тот же МКБ пришел не как осложнение, а как сопутствующий, это смена вида
        # если в списке диагнозов из МИС придут дубли кодов МКБ - отсекать лишние
        # Если код МКБ в основном заболевании - игнорировать (отсекать) его в осложнениях и сопутствующих.
        # Если код МКБ в осложнении - отсекать его в сопутствующих
        # если два раза в одной группе (в осложнениях, например) - оставлять один

        medical_report = data.get('medical_report', {})
        action = self.target_obj
        card = PregnancyCard.get_for_event(action.event)
        diagnostics = card.get_client_diagnostics(action.begDate,
                                                  action.endDate)
        db_diags = {}
        for diagnostic in diagnostics:
            diagnosis = diagnostic.diagnosis
            diagKind_code = list(Action_Diagnosis.query.join(
                rbDiagnosisKind,
            ).filter(
                Action_Diagnosis.action == action,
                Action_Diagnosis.diagnosis == diagnosis,
            ).values(rbDiagnosisKind.code))[0][0]
            db_diags[diagnostic.MKB] = {
                'diagnosis_id': diagnosis.id,
                'diagKind_code': diagKind_code,
            }

        mis_diags = {}
        for risar_key, mis_key, is_array, default in (
            ('main', 'diagnosis_osn', False, None),
            ('complication', 'diagnosis_osl', True, []),
            ('associated', 'diagnosis_sop', True, []),
        ):
            mkb_list = medical_report.get(mis_key, default)
            if not is_array:
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
                'diagnostic_changed': False,
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
                kind_changed = mis_diag.get('diagKind_code') != db_diag.get('diagKind_code')
                diagnosis_type = self.rb(mis_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = None
                add_diag_data()
            elif not db_diag and mis_diag:
                # открыть
                kind_changed = False
                diagnosis_type = self.rb(mis_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = None
                add_diag_data()
            elif db_diag and not mis_diag:
                # закрыть
                # нельзя закрывать, если используется в документах своего типа с бОльшей датой
                if self.is_using_by_next_checkups(db_diag['diagnosis_id'], action):
                    continue
                kind_changed = False
                diagnosis_type = self.rb(db_diag.get('diagKind_code'), rbDiagnosisKind)
                end_date = form_data.get('beg_date')
                add_diag_data()
        return res

    @staticmethod
    def is_using_by_next_checkups(diagnosis_id, action):
        q = Action_Diagnosis.query.join(Action).filter(
            Action_Diagnosis.diagnosis_id == diagnosis_id,
            Action.begDate >= action.begDate,
            Action.actionType == action.actionType,
            Action.deleted == 0,
        )
        return db.session.query(q.exists()).scalar()

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

    def close_diags(self):
        # Роман:
        # сначала найти открытые диагнозы пациента (это будут просто диагнозы без типа), затем среди них определить какие являются основными,
        # осложнениями и пр. - это значит, что Diagnosis связывается с осмотром через Action_Diagnosis, где указывается его тип, т.е. диагноз
        # пациента в рамках какого-то осмотра будет иметь определенный тип. *Все открытые диагнозы пациента, для которых не указан тип в связке
        # с экшеном являются сопотствующими неявно*.
        # тут надо понять логику работы с диагнозами (четкого описания нет), после этого нужно доработать механизм диагнозов - из того, что я знаю,
        # сейчас проблема как раз с определением тех диагнозов пациента, которые относятся к текущему случаю. Для этого нужно исправлять запрос,
        # выбирающий диагнозы по датам с учетом дат Event'а. После этого уже интегрировать.

        # Action_Diagnosis
        # Diagnostic.query.filter(Diagnosis.id == diagnosis)
        # q = Diagnosis.query.filter(Diagnosis.client == self.parent_obj.client)
        # q.update({'deleted': 1})
        raise

    def as_json(self):
        return {
            "exam_obs_id": self.target_obj.id,
        }

    def delete_target_obj(self):
        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()
        # В методе удаления осмотра с плодами ничего не делать, у action.deleted = 1
        # self.delete_fetuses()

        self.target_obj_class.query.filter(
            self.target_obj_class.event == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

    def delete_fetuses(self):
        FetusState.query.filter(
            FetusState.delete == 0,
            FetusState.action_id == self.target_obj_id
        ).delete()

    def save_external_data(self):
        if self.new:
            external_action = ExternalAction(
                action=self.target_obj,
                action_id=self.target_obj_id,
                external_id=self.external_id,
                external_system=self.external_system,
                external_system_id=self.external_system.id,
            )
            db.session.add(external_action)
