# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, ALREADY_PRESENT_ERROR
from .schemas import DoctorSchema

from nemesis.models.person import Person, rbSpeciality, rbPost
from nemesis.models.organisation import Organisation
from nemesis.models.enums import Gender
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_int
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_uuid


logger = logging.getLogger('simple')


class DoctorXForm(DoctorSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Person
    target_id_required = False
    parent_id_required = False

    def check_duplicate(self, data):
        person_code = data['regional_code']
        org_code = data['organization']
        q = Person.query.join(Organisation).filter(
            Person.regionalCode == person_code,
            Person.deleted == 0,
            Organisation.TFOMSCode == org_code,
            Organisation.deleted == 0
        )
        person_exists = db.session.query(q.exists()).scalar()
        if person_exists:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует Врач c кодом {0} и кодом ЛПУ {1}'.format(person_code, org_code)
            )

    def _find_target_obj_query(self):
        pass

    def init_and_check_params(self, lpu_code=None, doctor_code=None, data=None):
        if not self.new:
            self.target_obj = self.find_doctor(doctor_code, lpu_code)
        super(DoctorXForm, self).check_params(None, self.target_obj.id if self.target_obj else None, data)

    def update_target_obj(self, data):
        if self.new:
            self.target_obj = Person()
            self._changed.append(self.target_obj)

        self.target_obj.lastName = data.get('last_name')
        self.target_obj.firstName = data.get('first_name')
        self.target_obj.patrName = data.get('patr_name') or ''
        sex = self.to_enum(safe_int(data.get('sex')), Gender)
        self.target_obj.sex = sex.value
        self.target_obj.birthDate = safe_date(data.get('birth_date'))
        self.target_obj.SNILS = data.get('SNILS') or ''
        self.target_obj.INN = data.get('INN') or ''
        org = self.find_org(data.get('organization'))
        self.target_obj.organisation = org
        if 'speciality' in data:
            self._check_rb_value('rbSpeciality', data['speciality'])
            self.target_obj.speciality = rbSpeciality.query.filter(rbSpeciality.code == data['speciality']).first()
        else:
            self.target_obj.speciality = None
        if 'post' in data:
            self._check_rb_value('rbPost', data['post'])
            self.target_obj.post = rbPost.query.filter(rbPost.code == data['post']).first()
        else:
            self.target_obj.post = None
        self.target_obj.login = data.get('login')
        self.target_obj.regionalCode = data.get('regional_code')
        self._fill_required_fields()

    def _fill_required_fields(self):
        self.target_obj.uuid = get_new_uuid()
        self.target_obj.code = ''
        self.target_obj.federalCode = ''
        self.target_obj.office = ''
        self.target_obj.office2 = ''
        self.target_obj.ambPlan = 0
        self.target_obj.ambPlan2 = 0
        self.target_obj.ambNorm = 0
        self.target_obj.homPlan = 0
        self.target_obj.homPlan2 = 0
        self.target_obj.homNorm = 0
        self.target_obj.expPlan = 0
        self.target_obj.expNorm = 0
        self.target_obj.password = ''
        self.target_obj.retired = 0
        self.target_obj.birthPlace = ''
        self.target_obj.typeTimeLinePerson = 0

    def as_json(self):
        return {
            'last_name': self.target_obj.lastName,
            'first_name': self.target_obj.firstName,
            'patr_name': self.target_obj.patrName,
            'sex': self.target_obj.sex,
            'birth_date': self.target_obj.birthDate,
            'SNILS': self.target_obj.SNILS,
            'INN': self.target_obj.INN,
            'organization': self.from_org_rb(self.target_obj.organisation),
            'speciality': self.from_rb(self.target_obj.speciality),
            'post': self.from_rb(self.target_obj.post),
            'login': self.target_obj.login,
            'regional_code': self.target_obj.regionalCode,
        }