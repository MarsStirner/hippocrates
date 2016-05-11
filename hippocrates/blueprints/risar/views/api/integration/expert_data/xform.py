#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.models.risar import RisarRiskGroup
from blueprints.risar.views.api.integration.expert_data.schemas import \
    ExpertDataSchema
from blueprints.risar.views.api.integration.xform import XForm
from nemesis.models.event import Event, EventType
from nemesis.models.risar import rbPerinatalRiskRateMkbAssoc
from nemesis.models.enums import PregnancyPathology
from nemesis.lib.utils import safe_dict


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

    def as_json(self):
        self.find_target_obj(self.target_obj_id)
        event = self.target_obj
        self.pcard = PregnancyCard.get_for_event(event)
        action = self.pcard.attrs

        res = {
            'risk_degree': self.from_rb(action['prenatal_risk_572'].value),
            'established_preeclampsia': self.from_rb(action['preeclampsia_comfirmed'].value),
            'suspected_preeclampsia': self.from_rb(action['preeclampsia_susp'].value),
            'estimated_birth_date': action['predicted_delivery_date'].value,
            'risk_groups': self._get_risk_groups(),
            'patology_groups': [
                safe_dict(self.to_enum(x, PregnancyPathology))
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
                    'diagnosis_code': risk_diag.mkb.DiagID,
                    'diagnosis_name': risk_diag.mkb.DiagName,
                }
            )
        if data:
            res['risk_diagnosis'] = data,
