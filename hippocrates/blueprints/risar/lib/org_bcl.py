# -*- coding: utf-8 -*-

from sqlalchemy import func, and_
from sqlalchemy.orm import immediateload

from nemesis.systemwide import db
from nemesis.models.organisation import OrganisationBirthCareLevel, Organisation
from nemesis.models.enums import PerinatalRiskRate, PrenatalRiskRate
from nemesis.models.exists import Person
from nemesis.models.event import Event
from nemesis.models.client import Client
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer


class OrganisationFetcher(object):

    def __init__(self):
        self.query = Organisation.query.filter(
            Organisation.deleted == 0
        ).order_by(Organisation.id)

    def apply_filter(self, **flt):
        if 'obcl_id' in flt:
            self.query = self.query.join(
                Organisation.org_obcls,
                OrganisationBirthCareLevel
            ).filter(OrganisationBirthCareLevel.id == flt['obcl_id'])
            return self
        return self

    def apply_with_patients_by_risk(self):
        patient_sq = db.session.query(Event).join(
            Event.execPerson,
            Client,
            (Action, Action.event_id == Event.id),
            (ActionType, and_(Action.actionType_id == ActionType.id, ActionType.flatCode == 'cardAttributes')),
            ActionProperty,
            (
                ActionPropertyType, and_(
                ActionProperty.type_id == ActionPropertyType.id,
                ActionPropertyType.code == 'prenatal_risk_572')
            ),
            ActionProperty_Integer
        ).filter(
            Event.execDate.is_(None),
            Event.result_id.is_(None),
        ).group_by(
            Person.org_id
        ).with_entities(
            Person.org_id
        ).add_columns(
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.low[0], 1, 0)).label('count_low'),
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.medium[0], 1, 0)).label('count_medium'),
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.high[0], 1, 0)).label('count_high')
        ).subquery()
        self.query = self.query.outerjoin(
            patient_sq, Organisation.id == patient_sq.c.org_id
        ).add_columns(
            patient_sq.c.count_low,
            patient_sq.c.count_medium,
            patient_sq.c.count_high
        )

    def apply_with_obcl(self):
        self.query = self.query.options(immediateload(Organisation.obcl_list))

    def get_all(self):
        return self.query.all()


class OrgBirthCareLevelFetcher(object):

    def __init__(self):
        self.set_base_query()

    def set_base_query(self):
        self.query = OrganisationBirthCareLevel.query.filter(
            OrganisationBirthCareLevel.deleted == 0
        ).order_by(OrganisationBirthCareLevel.idx)

    def apply_filter(self, **flt):
        if 'obcl_id' in flt:
            self.query = self.query.filter(OrganisationBirthCareLevel.id == flt['obcl_id'])
            return self
        return self

    def apply_with_count(self):
        self.query = self.query.outerjoin(
            OrganisationBirthCareLevel.org_obcls,
            Organisation
        ).group_by(
            OrganisationBirthCareLevel.id
        ).add_columns(func.count(Organisation.id.distinct()))

    def get_all(self):
        return self.query.all()

    def get_first(self):
        return self.query.first()

    def paginate(self, per_page=20, page=1):
        return self.query.paginate(page, per_page, False)

    def reset(self):
        self.set_base_query()


class OrgBirthCareLevelRepr(object):

    def represent_levels_count(self):
        selector = OrgBirthCareLevelFetcher()
        selector.apply_with_count()
        data = selector.get_all()
        return {
            'obcl_items': [
                self.represent_obcl_count(obcl, org_count) for obcl, org_count in data
            ]
        }

    def represent_level_orgs(self, obcl_id):
        org_fetcher = OrganisationFetcher()
        org_fetcher.apply_filter(obcl_id=obcl_id)
        org_fetcher.apply_with_patients_by_risk()
        org_fetcher.apply_with_obcl()
        org_data = org_fetcher.get_all()
        return {
            'org_items': [
                self.represent_org_for_level(org, org.obcl_list, count_low, count_medium, count_high)
                for org, count_low, count_medium, count_high in org_data
            ]
        }

    def represent_obcl_count(self, obcl, org_count):
        return dict(
            self.represent_obcl(obcl),
            org_count=org_count
        )

    def represent_obcl(self, obcl):
        return {
            'id': obcl.id,
            'code': obcl.code,
            'name': obcl.name,
            'description': obcl.description,
            'perinatal_risk_rate': PerinatalRiskRate(obcl.perinatalRiskRate_id),
            'idx': obcl.idx
        }

    def represent_org_for_level(self, org, obcl_list, count_low, count_medium, count_high):
        return dict(
            OrganisationRepr().represent_org_bcl(org, obcl_list),
            patient_by_risk_count={
                'low': count_low,
                'medium': count_medium,
                'high': count_high
            }
        )


class OrganisationRepr():

    def represent_org_bcl(self, org, obcl_list):
        obcl_repr = OrgBirthCareLevelRepr()
        return dict(
            self.represent_org(org),
            obcls=map(obcl_repr.represent_obcl, obcl_list)
        )

    def represent_org(self, org):
        return {
            'id': org.id,
            'full_name': org.fullName,
            'short_name': org.shortName,
            'title': org.title,
            'infis': org.infisCode,
            'is_insurer': bool(org.isInsurer),
            'is_hospital': bool(org.isHospital),
            'address': org.Address,
            'phone': org.phone,
            'deleted': org.deleted
        }