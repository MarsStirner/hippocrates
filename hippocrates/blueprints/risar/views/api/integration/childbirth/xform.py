#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.epicrisis_children import create_or_update_newborns
from blueprints.risar.lib.represent import represent_epicrisis
from blueprints.risar.lib.utils import close_open_checkups, get_action
from blueprints.risar.models.risar import RisarEpicrisis_Children
from blueprints.risar.risar_config import risar_epicrisis
from blueprints.risar.views.api.integration.childbirth.schemas import \
    ChildbirthSchema
from blueprints.risar.views.api.integration.xform import CheckupsXForm, \
    ALREADY_PRESENT_ERROR
from nemesis.lib.apiutils import ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_time
from nemesis.models.actions import ActionType, Action
from nemesis.models.enums import Gender
from nemesis.models.event import Event
from nemesis.models.exists import MKB
from nemesis.systemwide import db


class ChildbirthXForm(ChildbirthSchema, CheckupsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action
    target_id_required = False

    GENERAL_MAP = {
        'arrival_date': {'attr': 'admission_date', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_duration': {'attr': 'pregnancy_duration', 'default': None, 'rb': None, 'is_vector': False},
        'delivery_date': {'attr': 'delivery_date', 'default': None, 'rb': None, 'is_vector': False},
        'delivery_time': {'attr': 'delivery_time', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_speciality': {'attr': 'pregnancy_speciality', 'default': None, 'rb': None, 'is_vector': False},
        'afterbirth_features': {'attr': 'postnatal_speciality', 'default': None, 'rb': None, 'is_vector': False},
        'help': {'attr': 'help', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_final': {'attr': 'pregnancy_final', 'default': None, 'rb': 'rbRisarPregnancy_Final', 'is_vector': False},
        'abort': {'attr': 'abortion', 'default': None, 'rb': 'rbRisarAbort', 'is_vector': False},
        'maternity_hosp_doctor': {'attr': 'maternity_hospital_doctor', 'default': None, 'rb': None, 'is_vector': False},
    }

    MOTHER_DEATH_MAP = {
        'reason_of_death': {'attr': 'reason_of_death', 'default': None, 'rb': None, 'is_vector': False},
        'death_date': {'attr': 'death_date', 'default': None, 'rb': None, 'is_vector': False},
        'death_time': {'attr': 'death_time', 'default': None, 'rb': None, 'is_vector': False},
        'control_expert_conclusion': {'attr': 'control_expert_conclusion', 'default': None, 'rb': None, 'is_vector': False},
    }

    COMPLICATIONS_MAP = {
        'delivery_waters': {'attr': 'delivery_waters', 'default': None, 'rb': 'rbRisarDelivery_Waters', 'is_vector': False},
        'pre_birth_delivery_waters': {'attr': 'pre_birth_delivery_waters', 'default': None, 'rb': None, 'is_vector': False},
        'weakness': {'attr': 'weakness', 'default': None, 'rb': 'rbRisarWeakness', 'is_vector': False},
        'meconium_colouring': {'attr': 'meconium_color', 'default': None, 'rb': None, 'is_vector': False},
        'patologicsl_preliminal_period': {'attr': 'pathological_preliminary_period', 'default': None, 'rb': None, 'is_vector': False},
        'labor_anomalies': {'attr': 'abnormalities_of_labor', 'default': None, 'rb': None, 'is_vector': False},
        'chorioamnionit': {'attr': 'chorioamnionitis', 'default': None, 'rb': None, 'is_vector': False},
        'perineal_tear': {'attr': 'perineal_tear', 'default': None, 'rb': 'rbPerinealTear', 'is_vector': False},
        'eclampsia': {'attr': 'eclampsia', 'default': None, 'rb': 'rbRisarEclampsia', 'is_vector': False},
        'funiculus': {'attr': 'funiculus', 'default': None, 'rb': 'rbRisarFuniculus', 'is_vector': False},
        'afterbirth': {'attr': 'afterbirth', 'default': None, 'rb': 'rbRisarAfterbirth', 'is_vector': False},
        'poor_blood': {'attr': 'anemia', 'default': None, 'rb': None, 'is_vector': False},
        'infections_during_birth': {'attr': 'infections_during_delivery', 'default': None, 'rb': None, 'is_vector': False},
        'infections_after_birth': {'attr': 'infections_after_delivery', 'default': None, 'rb': None, 'is_vector': False},
    }

    MANIPULATIONS_MAP = {
        'caul': {'attr': 'caul', 'default': None, 'rb': None, 'is_vector': False},
        'calfbed': {'attr': 'calfbed', 'default': None, 'rb': None, 'is_vector': False},
        'perineotomy': {'attr': 'perineotomy', 'default': None, 'rb': None, 'is_vector': False},
        'secundines': {'attr': 'secundines', 'default': None, 'rb': None, 'is_vector': False},
        'other_manipulations': {'attr': 'other_manipulations', 'default': None, 'rb': None, 'is_vector': False},
    }

    OPERATIONS_MAP = {
        'caesarean_section': {'attr': 'caesarean_section', 'default': None, 'rb': 'rbRisarCaesarean_Section', 'is_vector': False},
        'obstetrical_forceps': {'attr': 'obstetrical_forceps', 'default': None, 'rb': 'rbRisarObstetrical_Forceps', 'is_vector': False},
        'vacuum_extraction': {'attr': 'vacuum_extraction', 'default': None, 'rb': None, 'is_vector': False},
        'indication': {'attr': 'indication', 'default': None, 'rb': 'rbRisarIndication', 'is_vector': False},
        'specialities': {'attr': 'specialities', 'default': None, 'rb': None, 'is_vector': False},
        'anesthetization': {'attr': 'anesthetization', 'default': None, 'rb': 'rbRisarAnesthetization', 'is_vector': False},
        'hysterectomy': {'attr': 'hysterectomy', 'default': None, 'rb': 'rbRisarHysterectomy', 'is_vector': False},
        'operation_complication': {'attr': 'complications', 'default': [], 'rb': MKB, 'is_vector': True, 'rb_code_field': 'DiagID'},
        'embryotomy': {'attr': 'embryotomy', 'default': None, 'rb': None, 'is_vector': False},
    }

    KIDS_MAP = {
        'alive': {'attr': 'alive', 'default': None, 'rb': None, 'is_vector': False},
        'weight': {'attr': 'weight', 'default': None, 'rb': None, 'is_vector': False},
        'length': {'attr': 'length', 'default': None, 'rb': None, 'is_vector': False},
        'maturity_rate': {'attr': 'maturity_rate', 'default': None, 'rb': 'rbRisarMaturity_Rate', 'is_vector': False},
        'apgar_score_1': {'attr': 'apgar_score_1', 'default': None, 'rb': None, 'is_vector': False},
        'apgar_score_5': {'attr': 'apgar_score_5', 'default': None, 'rb': None, 'is_vector': False},
        'apgar_score_10': {'attr': 'apgar_score_10', 'default': None, 'rb': None, 'is_vector': False},
        'death_reasons': {'attr': 'death_reason', 'default': None, 'rb': None, 'is_vector': False},
        'diseases': {'attr': 'diseases', 'default': [], 'rb': MKB, 'is_vector': True, 'rb_code_field': 'DiagID'},
    }

    DIAG_KINDS_MAP = {
        'main': {'attr': 'diagnosis_osn', 'default': None, 'is_vector': False, 'level': 1},
        'complication': {'attr': 'diagnosis_osl', 'default': [], 'is_vector': True, 'level': 2},
        'associated': {'attr': 'diagnosis_sop', 'default': [], 'is_vector': True, 'level': 3},
    }

    PAT_DIAG_KINDS_MAP = {
        'main': {'attr': 'pat_diagnosis_osn', 'default': None, 'is_vector': False, 'level': 1},
        'complication': {'attr': 'pat_diagnosis_osl', 'default': [], 'is_vector': True, 'level': 2},
        'associated': {'attr': 'pat_diagnosis_sop', 'default': [], 'is_vector': True, 'level': 3},
    }

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == risar_epicrisis,
        )
        return res

    def check_external_id(self, data):
        pass

    def check_duplicate(self, data):
        q = self._find_target_obj_query()
        target_obj_exist = db.session.query(q.exists()).scalar()
        if target_obj_exist:
            raise ApiException(ALREADY_PRESENT_ERROR, u'%s already exist' %
                               self.target_obj_class.__name__)

    def update_target_obj(self, data):
        if not self.new:
            self.find_target_obj(self.target_obj_id)
        self.find_parent_obj(self.parent_obj_id)
        self.set_pcard()
        form_data = self.mapping_as_form(data)
        self.update_form(form_data)

    def mapping_as_form(self, data):
        res = {}
        self.mapping_general_info(data, res)
        self.mapping_mother_death(data, res)
        self.mapping_complications(data, res)
        self.mapping_manipulations(data, res)
        self.mapping_operations(data, res)
        self.mapping_kids(data, res)
        res['get_diagnoses_func'] = lambda: self.get_diagnoses((
            (data.get('general_info', {}), self.DIAG_KINDS_MAP, 'final'),
            (data.get('mother_death', {}), self.PAT_DIAG_KINDS_MAP, 'pathanatomical')
        ), res.get('person'), res.get('delivery_date'))
        return res

    def mapping_general_info(self, data, res):
        part = data.get('general_info', {})
        self.mapping_part(self.GENERAL_MAP, part, res)

        self.person = self.find_doctor(
            part.get('maternity_hospital_doctor'),
            part.get('maternity_hospital')
        )
        res['person'] = self.person.__json__()

        maternity_hospital = self.find_org(part.get('maternity_hospital'))
        curation_hospital = self.find_org(part.get('curation_hospital'))
        res.update({
            'LPU': maternity_hospital,
            'newborn_LPU': curation_hospital,
            'delivery_time': res.get('delivery_time') and safe_time(res.get('delivery_time')).isoformat(),
        })

    def mapping_mother_death(self, data, res):
        part = data.get('mother_death', {})
        self.mapping_part(self.MOTHER_DEATH_MAP, part, res)

        res.update({
            'death_time': res.get('death_time') and safe_time(res.get('death_time')).isoformat(),
        })

    def mapping_complications(self, data, res):
        part = data.get('complications', {})
        self.mapping_part(self.COMPLICATIONS_MAP, part, res)

    def mapping_manipulations(self, data, res):
        part = data.get('manipulations', {})
        self.mapping_part(self.MANIPULATIONS_MAP, part, res)

    def mapping_operations(self, data, res):
        part = data.get('operations', {})
        self.mapping_part(self.OPERATIONS_MAP, part, res)

    def mapping_kids(self, data, res):
        mis_kids_list = data.get('kids', [])
        db_kids_q = RisarEpicrisis_Children.query.filter(RisarEpicrisis_Children.action_id == self.target_obj_id)
        db_kids_ids = tuple(db_kids_q.values(RisarEpicrisis_Children.id))
        # Обновляем записи как попало (нет ID), лишние удаляем, новые создаем
        for i in xrange(max(len(db_kids_ids), len(mis_kids_list))):
            deleted = 1
            mis_child = {}
            db_child_id = None
            if i < len(db_kids_ids):
                db_child_id = db_kids_ids[i][0]
            if i < len(mis_kids_list):
                deleted = 0
                mis_child = mis_kids_list[i]

            nb_state = {'deleted': deleted}
            if db_child_id:
                nb_state['id'] = db_child_id
            if mis_child:
                self.mapping_part(self.KIDS_MAP, mis_child, nb_state)
                nb_state['sex'] = Gender(mis_child['sex']).__json__() if mis_child['sex'] is not None else None
                nb_state['date'] = mis_child['date'] if mis_child['alive'] else mis_child['death_date']
                nb_state['time'] = safe_time(mis_child['time'] if mis_child['alive'] else mis_child['death_time'])
            res.setdefault('newborn_inspections', []).append(nb_state)

    def update_form(self, data):
        # like blueprints.risar.views.api.epicrisis.api_0_chart_epicrisis

        event_id = self.parent_obj_id
        event = self.parent_obj
        get_diagnoses_func = data.pop('get_diagnoses_func')

        newborn_inspections = filter(None, data.pop('newborn_inspections', []))
        action = get_action(event, risar_epicrisis, True)
        self.target_obj = action
        diagnoses = get_diagnoses_func()
        action.setPerson = self.person
        action.person = self.person

        if not action.id:
            close_open_checkups(event_id)  # закрыть все незакрытые осмотры
        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value
        create_or_update_diagnoses(action, diagnoses)
        create_or_update_newborns(action, newborn_inspections)

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
        self.find_target_obj(self.target_obj_id)

        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()
        # В методе удаления осмотра с плодами ничего не делать, у action.deleted = 1
        # self.delete_newborns()
        # todo: при удалении последнего осмотра наверно нужно открывать предпослений

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

    def delete_newborns(self):
        RisarEpicrisis_Children.query.filter(
            RisarEpicrisis_Children.delete == 0,
            RisarEpicrisis_Children.action_id == self.target_obj_id
        ).delete()

    def as_json(self):
        data = represent_epicrisis(self.parent_obj, self.target_obj)
        return {
            "childbirth_id": self.target_obj.id,
            "general_info": self._represent_general_info(data),
            "mother_death": self._represent_mother_death(data),
            "complications": self._represent_complications(data),
            "manipulations": self._represent_manipulations(data),
            "operations": self._represent_operations(data),
            "kids": self._represent_kids(data),
        }

    def _represent_general_info(self, data):
        res = self._represent_part(self.GENERAL_MAP, data)

        lpu = data.get('LPU')
        newborn_lpu = data.get('newborn_LPU')
        res.update({
            'maternity_hospital': lpu and lpu.TFOMSCode,
            'curation_hospital': newborn_lpu and newborn_lpu.TFOMSCode,
            'delivery_time': self.safe_time_format(res.get('delivery_time'), '%H:%M'),
        })

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

    def _represent_mother_death(self, data):
        res = self._represent_part(self.MOTHER_DEATH_MAP, data)

        res.update({
            'death': bool(data.get('death_date')),
            'death_time': self.safe_time_format(res.get('death_time'), '%H:%M'),
        })

        diags_data = data.get('diagnoses')
        for dd in diags_data:
            if dd['end_date']:
                continue
            kind = self.PAT_DIAG_KINDS_MAP[dd['diagnosis_types']['pathanatomical'].code]
            mkb_code = dd['diagnostic']['mkb'].DiagID
            if kind['is_vector']:
                res.setdefault(kind['attr'], []).append(mkb_code)
            else:
                res[kind['attr']] = mkb_code
        return res

    def _represent_complications(self, data):
        return self._represent_part(self.COMPLICATIONS_MAP, data)

    def _represent_manipulations(self, data):
        return self._represent_part(self.MANIPULATIONS_MAP, data)

    def _represent_operations(self, data):
        return self._represent_part(self.OPERATIONS_MAP, data)

    def _represent_kids(self, data):
        newborns_list = data.get('newborn_inspections', [])
        res = []
        for nb_data in newborns_list:
            nb = self._represent_part(self.KIDS_MAP, nb_data)
            nb['sex'] = nb_data['sex'].value if nb_data['sex'] is not None else None
            nb['date' if nb_data['alive'] else 'death_date'] = nb_data.get('date')
            nb['time' if nb_data['alive'] else 'death_time'] = self.safe_time_format(nb_data.get('time'), '%H:%M')
            res.append(nb)
        return res
