#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.risar_config import general_specialists_checkups
from hippocrates.blueprints.risar.views.api.integration.specialists_checkup.schemas import \
    SpecialistsCheckupSchema
from hippocrates.blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from hippocrates.blueprints.risar.lib.expert.em_diagnosis import get_measure_result_mkbs
from nemesis.lib.utils import safe_date, safe_datetime
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event
from nemesis.models.enums import MeasureType


class SpecialistsCheckupXForm(SpecialistsCheckupSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action
    flat_code = 'general_checkup'

    diagnosis_codes = ('MainDiagnosis', )

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
                'new_mkbs': [new_data.get('diagnosis'), ] if 'diagnosis' in new_data else [],
                'old_beg_date': safe_datetime(self.target_obj['CheckupDate'].value),
                'new_beg_date': safe_datetime(new_data['checkup_date']),
                'old_person': self.target_obj['Doctor'].value,
                'new_person': self.find_doctor(new_data.get('doctor_code'), new_data.get('lpu_code'))
            }
            res['changed'] = any(res[o] != res[n] for o, n in (
                ('old_mkbs', 'new_mkbs'), ('old_beg_date', 'new_beg_date'), ('old_person', 'new_person')
            ))
            return res
        else:
            return {
                'new_mkbs': [new_data.get('diagnosis'), ] if 'diagnosis' in new_data else [],
            }

    def modify_target(self, new_date, new_person):
        self.target_obj.begDate = self.target_obj.endDate = safe_datetime(new_date)
        self.target_obj.person = new_person
        return self.target_obj

    def get_measure_type(self):
        return MeasureType(MeasureType.checkup[0])

    def set_result_action_data(self, data):
        self.target_obj.begDate = self.target_obj.endDate = safe_datetime(data['CheckupDate'])
        self.target_obj.person = data['Doctor']

    def prepare_params(self, data):
        self.person = self.find_doctor(data.get('doctor_code'), data.get('lpu_code'))

    def get_properties_data(self, data):
        return {
            'CheckupDate': safe_date(data.get('checkup_date')),
            'Doctor': self.person,
            'LPUCheckup': self.person.organisation,
            'MainDiagnosis': self.to_mkb_rb(data.get('diagnosis')),
            'Results': data.get('results', '').replace('\r\n', '<br>'),
        }

    def as_json(self):
        an_props = self.target_obj.propsByCode
        res = {
            'external_id': self.external_id,
            'result_action_id': self.target_obj.id,
            'measure_id': self.em.id,
            'measure_status': self.em.literal_status,
            'measure_type_code': self.em.measure.code,
            'checkup_date': an_props['CheckupDate'].value,
            'lpu_code': self.person.organisation and self.person.organisation.regionalCode or '',
            'doctor_code': self.person.regionalCode,
            'diagnosis': an_props['MainDiagnosis'].value,
            'results': an_props['Results'].value if 'Results' in an_props else ''
        }
        return res
