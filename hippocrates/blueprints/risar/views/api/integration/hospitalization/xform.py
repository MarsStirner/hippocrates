#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.models.risar import RisarRiskGroup, ActionIdentification
from blueprints.risar.views.api.integration.hospitalization.schemas import \
    HospitalizationSchema
from blueprints.risar.views.api.integration.xform import XForm, \
    VALIDATION_ERROR, ALREADY_PRESENT_ERROR, MIS_BARS_CODE, NOT_FOUND_ERROR
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbAccountingSystem
from nemesis.models.risar import rbPerinatalRiskRateMkbAssoc
from nemesis.lib.apiutils import ApiException
from nemesis.systemwide import db


class HospitalizationXForm(HospitalizationSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def __init__(self, *a, **kw):
        super(HospitalizationXForm, self).__init__(*a, **kw)
        self.external_id = None
        self.external_system = rbAccountingSystem.query.filter(
            rbAccountingSystem.code == MIS_BARS_CODE,
        ).first()

    def check_duplicate(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'api_checkup_obs_first_save used without "external_id"' %
                self.target_obj_class.__name__
            )
        q = self._find_target_obj_query().join(
            ActionIdentification
        ).join(rbAccountingSystem).filter(
            ActionIdentification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if target_obj_exist:
            raise ApiException(ALREADY_PRESENT_ERROR, u'%s already exist' %
                               self.target_obj_class.__name__)

    def check_external_id(self, data):
        self.external_id = data.get('external_id')
        if not self.external_id:
            raise ApiException(
                VALIDATION_ERROR,
                u'api_checkup_obs_first_save used without "external_id"' %
                self.target_obj_class.__name__
            )
        q = ActionIdentification.query.join(rbAccountingSystem).filter(
            ActionIdentification.external_id == self.external_id,
            rbAccountingSystem.code == MIS_BARS_CODE,
            ActionIdentification.action_id == self.target_obj_id,
        )
        target_obj_exist = db.session.query(q.exists()).scalar()
        if not target_obj_exist:
            raise ApiException(NOT_FOUND_ERROR, u'%s not found' %
                               self.target_obj_class.__name__)

    def save_external_data(self):
        if self.new:
            external_action = ActionIdentification(
                action=self.target_obj,
                action_id=self.target_obj_id,
                external_id=self.external_id,
                external_system=self.external_system,
                external_system_id=self.external_system.id,
            )
            db.session.add(external_action)

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
        form_data = self.mapping_as_form(data)
        self.update_form(form_data)
        self.save_external_data()

    def mapping_as_form(self, data):
        res = {}
        self.mapping_fields(data, res)
        return res

    def mapping_fields(self, data, res):
        self.mapping_part(self.FIELDS_MAP, data, res)

        person_id = self.find_doctor(data.get('doctor'), data.get('hospital')).id
        res.update({
            'person': {
                'id': person_id,
            },
            'get_diagnoses_func': lambda: self.get_diagnoses(data, res),
        })

    def get_diags_data(self, data):
        return data

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups_puerpera.api_0_checkup_puerpera
        pass

    def reevaluate_data(self):
        from blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
        reevaluate_card_fill_rate_all(self.pcard)

    def close_diags(self):
        # Роман:
        # сначала найти открытые диагнозы пациента (это будут просто диагнозы без типа), затем среди них определить какие являются основными,
        # осложнениями и пр. - это значит, что Diagnosis связывается с осмотром через Action_Diagnosis, где указывается его тип, т.е. диагноз
        # пациента в рамках какого-то осмотра будет иметь определенный тип. *Все открытые диагнозы пациента, для которых не указан тип в связке
        # с экшеном являются сопотствующими неявно*.
        # тут надо понять логику работы с диагнозами (четкого описания нет), после этого нужно доработать механизм диагнозов - из того, что я знаю,
        # сейчас проблема как раз с определением тех диагнозов пациента, которые относятся к текущему случаю. Для этого нужно исправлять запрос,
        # выбирающий диагнозы по датам с учетом дат Event'а. После этого уже интегрировать.

        # Action_Diagnosis
        # Diagnostic.query.filter(Diagnosis.id == diagnosis)
        # q = Diagnosis.query.filter(Diagnosis.client == self.parent_obj.client)
        # q.update({'deleted': 1})
        raise

    def delete_target_obj(self):
        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()
        # В методе удаления осмотра с плодами ничего не делать, у action.deleted = 1
        # self.delete_fetuses()

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

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
            'patology_groups': [unicode(x) for x in action['pregnancy_pathology_list'].value or []],
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
