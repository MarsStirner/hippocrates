# -*- coding: utf-8 -*-
from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, IntegerField, RadioField, SelectField, TextAreaField, BooleanField, FormField
from wtforms.widgets import TextInput, Select
from wtforms.validators import DataRequired, Email, AnyOf, Optional, Required

from application.app import app
from blueprints.schedule.models.exists import rbDocumentType, rbUFMS, rbPolicyType, Organisation


class AngularJSTextInput(TextInput):
    def __call__(self, field, **kwargs):
        for key in list(kwargs):
            if key.startswith('ng_'):
                kwargs['ng-' + key[3:]] = kwargs.pop(key)
        return super(AngularJSTextInput, self).__call__(field, **kwargs)


class AngularJSSelect(Select):
    def __call__(self, field, **kwargs):
        for key in list(kwargs):
            if key.startswith('ng_'):
                kwargs['ng-' + key[3:]] = kwargs.pop(key)
        return super(AngularJSSelect, self).__call__(field, **kwargs)


class ClientForm(Form):
    lastname = StringField(u'Фамилия<span class="text-danger">*</span>', [DataRequired()], widget=AngularJSTextInput())
    firstname = StringField(u'Имя<span class="text-danger">*</span>', [DataRequired()], widget=AngularJSTextInput())
    patronymic = StringField(u'Отчество<span class="text-danger">*</span>', widget=AngularJSTextInput())
    #BirthdayForm = FormField(BirthdayForm, label=u'Дата рождения')
    #birthDate = IntegerField(u'День рождения<span class="text-error">*</span>', [DataRequired(u'Обязательное поле')])
    # month = IntegerField(u'Месяц рождения<span class="text-error">*</span>', [DataRequired(u'Обязательное поле')])
    # year = IntegerField(u'Год рождения<span class="text-error">*</span>',
    #                     [DataRequired(u'Обязательное поле'), DateValidator('month', 'day')])
    gender = SelectField(u'Пол<span class="text-danger">*</span>', [Required()], choices=[(u'М', u'М'), (u'Ж', u'Ж')],
                         widget=AngularJSSelect())
    notes = TextAreaField(u'Примечания')
    document_number = StringField(u'Номер', widget=AngularJSTextInput())
    document_serial = StringField(u'Серия', widget=AngularJSTextInput())
    compulsory_policy_number = StringField(u'Номер', widget=AngularJSTextInput())
    compulsory_policy_serial = StringField(u'Серия', widget=AngularJSTextInput())
    voluntary_policy_number = StringField(u'Номер', widget=AngularJSTextInput())
    voluntary_policy_serial = StringField(u'Серия', widget=AngularJSTextInput())
    with app.app_context():
        document_type = SelectField(u'Тип', choices=[(doc_type.code, doc_type.name) for
                                    doc_type in rbDocumentType.query.all() if doc_type.group.code == '1'],
                                    widget=AngularJSSelect())
        ufms = SelectField(u'Выдан', choices=[(ufms.name, ufms.name) for ufms in rbUFMS.query.all()],
                           widget=AngularJSSelect())
        compulsory_policy_type = SelectField(u'Тип', choices=[(c_policy_type.code, c_policy_type.name) for
                                             c_policy_type in rbPolicyType.query.all() if
                                             c_policy_type.code in ('cmiOld', 'cmiTmp', 'cmiCommonPaper',
                                                                    'cmiCommonElectron', 'cmiUEC',
                                                                    'cmiFnkcIndustrial', 'cmiFnkcLocal')],
                                             widget=AngularJSSelect())
        compulsory_policy_org = SelectField(u'СМО', choices=[(org.id, org.shortName) for org in
                                            Organisation.query.all()], widget=AngularJSSelect())
        voluntary_policy_type = SelectField(u'Тип', choices=[(v_policy_type.code, v_policy_type.name) for
                                            v_policy_type in rbPolicyType.query.all() if v_policy_type.code in 'vmi'],
                                            widget=AngularJSSelect())
        voluntary_policy_org = SelectField(u'СМО', choices=[(org.id, org.shortName) for org in
                                           Organisation.query.all()], widget=AngularJSSelect())

    snils = StringField(u'СНИЛС', widget=AngularJSTextInput())