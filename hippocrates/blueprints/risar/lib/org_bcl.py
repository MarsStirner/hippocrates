# -*- coding: utf-8 -*-

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import immediateload

from nemesis.systemwide import db
from nemesis.models.organisation import OrganisationBirthCareLevel, Organisation, Organisation_OrganisationBCLAssoc
from nemesis.models.enums import PerinatalRiskRate, PrenatalRiskRate
from nemesis.models.exists import Person
from nemesis.models.event import Event
from nemesis.models.client import Client
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
from nemesis.lib.utils import format_hex_color


class BaseFetcher(object):

    def __init__(self):
        self.set_base_query()

    def set_base_query(self):
        self.query = None

    def get_all(self):
        return self.query.all()

    def get_first(self):
        result = self.query.first()
        return result[0] if result else None

    def paginate(self, per_page=20, page=1):
        return self.query.paginate(page, per_page, False)

    def reset(self):
        self.set_base_query()


class OrganisationFetcher(BaseFetcher):

    def set_base_query(self):
        self.query = Organisation.query.filter(
            Organisation.deleted == 0
        ).order_by(Organisation.id)

    def apply_filter(self, **flt):
        if 'obcl_id' in flt:
            self.query = self.query.outerjoin(
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
            Event.deleted == 0,
            Action.deleted == 0,
            Event.execDate.is_(None),
            # Event.result_id.is_(None),
        ).group_by(
            Person.org_id
        ).with_entities(
            Person.org_id
        ).add_columns(
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.low[0], 1, 0)).label('count_low'),
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.medium[0], 1, 0)).label('count_medium'),
            func.sum(func.IF(ActionProperty_Integer.value_ == PrenatalRiskRate.high[0], 1, 0)).label('count_high'),
            func.sum(func.IF(or_(
                ActionProperty_Integer.value_ == PrenatalRiskRate.undefined[0],
                Action.id == None
            ), 1, 0)).label('count_undefined'),
            func.count(Event.id.distinct()).label('count_all')
        ).subquery()
        self.query = self.query.outerjoin(
            patient_sq, Organisation.id == patient_sq.c.org_id
        ).add_columns(
            patient_sq.c.count_low,
            patient_sq.c.count_medium,
            patient_sq.c.count_high,
            patient_sq.c.count_undefined,
            patient_sq.c.count_all
        )

    def apply_with_obcl(self):
        self.query = self.query.options(immediateload(Organisation.obcl_list))

    def apply_org_count_empty_obcl(self):
        self.query = self.query.outerjoin(
            Organisation_OrganisationBCLAssoc,
            OrganisationBirthCareLevel
        ).filter(
            OrganisationBirthCareLevel.id == None
        ).with_entities(
            func.count(Organisation.id.distinct())
        )


class OrgBirthCareLevelFetcher(BaseFetcher):

    def set_base_query(self):
        self.query = OrganisationBirthCareLevel.query.filter(
            OrganisationBirthCareLevel.deleted == 0
        ).order_by(OrganisationBirthCareLevel.idx)

    def apply_filter(self, **flt):
        if 'obcl_id' in flt:
            self.query = self.query.filter(OrganisationBirthCareLevel.id == flt['obcl_id'])
            return self
        return self

    def apply_with_org_count(self):
        self.query = self.query.outerjoin(
            OrganisationBirthCareLevel.org_obcls,
            Organisation
        ).group_by(
            OrganisationBirthCareLevel.id
        ).add_columns(func.count(Organisation.id.distinct()))


class OrgBirthCareLevelRepr(object):

    def represent_levels_count(self):
        fetcher = OrgBirthCareLevelFetcher()
        fetcher.apply_with_org_count()
        obcl_data = fetcher.get_all()
        fetcher = OrganisationFetcher()
        fetcher.apply_org_count_empty_obcl()
        empty_obcl_org_count = fetcher.get_first()
        return {
            'obcl_items': [
                self.represent_obcl_count(obcl, org_count) for obcl, org_count in obcl_data
            ],
            'empty_obcl': self.represent_obcl_count(None, empty_obcl_org_count)
        }

    def represent_level_orgs(self, obcl_id):
        org_fetcher = OrganisationFetcher()
        org_fetcher.apply_filter(obcl_id=obcl_id)
        org_fetcher.apply_with_patients_by_risk()
        org_fetcher.apply_with_obcl()
        org_data = org_fetcher.get_all()
        return {
            'org_items': [
                self.represent_org_for_level(org, org.obcl_list, count_low, count_medium, count_high, count_undefined, count_all)
                for org, count_low, count_medium, count_high, count_undefined, count_all in org_data
            ]
        }

    def represent_obcl_count(self, obcl, org_count):
        return dict(
            self.represent_obcl(obcl) if obcl else {},
            org_count=org_count
        )

    def represent_obcl(self, obcl):
        return {
            'id': obcl.id,
            'code': obcl.code,
            'name': obcl.name,
            'description': obcl.description,
            'perinatal_risk_rate': PerinatalRiskRate(obcl.perinatalRiskRate_id),
            'idx': obcl.idx,
            'color': format_hex_color(obcl.color)
        }

    def represent_org_for_level(self, org, obcl_list, count_low, count_medium, count_high, count_undefined, count_all):
        return dict(
            OrganisationRepr().represent_org_bcl(org, obcl_list),
            patient_by_risk_count={
                'low': count_low or 0,
                'medium': count_medium or 0,
                'high': count_high or 0,
                'undefined': count_undefined or 0,
                'all': count_all or 0
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