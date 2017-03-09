#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.models.risar import RisarRiskGroup
from hippocrates.blueprints.risar.views.api.integration.expert_data.schemas import \
    ExpertDataSchema, ExpertDataTomskSchema
from hippocrates.blueprints.risar.views.api.integration.xform import XForm, VALIDATION_ERROR
from hippocrates.blueprints.risar.lib.radzinsky_risks.calc_regional_risks import get_event_tomsk_regional_risks_info
from hippocrates.blueprints.risar.lib.specific import SpecificsManager
from hitsl_utils.api import ApiException
from nemesis.models.event import Event, EventType
from nemesis.models.risar import rbPerinatalRiskRateMkbAssoc
from nemesis.models.enums import PregnancyPathology, TomskRegionalRiskStage
from nemesis.lib.apiutils import ApiException


class ExpertDataXForm(ExpertDataSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Event
    parent_id_required = False

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(EventType).filter(
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0,
        )
        return res

    def get_card(self):
        if not self.pcard:
            self.pcard = PregnancyCard.get_for_event(self.target_obj)
        return self.pcard

    def as_json(self):
        self.find_target_obj(self.target_obj_id)
        card = self.get_card()
        action = card.attrs

        res = {
            'risk_degree': self.from_rb(action['prenatal_risk_572'].value),
            'established_preeclampsia': self.from_rb(action['preeclampsia_comfirmed'].value),
            'suspected_preeclampsia': self.from_rb(action['preeclampsia_susp'].value),
            'estimated_birth_date': action['predicted_delivery_date'].value,
            'risk_groups': self._get_risk_groups(),
            'patology_groups': [
                unicode(PregnancyPathology(x))
                for x in action['pregnancy_pathology_list'].value or []
            ],
        }
        self._set_risk_diagnosis(res, action)
        return res

    def _get_risk_groups(self):
        return [x[0] for x in RisarRiskGroup.query.filter(
            RisarRiskGroup.event_id == self.target_obj_id,
            RisarRiskGroup.deleted == 0,
        ).values('riskGroup_code')]

    def _set_risk_diagnosis(self, res, action):
        event = self.target_obj
        diagnostics = self.pcard.get_client_diagnostics(event.setDate, event.execDate)
        opened_diags_ids = [d.mkb.id for d in diagnostics if not d.endDate]
        risk_degree_id = action['prenatal_risk_572'].value.id
        risk_diagnosis = rbPerinatalRiskRateMkbAssoc.query.filter(
            rbPerinatalRiskRateMkbAssoc.riskRate_id == risk_degree_id,
            rbPerinatalRiskRateMkbAssoc.mkb_id.in_(opened_diags_ids),
        ).all()
        data = []
        for risk_diag in risk_diagnosis:
            data.append(
                {
                    'diagnosis_code': risk_diag.mkb.regionalCode,
                    'diagnosis_name': risk_diag.mkb.DiagName,
                }
            )
        if data:
            res['risk_diagnosis'] = data


class ExpertDataTomskXForm(ExpertDataTomskSchema, ExpertDataXForm):

    def check_params(self, target_obj_id, parent_obj_id=None, data=None):
        super(ExpertDataTomskXForm, self).check_params(target_obj_id, parent_obj_id, data)
        if not SpecificsManager.is_region_tomsk():
            raise ApiException(VALIDATION_ERROR, u'В данном режиме работы системы этот метод API недоступен')

    def _get_regional_risks(self):
        risks = get_event_tomsk_regional_risks_info(self.get_card())
        general_info = risks['general_info']
        stage_factors = risks['stage_factors']

        res = []
        for stage_id, sum_attr_name in zip(
            (TomskRegionalRiskStage.initial[0], TomskRegionalRiskStage.before21[0],
             TomskRegionalRiskStage.from21to30[0], TomskRegionalRiskStage.from31to36[0]),
            ('initial_points', 'before21week_points',
             'from21to30week_points', 'from31to36week_points')
        ):
            stage_code = TomskRegionalRiskStage(stage_id).code
            stage_item = {
                'stage': stage_code,
                'factors': [factor_info['code']
                            for factor_list in stage_factors[stage_code].itervalues()
                            for factor_info in factor_list
                            if factor_info['triggered']],
                'sum': general_info[sum_attr_name]
            }
            res.append(stage_item)
        return res

    def as_json(self):
        res = super(ExpertDataTomskXForm, self).as_json()
        res['regional_scale_risks'] = self._get_regional_risks()
        return res
