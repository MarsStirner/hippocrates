#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.risar_config import general_results
from hippocrates.blueprints.risar.views.api.integration.research.schemas import \
    ResearchSchema
from hippocrates.blueprints.risar.views.api.integration.xform import MeasuresResultsXForm
from nemesis.lib.utils import safe_date, safe_datetime
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event


class ResearchXForm(ResearchSchema, MeasuresResultsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action
    flat_code = 'general_research'

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

    def prepare_params(self, data):
        if data.get('lpu_code'):
            self.organisation = self.find_org(data.get('lpu_code'))
        if data.get('doctor_code') and data.get('lpu_code'):
            self.person = self.find_doctor(data.get('doctor_code'), data.get('lpu_code'))

    def get_properties_data(self, data):
        return {
            'Results': data.get('results', '').replace('\r\n', '<br>'),
            'RealizationDate': safe_date(data.get('realization_date')),
            'AnalysisNumber': data.get('analysis_number'),
            'LPURealization': self.organisation,
            'Doctor': self.person,
            'Comment': data.get('comment'),
        }

    def set_result_action_data(self, data):
        self.target_obj.begDate = self.target_obj.endDate = safe_datetime(data['RealizationDate'])
        self.target_obj.person = data['Doctor']

    def as_json(self):
        an_props = self.target_obj.propsByCode
        res = {
            'result_action_id': self.target_obj.id,
            'external_id': self.external_id,
            'measure_id': self.em.id,
            'measure_status': self.em.literal_status,
            'measure_type_code': self.em.measure.code,
            'realization_date': an_props['RealizationDate'].value,
            'analysis_number': an_props['AnalysisNumber'].value or '',
            'results': an_props['Results'].value or '',
            'comment': an_props['Comment'].value or '',
        }

        if self.person:
            res['doctor_code'] = self.person.regionalCode
            res['lpu_code'] = ''
            if self.person.organisation:
                res['lpu_code'] = self.person.organisation.regionalCode or ''

        return res
