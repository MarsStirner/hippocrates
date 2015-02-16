# -*- coding: utf-8 -*-
from application.systemwide import db
from application.models.exists import Person
from flask import url_for
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
import hashlib


class User(UserMixin):

    def __init__(self, person):
        if not isinstance(person, Person):
            raise AttributeError(u'Not instance of models.Person')
        self.deleted = 0
        self.__dict__.update(dict((key, value)
                                  for key, value in person.__dict__.iteritems()
                                  if not callable(value) and not key.startswith('__')))
        self.roles = list()
        self._current_role = None
        self.rights = dict()
        self.post = dict()
        if person.post:
            self.post.update(dict((key, value)
                             for key, value in person.post.__dict__.iteritems()
                             if not callable(value) and not key.startswith('__')))
        self.set_roles_rights(person)

        orgStructure = person.org_structure
        atos = set()
        while orgStructure:
            atos.add(orgStructure.id)
            orgStructure = orgStructure.parent if orgStructure.inheritActionTypes else None
        self.action_type_org_structures = atos
        self.action_type_personally = []

    @property
    def current_role(self):
        return getattr(self, '_current_role', None)

    @current_role.setter
    def current_role(self, value):
        self._current_role = value
        from ..models.actions import ActionType_User
        from ..models.exists import rbUserProfile
        self.action_type_personally = [
            record.actionType_id
            for record in ActionType_User.query.outerjoin(rbUserProfile).filter(db.or_(
                ActionType_User.person_id == self.id,
                rbUserProfile.code == value
            ))
        ]
        self.current_rights = self.rights[value]

    def is_active(self):
        return self.deleted == 0

    def is_admin(self):
        return getattr(self, 'current_role', None) == 'admin'

    def role_in(self, *args):
        roles = []
        for arg in args:
            if isinstance(arg, list):
                roles.extend(arg)
            elif isinstance(arg, tuple):
                roles.extend(list(arg))
            else:
                roles.append(arg)
        return self.current_role in roles

    def has_role(self, role):
        # what about list?
        for r in self.roles:
            if r[0] == role:
                return True
        return False

    def has_right(self, right):
        # what about list?
        return right in self.current_rights

    def set_roles_rights(self, person):
        if person.user_profiles:
            for role in person.user_profiles:
                self.roles.append((role.code, role.name))
                if role.rights:
                    self.rights[role.code] = list()
                    for right in role.rights:
                        self.rights[role.code].append(right.code)

    def export_js(self):
        return {
            'id': self.get_id(),
            'roles': self.roles,
            'is_admin': self.is_admin(),
            'current_role': self.current_role,
            'rights': self.rights,
            'action_type_org_structures': sorted(getattr(self, 'action_type_org_structures', set())),
            'action_type_personally': sorted(getattr(self, 'action_type_personally', [])),
        }


class AnonymousUser(AnonymousUserMixin):

    def is_admin(self):
        return False

    def export_js(self):
        return {
            'id': None,
            'roles': [],
            'is_admin': self.is_admin(),
            'current_role': None,
            'rights': [],
        }


class UserAuth():

    @classmethod
    def auth_user(cls, login, password):
        person = cls.__get_by_login(login)
        if person and cls.__check_password(person.password, password):
            return User(person)
        return None

    @classmethod
    def __get_by_login(cls, login):
        person = db.session.query(Person).filter(Person.login == login).first()
        if person:
            return person
        return None

    @classmethod
    def __check_password(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def __prepare_user(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_id(cls, user_id):
        return User(db.session.query(Person).get(int(user_id)))

    @classmethod
    def get_roles_by_login(cls, login):
        from ..models.exists import rbUserProfile, PersonProfiles
        return [
            {'code': role.code, 'name': role.name}
            for role in (rbUserProfile.query
                         .join(PersonProfiles)
                         .join(Person)
                         .filter(Person.login == login)
                         .order_by(rbUserProfile.name))
        ]


class UserUtils(object):

    def can_delete_event(self, event):
        return event and (
            current_user.has_right('evtDelAll') or
            current_user.has_right('adm') or
            (current_user.has_right('evtDelOwn') and
                (current_user.id == event.execPerson_id or
                 current_user.id == event.createPerson_id)
            )
        )


class UserProfileManager(object):
    user = None

    admin = 'admin'  # Администратор
    reg_clinic = 'clinicRegistrator'  # Регистратор поликлиники
    doctor_clinic = 'clinicDoctor'  # Врач поликлиники
    doctor_diag = 'diagDoctor'  # Врач диагностики
    doctor_stat = 'statDoctor'  # Врач медицинский статистик
    nurse_admission = 'admNurse'  # Медсестра приемного отделения

    ui_groups = {
        'doctor': [admin, doctor_clinic, doctor_diag],
        'registrator': [admin, reg_clinic],
        'registrator_cut': [admin, nurse_admission]
    }

    @classmethod
    def _get_user(cls):
        return cls.user or current_user

    @classmethod
    def set_user(cls, user):
        cls.user = user

    @classmethod
    def _get_user_role(cls):
        user = cls.user or current_user
        return user.current_role if not user.is_anonymous() else None

    @classmethod
    def has_ui_registrator(cls):
        return cls._get_user_role() in cls.ui_groups['registrator']

    @classmethod
    def has_ui_registrator_cut(cls):
        return cls._get_user_role() in cls.ui_groups['registrator_cut']

    @classmethod
    def has_ui_doctor(cls):
        return cls._get_user_role() in cls.ui_groups['doctor']

    @classmethod
    def has_ui_doctor_stat(cls):
        return cls._get_user_role() == cls.doctor_stat

    @classmethod
    def get_default_url(cls):
        if cls._get_user_role() == cls.nurse_admission:
            return url_for('patients.index')
        return url_for('index')