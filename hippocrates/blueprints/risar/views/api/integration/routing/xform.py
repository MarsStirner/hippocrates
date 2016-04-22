#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.represent import get_lpu_attached, \
    group_orgs_for_routing, represent_mkbs_for_routing
from blueprints.risar.views.api.integration.routing.schemas import \
    RoutingSchema
from blueprints.risar.views.api.integration.xform import XForm
from nemesis.models.enums import PerinatalRiskRate
from nemesis.models.event import Event, EventType
from nemesis.models.organisation import Organisation, \
    OrganisationBirthCareLevel
from nemesis.models.risar import rbPerinatalRiskRate
from nemesis.systemwide import db


class RoutingXForm(RoutingSchema, XForm):
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
        client = event.client
        lpu_attached = get_lpu_attached(client.attachments)
        diagnoses = represent_mkbs_for_routing(event)

        hospital_list = self.get_hospital_list(diagnoses)
        group_orgs = self.get_group_orgs(hospital_list, client)
        region_orgs_ids = [y['id'] for x in group_orgs['region_orgs'].values() for y in x['orgs']]
        district_orgs_ids = [y['id'] for x in group_orgs['district_orgs'].values() for y in x['orgs']]
        hospital_emergency_list = [x[0] for x in Organisation.query.filter(Organisation.id.in_(region_orgs_ids)).values(Organisation.TFOMSCode)]
        hospital_emergency_list_district = [x[0] for x in Organisation.query.filter(Organisation.id.in_(district_orgs_ids)).values(Organisation.TFOMSCode)]

        res = {
            'hospital_planned': lpu_attached['plan_lpu'] and lpu_attached['plan_lpu'].org.TFOMSCode,
            'hospital_emergency': lpu_attached['extra_lpu'] and lpu_attached['extra_lpu'].org.TFOMSCode,
            'hospital_planned_list': [x.TFOMSCode for x in hospital_list],
            'hospital_emergency_list': hospital_emergency_list,
            'hospital_emergency_list_district': hospital_emergency_list_district,
        }
        return res

    def get_hospital_list(self, diagnoses):
        query = Organisation.query.filter(Organisation.isLPU == 1)
        if diagnoses:
            max_risk = diagnoses[0]['risk_rate'].value
            if max_risk > rbPerinatalRiskRate.query.get(PerinatalRiskRate.undefined[0]).value:
                suit_orgs_q = db.session.query(
                    Organisation.id.distinct().label('organisation_id')
                ).join(
                    OrganisationBirthCareLevel.orgs
                ).filter(
                    OrganisationBirthCareLevel.perinatalRiskRate_id == max_risk
                ).subquery('suitableOrgs')
                query = query.join(suit_orgs_q, Organisation.id == suit_orgs_q.c.organisation_id)
        suitable_orgs = query.all()
        return suitable_orgs

    def get_group_orgs(self, suitable_orgs, client):
        orgs = group_orgs_for_routing(suitable_orgs, client)
        return orgs
