# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from blueprints.risar.app import module
from blueprints.risar.lib.org_bcl import OrgBirthCareLevelRepr


@module.route('/api/0/org_birth_care_level/org_count/')
@api_method
def api_0_obcl_org_count_get():
    return OrgBirthCareLevelRepr().represent_levels_count()


@module.route('/api/0/org_birth_care_level/orgs_info/')
@module.route('/api/0/org_birth_care_level/orgs_info/<int:obcl_id>')
@api_method
def api_0_obcl_org_patient_count_get(obcl_id=None):
    if not obcl_id:
        raise ApiException(400, '`obcl_id` required')
    return OrgBirthCareLevelRepr().represent_level_orgs(obcl_id)
