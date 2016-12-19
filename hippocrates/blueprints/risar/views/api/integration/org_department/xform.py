# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, ALREADY_PRESENT_ERROR
from .schemas import OrgDepartmentSchema

from nemesis.models.exists import OrgStructure
from nemesis.systemwide import db
from nemesis.lib.utils import safe_bool, safe_int
from nemesis.lib.apiutils import ApiException


logger = logging.getLogger('simple')


class OrgDepartmentXForm(OrgDepartmentSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = OrgStructure
    target_id_required = False
    parent_id_required = False

    def check_duplicate(self, data):
        org_str_code = data['regionalCode']
        q = OrgStructure.query.filter(
            OrgStructure.regionalCode == org_str_code,
            OrgStructure.deleted == 0
        )
        org_exists = db.session.query(q.exists()).scalar()
        if org_exists:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует Подразделение c кодом {0}'.format(org_str_code)
            )

    def _find_target_obj_query(self):
        query = OrgStructure.query.filter(
            OrgStructure.deleted == 0
        )
        return query

    def init_and_check_params(self, org_str_code=None, data=None):
        if not self.new:
            self.target_obj = self.find_org_structure(org_str_code)
        super(OrgDepartmentXForm, self).check_params(None, self.target_obj.id if self.target_obj else None, data)

    def update_target_obj(self, data):
        if self.new:
            self.target_obj = OrgStructure()
            self._changed.append(self.target_obj)

        org_id = self.find_org(data['organisation_id']).id
        parent_department_code = data.get('parent_department')
        if parent_department_code:
            parent_id = self.find_org_structure(parent_department_code).id
            self.target_obj.parent_id = parent_id
        self.target_obj.organisation_id = org_id
        self.target_obj.regionalCode = data.get('regionalCode')
        self.target_obj.TFOMSCode = data.get('TFOMSCode')
        self.target_obj.name = data.get('name') or ''
        self.target_obj.Address = data.get('address') or ''
        self.target_obj.type = data.get('type') or '0'

        self._fill_required_fields()

    def _fill_required_fields(self):
        self.target_obj.code = ''
        self.target_obj.infisCode = ''
        self.target_obj.infisInternalCode = ''
        self.target_obj.infisDepTypeCode = ''
        self.target_obj.infisTariffCode = ''

    def as_json(self):
        if self.target_obj:
            return self.org_represent(self.target_obj)
        else:
            res = []
            for org_struct in self._find_target_obj_query():
                res.append(self.org_represent(org_struct))
            return res

    def org_represent(self, target_obj):
        return {
            'organisation_id': target_obj.organisation.regionalCode,
            'parent_department': target_obj.parent_id and target_obj.parent.regionalCode,
            'regionalCode': target_obj.regionalCode,
            'TFOMSCode': target_obj.TFOMSCode,
            'name': target_obj.name,
            'address': target_obj.Address,
            'type': target_obj.type,
        }

    def delete_target_obj(self):
        self.target_obj.deleted = 1
        self._changed.append(self.target_obj)
