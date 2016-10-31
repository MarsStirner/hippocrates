# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, ALREADY_PRESENT_ERROR
from .schemas import OrganizationSchema

from nemesis.models.organisation import Organisation
from nemesis.systemwide import db
from nemesis.lib.utils import safe_bool, safe_int
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_uuid


logger = logging.getLogger('simple')


class OrganizationXForm(OrganizationSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Organisation
    target_id_required = False
    parent_id_required = False

    def check_duplicate(self, data):
        org_code = data['TFOMSCode']
        q = Organisation.query.filter(
            Organisation.TFOMSCode == org_code,
            Organisation.deleted == 0
        )
        org_exists = db.session.query(q.exists()).scalar()
        if org_exists:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует Организация c кодом {0}'.format(org_code)
            )

    def _find_target_obj_query(self):
        pass

    def init_and_check_params(self, org_code=None, data=None):
        if not self.new:
            self.target_obj = self.find_org(org_code)
        super(OrganizationXForm, self).check_params(None, self.target_obj.id if self.target_obj else None, data)

    def update_target_obj(self, data):
        if self.new:
            self.target_obj = Organisation()
            self._changed.append(self.target_obj)

        self.target_obj.fullName = data.get('full_name') or ''
        self.target_obj.shortName = data.get('short_name') or ''
        self.target_obj.infisCode = data.get('infis_code') or ''
        self.target_obj.Address = data.get('address') or ''
        self.target_obj.area = data.get('area') or ''
        self.target_obj.phone = data.get('phone') or ''
        self.target_obj.TFOMSCode = data.get('TFOMSCode')
        self.target_obj.INN = data.get('INN') or ''
        self.target_obj.KPP = data.get('KPP') or ''
        self.target_obj.OGRN = data.get('OGRN') or ''
        self.target_obj.OKATO = data.get('OKATO') or ''
        self.target_obj.isLPU = safe_int(safe_bool(data.get('is_LPU')))
        self.target_obj.isStationary = safe_int(safe_bool(data.get('is_stationary')))
        self.target_obj.isInsurer = safe_int(safe_bool(data.get('is_insurer')))

        self._fill_required_fields()

    def _fill_required_fields(self):
        self.target_obj.uuid = get_new_uuid()
        self.target_obj.title = ''
        self.target_obj.isHospital = 0
        self.target_obj.obsoleteInfisCode = ''
        self.target_obj.OKVED = ''
        self.target_obj.OKPF_code = ''
        self.target_obj.OKFS_code = 0
        self.target_obj.OKPO = ''
        self.target_obj.FSS = ''
        self.target_obj.region = ''
        self.target_obj.chief = ''
        self.target_obj.accountant = ''
        self.target_obj.notes = ''
        self.target_obj.miacCode = ''

    def as_json(self):
        return {
            'full_name': self.target_obj.fullName,
            'short_name': self.target_obj.shortName,
            'infis_code': self.target_obj.infisCode,
            'address': self.target_obj.Address,
            'area': self.target_obj.area,
            'phone': self.target_obj.phone,
            'TFOMSCode': self.target_obj.TFOMSCode,
            'INN': self.target_obj.INN,
            'KPP': self.target_obj.KPP,
            'OGRN': self.target_obj.OGRN,
            'OKATO': self.target_obj.OKATO,
            'is_LPU': self.target_obj.isLPU,
            'is_stationary': self.target_obj.isStationary,
            'is_insurer': self.target_obj.isInsurer,
        }
