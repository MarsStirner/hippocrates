#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_checkup_puerpera
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, close_open_checkups_puerpera
from hippocrates.blueprints.risar.risar_config import puerpera_inspection_flat_code
from hippocrates.blueprints.risar.views.api.integration.checkup_puerpera.schemas import \
    CheckupPuerperaSchema
from hippocrates.blueprints.risar.views.api.integration.xform import CheckupsXForm
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.actions import ActionType, Action
from nemesis.models.event import Event


class CheckupPuerperaXForm(CheckupPuerperaSchema, CheckupsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    FIELDS_MAP = {
        'beg_date': {'attr': 'date', 'default': None, 'rb': None, 'is_vector': False},
        'deliveryDate': {'attr': 'date_of_childbirth', 'default': None, 'rb': None, 'is_vector': False},
        'timeAfterDelivery': {'attr': 'time_since_childbirth', 'default': None, 'rb': None, 'is_vector': False},
        'complaints': {'attr': 'complaints', 'default': None, 'rb': 'rbRisarComplaints_Puerpera', 'is_vector': True},
        'nipples': {'attr': 'nipples', 'default': None, 'rb': 'rbRisarNipples_Puerpera', 'is_vector': True},
        'secretion': {'attr': 'secretion', 'default': None, 'rb': 'rbRisarSecretion_Puerpera', 'is_vector': True},
        'breast': {'attr': 'breast', 'default': None, 'rb': 'rbRisarBreast_Puerpera', 'is_vector': True},
        'lactation': {'attr': 'lactation', 'default': None, 'rb': 'rbRisarLactation_Puerpera', 'is_vector': False},
        'uterus': {'attr': 'uterus', 'default': None, 'rb': 'rbRisarUterus_Puerpera', 'is_vector': False},
        'scar': {'attr': 'scar', 'default': None, 'rb': 'rbRisarScar_Puerpera', 'is_vector': False},
        'state': {'attr': 'state', 'default': None, 'rb': 'rbRisarState', 'is_vector': False},
        'ad_right_high': {'attr': 'ad_right_high', 'default': None, 'rb': None, 'is_vector': False},
        'ad_left_high': {'attr': 'ad_left_high', 'default': None, 'rb': None, 'is_vector': False},
        'ad_right_low': {'attr': 'ad_right_low', 'default': None, 'rb': None, 'is_vector': False},
        'ad_left_low': {'attr': 'ad_left_low', 'default': None, 'rb': None, 'is_vector': False},
        'vein': {'attr': 'veins', 'default': None, 'rb': 'rbRisarVein', 'is_vector': False},
        'contraception': {'attr': 'contraception_recommendations', 'default': None, 'rb': 'rbRisarContraception_Puerpera', 'is_vector': False},
        'treatment': {'attr': 'treatment', 'default': None, 'rb': None, 'is_vector': False},
        'recomendations': {'attr': 'recommendations', 'default': None, 'rb': None, 'is_vector': False},
    }

    DIAG_KINDS_MAP = {
        'main': {'attr': 'diagnosis', 'default': None, 'is_vector': False, 'level': 1},
        # 'complication': {'attr': 'diagnosis_osl', 'default': [], 'is_vector': True, 'level': 2},
        # 'associated': {'attr': 'diagnosis_sop', 'default': [], 'is_vector': True, 'level': 3},
    }

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == puerpera_inspection_flat_code,
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
        self.mapping_fields(data, res)
        return res

    def mapping_fields(self, data, res):
        self.mapping_part(self.FIELDS_MAP, data, res)

        self.person = self.find_doctor(data.get('doctor'), data.get('hospital'))
        res['person'] = self.person.__json__()
        res.update({
            'get_diagnoses_func': lambda: self.get_diagnoses((
                (data, self.DIAG_KINDS_MAP, 'final'),
            ), res.get('person'), res.get('beg_date'))
        })

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups_puerpera.api_0_pregnancy_checkup_puerpera

        event_id = self.parent_obj_id
        event = self.parent_obj
        checkup_id = self.target_obj_id
        flat_code = puerpera_inspection_flat_code

        beg_date = safe_datetime(safe_date(data.get('beg_date', None)))
        get_diagnoses_func = data.pop('get_diagnoses_func')

        action = get_action_by_id(checkup_id, event, flat_code, True)

        self.target_obj = action
        diagnoses = get_diagnoses_func()

        if not checkup_id:
            close_open_checkups_puerpera(event_id)

        action.begDate = beg_date
        action.setPerson = self.person
        action.person = self.person

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        create_or_update_diagnoses(action, diagnoses)

    def reevaluate_data(self):
        from hippocrates.blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
        reevaluate_card_fill_rate_all(self.pcard)

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

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

        self.delete_external_data()

    def as_json(self):
        data = represent_pregnancy_checkup_puerpera(self.target_obj)
        res = {
            "exam_puerpera_id": self.target_obj.id,
            "external_id": self.external_id,
        }
        res.update(self._represent_checkup(data))
        return res

    def _represent_checkup(self, data):
        res = self._represent_part(self.FIELDS_MAP, data)

        person = data.get('person')
        res.update({
            'hospital': person.organisation and person.organisation.TFOMSCode or '',
            'doctor': person.regionalCode,
        })
        res.update(self._represent_diagnoses(data))
        return res

    def _represent_diagnoses(self, data):
        res = {}

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
