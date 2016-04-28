#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.risar_config import general_results
from blueprints.risar.views.api.integration.research.schemas import \
    ResearchSchema
from blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from nemesis.lib.utils import safe_int, safe_date
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event


class ResearchXForm(ResearchSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.context == general_results,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def prepare_params(self, data):
        self.em = self.get_event_measure(
            data['measure_id'],
            data['measure_type_code'],
            data.get('realization_date'),
            data.get('realization_date'),
        )
        self.person = self.find_doctor(data.get('doctor_code'), data.get('lpu_code'))

    def get_properties_data(self, data):
        return {
            'Results': data.get('results'),
            'RealizationDate': safe_date(data.get('realization_date')),
            'LPURealization': self.person.organisation,
            'AnalysisNumber': safe_int(data.get('analysis_number')),
            'Comment': data.get('comment'),
            'Doctor': self.person,
        }

    def as_json(self):
        an_props = self.target_obj.propsByCode
        res = {
            'result_action_id': self.target_obj.id,
            'external_id': self.external_id,
            'measure_id': self.em.id,
            'measure_type_code': self.em.measure.code,
            'realization_date': an_props['RealizationDate'].value,
            'lpu_code': self.person.organisation and self.person.organisation.TFOMSCode or '',
            'analysis_number': an_props['AnalysisNumber'].value or '',
            'results': an_props['Results'].value or '',
            'comment': an_props['Comment'].value or '',
            'doctor_code': self.person.regionalCode,
        }
        return res
