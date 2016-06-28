#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.risar_config import general_specialists_checkups
from blueprints.risar.views.api.integration.specialists_checkup.schemas import \
    SpecialistsCheckupSchema
from blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from nemesis.lib.utils import safe_int, safe_date
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event


class SpecialistsCheckupXForm(SpecialistsCheckupSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.context == general_specialists_checkups,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def prepare_params(self, data):
        self.em = self.get_event_measure(
            data.get('measure_id'),
            data['measure_type_code'],
            data.get('checkup_date'),
            data.get('checkup_date'),
        )
        self.person = self.find_doctor(data.get('doctor_code'), data.get('lpu_code'))

    def get_properties_data(self, data):
        return {
            'CheckupDate': safe_date(data.get('checkup_date')),
            'Doctor': self.person,
            'LPUCheckup': self.person.organisation,
            'MainDiagnosis': self.to_mkb_rb(data.get('diagnosis')),
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
            'lpu_code': self.person.organisation and self.person.organisation.TFOMSCode or '',
            'doctor_code': self.person.regionalCode,
            'diagnosis': an_props['MainDiagnosis'].value,
        }
        return res