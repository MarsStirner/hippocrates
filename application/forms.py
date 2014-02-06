# -*- coding: utf-8 -*-
from wtforms import StringField, BooleanField, PasswordField, RadioField
from wtforms.validators import Required
from flask_wtf import Form


class LoginForm(Form):
    login = StringField(u'Логин')
    password = PasswordField(u'Пароль')