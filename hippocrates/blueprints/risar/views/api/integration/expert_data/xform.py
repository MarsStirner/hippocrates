#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.risar_config import puerpera_inspection_code
from blueprints.risar.views.api.integration.expert_data.schemas import \
    ExpertDataSchema
from blueprints.risar.views.api.integration.xform import XForm
from nemesis.models.event import Event, EventType


class ExpertDataXForm(ExpertDataSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Event
    parent_id_required = False

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

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(EventType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            EventType.flatCode == puerpera_inspection_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def reevaluate_data(self):
        from blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
        reevaluate_card_fill_rate_all(self.pcard)

    def as_json(self):
        data = represent_expert_data(self.target_obj, False)
        res = {
            "exam_puerpera_id": self.target_obj.id,
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
