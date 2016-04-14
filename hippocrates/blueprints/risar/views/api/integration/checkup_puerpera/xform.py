#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.represent import represent_checkup_puerpera
from blueprints.risar.lib.utils import get_action_by_id, close_open_checkups_puerpera
from blueprints.risar.risar_config import puerpera_inspection_code
from blueprints.risar.views.api.integration.checkup_puerpera.schemas import \
    CheckupPuerperaSchema
from blueprints.risar.views.api.integration.xform import CheckupsXForm
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.actions import ActionType, Action
from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind
from nemesis.models.event import Event
from nemesis.models.exists import MKB
from nemesis.systemwide import db


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

    def __init__(self, *a, **kw):
        super(CheckupPuerperaXForm, self).__init__(*a, **kw)
        self.card = None

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == puerpera_inspection_code,
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
        self.mapping_fields(data, res)
        return res

    def mapping_fields(self, data, res):
        self.mapping_part(self.FIELDS_MAP, data, res)

        person_id = self.find_doctor(data.get('doctor'), data.get('hospital')).id
        res.update({
            'person': {
                'id': person_id,
            },
            'get_diagnoses_func': lambda: self.get_diagnoses(data, res),
        })

    def get_diagnoses(self, data, form_data):
        # Прислали новый код МКБ, и не прислали старый - старый диагноз закрыли, новый открыли.
        # если тот же МКБ пришел не как осложнение, а как сопутствующий, это смена вида
        # если в списке диагнозов из МИС придут дубли кодов МКБ - отсекать лишние
        # Если код МКБ в основном заболевании - игнорировать (отсекать) его в осложнениях и сопутствующих.
        # Если код МКБ в осложнении - отсекать его в сопутствующих
        # если два раза в одной группе (в осложнениях, например) - оставлять один

        action = self.target_obj
        card = PregnancyCard.get_for_event(action.event)
        diagnostics = card.get_client_diagnostics(action.begDate,
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
            mkb_list = data.get(mis_key, default)
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

    @staticmethod
    def is_using_by_next_checkups(diagnosis_id, action):
        q = Action_Diagnosis.query.join(Action).filter(
            Action_Diagnosis.diagnosis_id == diagnosis_id,
            Action.begDate >= action.begDate,
            Action.actionType == action.actionType,
            Action.id != action.id,
            Action.deleted == 0,
        )
        return db.session.query(q.exists()).scalar()

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups_puerpera.api_0_checkup_puerpera

        event_id = self.parent_obj_id
        checkup_id = self.target_obj_id
        flat_code = puerpera_inspection_code

        beg_date = safe_datetime(safe_date(data.get('beg_date', None)))
        get_diagnoses_func = data.pop('get_diagnoses_func')

        event = Event.query.get(event_id)
        card = PregnancyCard.get_for_event(event)
        action = get_action_by_id(checkup_id, event, flat_code, True)

        self.target_obj = action
        diagnoses = get_diagnoses_func()

        if not checkup_id:
            close_open_checkups_puerpera(event_id)

        action.begDate = beg_date

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        create_or_update_diagnoses(action, diagnoses)

        self.card = card

    def reevaluate_data(self):
        from blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
        reevaluate_card_fill_rate_all(self.card)

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

    def as_json(self):
        data = represent_checkup_puerpera(self.target_obj, False)
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
