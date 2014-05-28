# -*- coding: utf-8 -*-
from application.systemwide import db
from application.models.exists import Person
from flask.ext.login import UserMixin, AnonymousUserMixin
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
        self.current_role = None
        self.rights = dict()
        self.post = dict()
        if person.post:
            self.post.update(dict((key, value)
                             for key, value in person.post.__dict__.iteritems()
                             if not callable(value) and not key.startswith('__')))
        self.set_roles_rights(person)

    def is_active(self):
        return self.deleted == 0

    def is_admin(self):
        return self.current_role == 'admin'

    def role_in(self, roles):
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        return self.current_role in roles

    def has_role(self, role):
        # what about list?
        for r in self.roles:
            if r[0] == role:
                return True
        return False

    def has_right(self, right):
        # what about list?
        return right in self.rights

    def set_roles_rights(self, person):
        if person.user_profiles:
            for role in person.user_profiles:
                self.roles.append((role.code, role.name))
                if role.rights:
                    self.rights[role.code] = list()
                    for right in role.rights:
                        self.rights[role.code].append(right.code)


class AnonymousUser(AnonymousUserMixin):

    def is_admin(self):
        return False


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