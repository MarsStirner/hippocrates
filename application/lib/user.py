# -*- coding: utf-8 -*-
from application.database import db
from application.models.exists import Person
import hashlib


class UserAuth():

    @classmethod
    def check_user(cls, login, password):
        user = cls.__get_by_login(login)
        if user and cls.__check_password(user.password, password):
            return user
        return None

    @classmethod
    def __get_by_login(cls, login):
        user = db.session.query(Person).filter(Person.login == login).first()
        if user:
            return user
        return None

    @classmethod
    def __check_password(cls, pw_hash, password):
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.query(Person).get(user_id)