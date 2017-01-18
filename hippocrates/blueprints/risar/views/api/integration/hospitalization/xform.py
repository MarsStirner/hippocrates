#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.risar_config import general_hospitalizations
from hippocrates.blueprints.risar.views.api.integration.hospitalization.schemas import \
    HospitalizationSchema
from hippocrates.blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from hippocrates.blueprints.risar.lib.expert.em_diagnosis import get_measure_result_mkbs
from nemesis.lib.utils import safe_int, safe_date, safe_datetime
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event
from nemesis.models.enums import MeasureType


class HospitalizationXForm(HospitalizationSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action
    flat_code = 'general_hospitalizations'

    diagnosis_codes = ('FinalDiagnosis', )

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            # ActionType.flatCode == self.flat_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def check_duplicate(self, data):
        self.external_id = data.get('external_id')

    def get_data_for_diags(self, new_data):
        if not self.new:
            old_mr_mkbs = get_measure_result_mkbs(self.target_obj, self.diagnosis_codes)
            res = {
                'old_mkbs': old_mr_mkbs,
                'new_mkbs': [new_data.get('diagnosis_out'), ] if 'diagnosis_out' in new_data else [],
                'old_beg_date': safe_datetime(self.target_obj['IssueDate'].value),
                'new_beg_date': safe_datetime(new_data['date_out']),
                'old_person': self.target_obj['Doctor'].value,
                'new_person': self.find_doctor(new_data.get('doctor'), new_data.get('hospital'))
            }
            res['changed'] = any(res[o] != res[n] for o, n in (
                ('old_mkbs', 'new_mkbs'), ('old_beg_date', 'new_beg_date'), ('old_person', 'new_person')
            ))
            return res
        else:
            return {
                'new_mkbs': [new_data.get('diagnosis_out'), ] if 'diagnosis_out' in new_data else [],
            }

    def modify_target(self, new_date, new_person):
        self.target_obj.begDate = self.target_obj.endDate = safe_datetime(new_date)
        self.target_obj.person = new_person
        return self.target_obj

    def get_measure_type(self):
        return MeasureType(MeasureType.hospitalization[0])

    def set_result_action_data(self, data):
        self.target_obj.begDate = self.target_obj.endDate = safe_datetime(data['IssueDate'])
        self.target_obj.person = data['Doctor']

    def prepare_params(self, data):
        self.find_parent_obj(self.parent_obj_id)
        data['measure_type_code'] = '0065'
        self.person = self.find_doctor(data.get('doctor'), data.get('hospital'))

    def get_properties_data(self, data):
        return {
            'ReceiptDate': safe_date(data.get('date_in')),
            'IssueDate': safe_date(data.get('date_out')),
            'Doctor': self.person,
            'PregnancyDuration': safe_int(data.get('pregnancy_week')),
            'DirectionDiagnosis': self.to_mkb_rb(data.get('diagnosis_in')),
            'FinalDiagnosis': self.to_mkb_rb(data.get('diagnosis_out')),
        }

    def as_json(self):
        an_props = self.target_obj.propsByCode
        res = {
            'external_id': self.external_id,
            'result_action_id': self.target_obj.id,
            'measure_id': self.em.id,
            'measure_status': self.em.literal_status,
            'date_in': an_props['ReceiptDate'].value,
            'date_out': an_props['IssueDate'].value,
            'hospital': self.person.organisation and self.person.organisation.regionalCode or '',
            'doctor': self.person.regionalCode,
            'pregnancy_week': an_props['PregnancyDuration'].value,
            'diagnosis_in': an_props['DirectionDiagnosis'].value,
            'diagnosis_out': an_props['FinalDiagnosis'].value,
        }
        return res
