#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.fetus import create_or_update_fetuses
from blueprints.risar.lib.represent import represent_checkup
from blueprints.risar.lib.utils import get_action_by_id, close_open_checkups, \
    notify_checkup_changes
from blueprints.risar.models.fetus import RisarFetusState
from blueprints.risar.risar_config import pc_inspection_code
from blueprints.risar.views.api.integration.checkup_pc.schemas import \
    CheckupPCSchema
from blueprints.risar.views.api.integration.xform import CheckupsXForm
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.actions import ActionType, Action
from nemesis.models.event import Event


class CheckupPCXForm(CheckupPCSchema, CheckupsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    GENERAL_MAP = {
        'beg_date': {'attr': 'date', 'default': None, 'rb': None, 'is_vector': False},
        'height': {'attr': 'height', 'default': None, 'rb': None, 'is_vector': False},
        'weight': {'attr': 'weight', 'default': None, 'rb': None, 'is_vector': False},
    }

    SOMATIC_MAP = {
        'state': {'attr': 'state', 'default': None, 'rb': 'rbRisarState', 'is_vector': False},
        'subcutaneous_fat': {'attr': 'subcutaneous_fat', 'default': None, 'rb': 'rbRisarSubcutaneous_Fat', 'is_vector': False},
        'tongue': {'attr': 'tongue', 'default': None, 'rb': 'rbRisarTongue', 'is_vector': True},
        'complaints': {'attr': 'complaints', 'default': None, 'rb': 'rbRisarComplaints', 'is_vector': True},
        'skin': {'attr': 'skin', 'default': None, 'rb': 'rbRisarSkin', 'is_vector': True},
        'lymph': {'attr': 'lymph', 'default': None, 'rb': 'rbRisarLymph', 'is_vector': True},
        'breast': {'attr': 'breast', 'default': None, 'rb': 'rbRisarBreast', 'is_vector': True},
        'heart_tones': {'attr': 'heart_tones', 'default': None, 'rb': 'rbRisarHeart_Tones', 'is_vector': True},
        'pulse': {'attr': 'pulse', 'default': None, 'rb': 'rbRisarPulse', 'is_vector': True},
        'nipples': {'attr': 'nipples', 'default': None, 'rb': 'rbRisarNipples', 'is_vector': True},
        'mouth': {'attr': 'mouth', 'default': None, 'rb': 'rbRisarMouth', 'is_vector': False},
        'breathe': {'attr': 'respiratory', 'default': None, 'rb': 'rbRisarBreathe', 'is_vector': True},
        'stomach': {'attr': 'abdomen', 'default': None, 'rb': 'rbRisarStomach', 'is_vector': True},
        'liver': {'attr': 'liver', 'default': None, 'rb': 'rbRisarLiver', 'is_vector': True},
        'urinoexcretory': {'attr': 'urinoexcretory', 'default': None, 'rb': 'rbRisarUrinoexcretory', 'is_vector': True},
        'ad_right_high': {'attr': 'ad_right_high', 'default': None, 'rb': None, 'is_vector': False},
        'ad_left_high': {'attr': 'ad_left_high', 'default': None, 'rb': None, 'is_vector': False},
        'ad_right_low': {'attr': 'ad_right_low', 'default': None, 'rb': None, 'is_vector': False},
        'ad_left_low': {'attr': 'ad_left_low', 'default': None, 'rb': None, 'is_vector': False},
        'edema': {'attr': 'edema', 'default': None, 'rb': None, 'is_vector': False},
        'vein': {'attr': 'veins', 'default': None, 'rb': 'rbRisarVein', 'is_vector': False},
        'bowel_and_bladder_habits': {'attr': 'bowel_and_bladder_habits', 'default': None, 'rb': None, 'is_vector': False},
        'heart_rate': {'attr': 'heart_rate', 'default': None, 'rb': None, 'is_vector': False},
    }

    OBSTETRIC_MAP = {
        'MikHHor': {'attr': 'horiz_diagonal', 'default': None, 'rb': None, 'is_vector': False},
        'MikhVert': {'attr': 'vert_diagonal', 'default': None, 'rb': None, 'is_vector': False},
        'abdominal': {'attr': 'abdominal_circumference', 'default': None, 'rb': None, 'is_vector': False},
        'fundal_height': {'attr': 'fundal_height', 'default': None, 'rb': None, 'is_vector': False},
        'metra_state': {'attr': 'uterus_state', 'default': None, 'rb': 'rbRisarMetra_State', 'is_vector': False},
        'DsSP': {'attr': 'dssp', 'default': None, 'rb': None, 'is_vector': False},
        'DsCr': {'attr': 'dscr', 'default': None, 'rb': None, 'is_vector': False},
        'DsTr': {'attr': 'dstr', 'default': None, 'rb': None, 'is_vector': False},
        'CExt': {'attr': 'cext', 'default': None, 'rb': None, 'is_vector': False},
        'CDiag': {'attr': 'cdiag', 'default': None, 'rb': None, 'is_vector': False},
        'CVera': {'attr': 'cvera', 'default': None, 'rb': None, 'is_vector': False},
        'soloviev_index': {'attr': 'soloviev_index', 'default': None, 'rb': None, 'is_vector': False},
        'pelvis_narrowness': {'attr': 'pelvis_narrowness', 'default': None, 'rb': 'rbRisarPelvis_Narrowness', 'is_vector': False},
        'pelvis_form': {'attr': 'pelvis_form', 'default': None, 'rb': 'rbRisarPelvis_Form', 'is_vector': False},
    }

    FETUS_MAP = {
        'position': {'attr': 'fetus_lie', 'default': None, 'rb': 'rbRisarFetus_Position', 'is_vector': False},
        'position_2': {'attr': 'fetus_position', 'default': None, 'rb': 'rbRisarFetus_Position_2', 'is_vector': False},
        'type': {'attr': 'fetus_type', 'default': None, 'rb': 'rbRisarFetus_Type', 'is_vector': False},
        'presenting_part': {'attr': 'fetus_presentation', 'default': None, 'rb': 'rbRisarPresenting_Part', 'is_vector': False},
        'heartbeat': {'attr': 'fetus_heartbeat', 'default': None, 'rb': 'rbRisarFetus_Heartbeat', 'is_vector': True},
        'heart_rate': {'attr': 'fetus_heart_rate', 'default': None, 'rb': None, 'is_vector': False},
    }

    VAGINAL_MAP = {
        'vagina': {'attr': 'vagina', 'default': None, 'rb': 'rbRisarVagina', 'is_vector': False},
        'cervix': {'attr': 'cervix', 'default': None, 'rb': 'rbRisarCervix', 'is_vector': False},
        'cervix_length': {'attr': 'cervix_length', 'default': None, 'rb': 'rbRisarCervix_Length', 'is_vector': False},
        'cervical_canal': {'attr': 'cervical_canal', 'default': None, 'rb': 'rbRisarCervical_Canal', 'is_vector': False},
        'cervix_consistency': {'attr': 'cervix_consistency', 'default': None, 'rb': 'rbRisarCervix_Consistency', 'is_vector': False},
        'cervix_position': {'attr': 'cervix_position', 'default': None, 'rb': 'rbRisarCervix_Position', 'is_vector': False},
        'cervix_maturity': {'attr': 'cervix_maturity', 'default': None, 'rb': 'rbRisarCervix_Maturity', 'is_vector': False},
        'body_of_womb': {'attr': 'body_of_uterus', 'default': [], 'rb': 'rbRisarBody_Of_Womb', 'is_vector': True},
        'appendages': {'attr': 'adnexa', 'default': None, 'rb': 'rbRisarAppendages', 'is_vector': False},
        'features': {'attr': 'specialities', 'default': None, 'rb': None, 'is_vector': False},
        'externalia': {'attr': 'vulva', 'default': None, 'rb': None, 'is_vector': False},
        # 'parametrium': {'attr': 'parametrium', 'default': None, 'rb': 'rbRisarParametrium', 'is_vector': True},
        'parametrium': {'attr': 'parametrium', 'default': None, 'rb': 'rbRisarParametrium', 'is_vector': False},
        'vagina_secretion': {'attr': 'vaginal_smear', 'default': None, 'rb': None, 'is_vector': False},
        'cervical_canal_secretion': {'attr': 'cervical_canal_smear', 'default': None, 'rb': None, 'is_vector': False},
        'onco_smear': {'attr': 'onco_smear', 'default': None, 'rb': None, 'is_vector': False},
        'urethra_secretion': {'attr': 'urethra_smear', 'default': None, 'rb': None, 'is_vector': False},
    }

    REPORT_MAP = {
        'pregnancy_week': {'attr': 'pregnancy_week', 'default': None, 'rb': None, 'is_vector': False},
        'next_date': {'attr': 'next_visit_date', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_continuation': {'attr': 'pregnancy_continuation', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_continuation_refusal': {'attr': 'abortion_refusal', 'default': None, 'rb': None, 'is_vector': False},
        'craft': {'attr': 'working_conditions', 'default': None, 'rb': 'rbRisarCraft', 'is_vector': False},
        'recommendations': {'attr': 'recommendations', 'default': None, 'rb': None, 'is_vector': False},
        'notes': {'attr': 'notes', 'default': None, 'rb': None, 'is_vector': False},
    }

    DIAG_KINDS_MAP = {
        'main': {'attr': 'diagnosis_osn', 'default': None, 'is_vector': False, 'level': 1},
        'complication': {'attr': 'diagnosis_osl', 'default': [], 'is_vector': True, 'level': 2},
        'associated': {'attr': 'diagnosis_sop', 'default': [], 'is_vector': True, 'level': 3},
    }

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == pc_inspection_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        self.find_parent_obj(self.parent_obj_id)
        self.set_pcard()
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
        self.mapping_part(self.GENERAL_MAP, gi, res)

        self.person = self.find_doctor(gi.get('doctor'), gi.get('hospital'))
        res['person'] = self.person.__json__()

    def mapping_somatic_status(self, data, res):
        ss = data.get('somatic_status', {})
        self.mapping_part(self.SOMATIC_MAP, ss, res)

    def mapping_obstetric_status(self, data, res):
        os = data.get('obstetric_status', {})
        self.mapping_part(self.OBSTETRIC_MAP, os, res)

    def mapping_fetus(self, data, res):
        fetus_list = data.get('fetus', [])
        fetus_q = RisarFetusState.query.filter(RisarFetusState.action_id == self.target_obj_id)
        fetus_ids = tuple(fetus_q.values(RisarFetusState.id))
        # Обновляем записи как попало (нет ID), лишние удаляем, новые создаем
        for i in xrange(max(len(fetus_ids), len(fetus_list))):
            deleted = 1
            fs = {}
            db_fetus_id = None
            if i < len(fetus_ids):
                db_fetus_id = fetus_ids[i][0]
            if i < len(fetus_list):
                deleted = 0
                fs = fetus_list[i]

            f_state = {}
            if db_fetus_id:
                f_state['id'] = db_fetus_id
            self.mapping_part(self.FETUS_MAP, fs, f_state)
            res.setdefault('fetuses', []).append({
                'deleted': deleted,
                'state': f_state,
            })

    def mapping_vaginal_examination(self, data, res):
        ve = data.get('vaginal_examination', {})
        self.mapping_part(self.VAGINAL_MAP, ve, res)

    def mapping_medical_report(self, data, res):
        mr = data.get('medical_report', {})
        self.mapping_part(self.REPORT_MAP, mr, res)

        res.update({
            'get_diagnoses_func': lambda: self.get_diagnoses((
                (mr, self.DIAG_KINDS_MAP, 'final'),
            ), res.get('person'), res.get('beg_date'))
        })

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups.api_0_checkup

        event_id = self.parent_obj_id
        event = self.parent_obj
        checkup_id = self.target_obj_id
        flat_code = pc_inspection_code

        beg_date = safe_datetime(safe_date(data.get('beg_date', None)))
        get_diagnoses_func = data.pop('get_diagnoses_func')
        fetuses = data.pop('fetuses', [])

        action = get_action_by_id(checkup_id, event, flat_code, True)

        self.target_obj = action
        diagnoses = get_diagnoses_func()

        if not checkup_id:
            close_open_checkups(event_id)

        self.set_pcard()
        notify_checkup_changes(self.pcard, action, data.get('pregnancy_continuation'))

        action.begDate = beg_date
        action.setPerson = self.person
        action.person = self.person

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        create_or_update_diagnoses(action, diagnoses)
        create_or_update_fetuses(action, fetuses)

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

    def delete_target_obj(self):
        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()
        # В методе удаления осмотра с плодами ничего не делать, у action.deleted = 1
        # self.delete_fetuses()
        # todo: при удалении последнего осмотра наверно нужно открывать предпослений

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

        self.delete_external_data()

    def delete_fetuses(self):
        RisarFetusState.query.filter(
            RisarFetusState.delete == 0,
            RisarFetusState.action_id == self.target_obj_id
        ).delete()

    def as_json(self):
        data = represent_checkup(self.target_obj, False)
        return {
            "exam_pc_id": self.target_obj.id,
            "external_id": self.external_id,
            "general_info": self._represent_general_info(data),
            "somatic_status": self._represent_somatic_status(data),
            "obstetric_status": self._represent_obstetric_status(data),
            "fetus": self._represent_fetus(data),
            "vaginal_examination": self._represent_vaginal_examination(data),
            "medical_report": self._represent_medical_report(data),
        }

    def _represent_general_info(self, data):
        res = self._represent_part(self.GENERAL_MAP, data)

        person = data.get('person')
        res.update({
            'hospital': person.organisation and person.organisation.TFOMSCode or '',
            'doctor': person.regionalCode,
        })
        return res

    def _represent_somatic_status(self, data):
        return self._represent_part(self.SOMATIC_MAP, data)

    def _represent_obstetric_status(self, data):
        return self._represent_part(self.OBSTETRIC_MAP, data)

    def _represent_fetus(self, data):
        fetus_list = data.get('fetuses', [])
        res = []
        for fs_data in fetus_list:
            fs = self._represent_part(self.FETUS_MAP, fs_data.get('state'))
            res.append(fs)
        return res

    def _represent_vaginal_examination(self, data):
        return self._represent_part(self.VAGINAL_MAP, data)

    def _represent_medical_report(self, data):
        res = self._represent_part(self.REPORT_MAP, data)

        diags_data = data.get('diagnoses')
        for dd in diags_data:
            if dd['end_date']:
                continue
            kind = self.DIAG_KINDS_MAP[dd['diagnosis_types']['final'].code]
            mkb_code = dd['diagnostic']['mkb'].DiagID
            if kind['is_vector']:
                res.setdefault(kind['attr'], []).append(mkb_code)
            else:
                res[kind['attr']] = mkb_code
        return res