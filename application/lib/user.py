# -*- coding: utf-8 -*-
from application.database import db
from application.models.exists import Person
from flask.ext.login import UserMixin
import hashlib


class User(UserMixin):

    def __init__(self, person):
        if not isinstance(person, Person):
            raise AttributeError(u'Not instance of models.Person')
        self.__person = person
        self.__roles = list()
        self.__rights = list()

    def is_active(self):
        return self.__person.deleted == 0

    def is_admin(self):
        return self.has_right('admin')

    def has_role(self, role):
        # what about list?
        return role in self.roles

    def has_right(self, right):
        # what about list?
        return right in self.rights

    @property
    def roles(self):
        if self.__roles:
            return self.__roles
        if self.__person.user_profiles:
            self.__rights = list()
            for role in self.__person.user_profiles:
                self.__roles.append(role.code)
                if role.rights:
                    for right in role.rights:
                        self.__rights.append(right.code)
        return self.__roles

    @property
    def rights(self):
        if self.__rights:
            return list(set(self.__rights))
        if self.__person.user_profiles:
            for role in self.__person.user_profiles:
                if role.rights:
                    for right in role.rights:
                        self.__rights.append(right.code)
        return list(set(self.__rights))

    def __getattr__(self, name):
        return getattr(self.__person, name)


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
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def __prepare_user(cls, pw_hash, password):
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_id(cls, user_id):
        return User(db.session.query(Person).get(user_id))