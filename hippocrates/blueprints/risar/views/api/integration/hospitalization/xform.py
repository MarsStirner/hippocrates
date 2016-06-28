#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.risar_config import general_hospitalizations
from blueprints.risar.views.api.integration.hospitalization.schemas import \
    HospitalizationSchema
from blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from nemesis.lib.utils import safe_int, safe_date
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event


class HospitalizationXForm(HospitalizationSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.context == general_hospitalizations,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def prepare_params(self, data):
        self.find_parent_obj(self.parent_obj_id)
        self.em = self.get_event_measure(
            data.get('measure_id'),
            '0065',
            data.get('date_in'),
            data.get('date_out'),
        )
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
            'hospitalization_id': self.target_obj.id,
            'measure_id': self.em.id,
            'measure_status': self.em.literal_status,
            'date_in': an_props['ReceiptDate'].value,
            'date_out': an_props['IssueDate'].value,
            'hospital': self.person.organisation and self.person.organisation.TFOMSCode or '',
            'doctor': self.person.regionalCode,
            'pregnancy_week': an_props['PregnancyDuration'].value,
            'diagnosis_in': an_props['DirectionDiagnosis'].value,
            'diagnosis_out': an_props['FinalDiagnosis'].value,
        }
        return res