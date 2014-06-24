# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, TextAreaField, DateField
from wtforms.widgets import TextInput, Select
from wtforms.validators import DataRequired, Required

from application.app import app
from application.models.client import Client
from application.models.exists import (rbDocumentType, rbUFMS, rbPolicyType, Organisation, rbSocStatusType,
    rbSocStatusClass, rbBloodType, rbAccountingSystem, rbRelationType, rbContactType, Person)


class AngularJSTextInput(TextInput):
    def __call__(self, field, **kwargs):
        for key in list(kwargs):
            if key.startswith('ng_'):
                kwargs['ng-' + key[3:]] = kwargs.pop(key)
            if key.startswith('datepicker_'):
                kwargs['datepicker-' + key[3:]] = kwargs.pop(key)
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
    birthdate = DateField(u'Дата рождения<span class="text-danger">*</span>', [DataRequired()])
    gender = SelectField(u'Пол<span class="text-danger">*</span>', [Required()], choices=[(u'М', u'М'), (u'Ж', u'Ж')],
                         widget=AngularJSSelect())
    snils = StringField(u'СНИЛС', widget=AngularJSTextInput())
    notes = TextAreaField(u'Примечания')

    doc_type = SelectField(u'Тип', choices=[], widget=AngularJSSelect())
    doc_number = StringField(u'Номер', widget=AngularJSTextInput())
    doc_serial = StringField(u'Серия', widget=AngularJSTextInput())
    doc_begDate = DateField(u'Дата выдачи')
    doc_endDate = DateField(u'Действителен до')
    ufms = SelectField(u'Выдан', widget=AngularJSSelect())

    cpol_type = SelectField(u'Тип', widget=AngularJSSelect())
    cpol_number = StringField(u'Номер', widget=AngularJSTextInput())
    cpol_serial = StringField(u'Серия', widget=AngularJSTextInput())
    cpol_begDate = DateField(u'Дата выдачи')
    cpol_endDate = DateField(u'Действителен до')
    compulsory_policy_org = SelectField(u'СМО', widget=AngularJSSelect())

    vpol_type = SelectField(u'Тип', widget=AngularJSSelect())
    vpol_number = StringField(u'Номер', widget=AngularJSTextInput())
    vpol_serial = StringField(u'Серия', widget=AngularJSTextInput())
    vpol_begDate = DateField(u'Дата выдачи')
    vpol_endDate = DateField(u'Действителен до')
    vpol_org = SelectField(u'СМО', widget=AngularJSSelect())


    soc_status_class = SelectField(u'Тип', choices=[], widget=AngularJSSelect())
    soc_status_type = SelectField(u'Тип', choices=[], widget=AngularJSSelect())
    blood_group = SelectField(u'Группа крови', choices=[], widget=AngularJSSelect())
    blood_person = SelectField(u'Врач', choices=[], widget=AngularJSSelect())

    identification_accountingSystem = SelectField(u'Внешняя учетная система', choices=[], widget=AngularJSSelect())

    direct_relation_other = SelectField(u'Связан с пациентом', choices=[], widget=AngularJSSelect())
    reversed_relation_other = SelectField(u'Связан с пациентом', choices=[], widget=AngularJSSelect())
    contact_contactType = SelectField(u'Тип контакатаа', choices=[], widget=AngularJSSelect())


    soc_status_begDate = DateField(u'Дата начала')
    soc_status_endDate = DateField(u'Дата окончания')
    blood_date = DateField(u'Дата установления')
    allergy_createDate = DateField(u'Дата начала')
    intolerance_createDate = DateField(u'Дата начала')
    allergy_power = SelectField(u'Степень', choices=[(0, u'0 - не известно'), (1, u'1 - малая'),(2, u'2 - средняя'),
                                (3, u'3 - высокая'), (4, u'4 - строгая')], widget=AngularJSSelect())
    intolerance_power = SelectField(u'Степень', choices=[(0, u'0 - не известно'), (1, u'1 - малая'),(2, u'2 - средняя'),
                                    (3, u'3 - высокая'), (4, u'4 - строгая')], widget=AngularJSSelect())
    allergy_substance = StringField(u'Медикамент', widget=AngularJSTextInput())
    allergy_notes = StringField(u'Примечания', widget=AngularJSTextInput())
    intolerance_medicament = StringField(u'Медикамент', widget=AngularJSTextInput())
    intolerance_notes = StringField(u'Примечания', widget=AngularJSTextInput())

    identification_identifier = StringField(u'Идентификатор', widget=AngularJSTextInput())
    identification_checkDate = DateField(u'Дата подтверждения')

    contact_contact = StringField(u'Контакт', widget=AngularJSTextInput())
    contact_notes = StringField(u'Примечание', widget=AngularJSTextInput())

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        if not self.blood_group.choices:
            self.blood_group.choices = [(blood_type.code, blood_type.name) for blood_type in rbBloodType.query.all()]
        if not self.blood_group.choices:
            self.blood_group.choices = [(person.id, person.nameText) for person in Person.query.all()]
        if not self.identification_accountingSystem.choices:
            self.identification_accountingSystem.choices = [(system.code, system.name)
                                                            for system in rbAccountingSystem.query.all()]
        if not self.direct_relation_other.choices:
            self.direct_relation_other.choices = [(client.id, client.nameText) for client in Client.query.all()]
        if not self.reversed_relation_other.choices:
            self.reversed_relation_other.choices = [(client.id, client.nameText) for client in Client.query.all()]
        if not self.contact_contactType.choices:
            self.contact_contactType.choices = [(contact.code, contact.name) for contact in rbContactType.query.all()]