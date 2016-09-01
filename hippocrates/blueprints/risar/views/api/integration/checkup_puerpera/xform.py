#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.represent import represent_checkup_puerpera
from blueprints.risar.lib.utils import get_action_by_id
from blueprints.risar.risar_config import puerpera_inspection_code
from blueprints.risar.views.api.integration.checkup_puerpera.schemas import \
    CheckupPuerperaSchema
from blueprints.risar.views.api.integration.xform import CheckupsXForm
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
            ActionType.flatCode == puerpera_inspection_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        self.find_parent_obj(self.parent_obj_id)
        self.set_pcard()
        self.target_obj = get_action_by_id(self.target_obj_id, self.parent_obj, puerpera_inspection_code, True)
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

        diag_data = []
        if 'diagnosis' in data:
            diag_data.append({
                'kind': 'main',
                'mkbs': [data['diagnosis']]
            })
        old_action_data = {
            'begDate': self.target_obj.begDate,
            'endDate': self.target_obj.endDate,
            'person': self.target_obj.person
        }
        res.update({
            '_data_for_diags': {
                'diags_list': [
                    {
                        'diag_data': diag_data,
                        'diag_type': 'final'
                    }
                ],
                'old_action_data': old_action_data
            }
        })

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups_puerpera.api_0_checkup_puerpera

        beg_date = safe_datetime(safe_date(data.get('beg_date', None)))
        data_for_diags = data.pop('_data_for_diags')

        action = self.target_obj

        action.begDate = beg_date
        action.setPerson = self.person
        action.person = self.person
        self.ais.refresh(self.target_obj)
        self.ais.set_cur_enddate()

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        self.update_diagnoses_system(data_for_diags['diags_list'], data_for_diags['old_action_data'])

        self.ais.close_previous()

    def reevaluate_data(self):
        pass

    def delete_target_obj(self):
        self.find_parent_obj(self.parent_obj_id)
        self.target_obj = get_action_by_id(self.target_obj_id, self.parent_obj, puerpera_inspection_code, True)
        self.ais.refresh(self.target_obj)
        self.delete_diagnoses()

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0,
        ).update({'deleted': 1})

        self.delete_external_data()

        # todo: при удалении последнего осмотра наверно нужно открывать предпослений
        # if self.ais.left: ...

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
