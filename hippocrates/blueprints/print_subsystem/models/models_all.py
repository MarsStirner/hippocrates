# -*- coding: utf-8 -*-

import calendar
from collections import defaultdict

from flask import g
import jinja2
from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey, Date, Float, or_, Boolean, Text, \
    SmallInteger, Time, Index, BigInteger, Enum, Table, BLOB, UnicodeText


# from application.database import db
from sqlalchemy.orm import relationship, backref
from ..config import MODULE_NAME
from ..lib.html import convenience_HtmlRip, replace_first_paragraph
from ..lib.num_to_text_converter import NumToTextConverter
from models_utils import *
from kladr_models import Kladr, Street
from ..database import Base, metadata
from sqlalchemy.dialects.mysql.base import MEDIUMBLOB


TABLE_PREFIX = MODULE_NAME


class ConfigVariables(Base):
    __bind_key__ = 'caesar'
    __tablename__ = '%s_config' % TABLE_PREFIX

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(25), unique=True, nullable=False)
    name = Column(Unicode(50), unique=True, nullable=False)
    value = Column(Unicode(100))
    value_type = Column(String(30))

    def __unicode__(self):
        return self.code


class Info(Base):
    u"""Базовый класс для представления объектов при передаче в шаблоны печати"""
    __abstract__ = True

    def __cmp__(self, x):
        ss = unicode(self)
        sx = unicode(x)
        if ss > sx:
            return 1
        elif ss < sx:
            return -1
        else:
            return 0

    def __add__(self, x):
        return unicode(self) + unicode(x)

    def __radd__(self, x):
        return unicode(x) + unicode(self)


class RBInfo(Info):
    __abstract__ = True
    
    def __init__(self):
        self.code = ""
        self.name = ""

    def __unicode__(self):
        return self.name


class Account(Info):
    __tablename__ = u'Account'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    contract_id = Column(Integer, ForeignKey('Contract.id'), nullable=False, index=True)
    orgStructure_id = Column(Integer, ForeignKey('OrgStructure.id'))
    payer_id = Column(Integer, ForeignKey('Organisation.id'), nullable=False, index=True)
    settleDate = Column(Date, nullable=False)
    number = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    uet = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    sum = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    exposeDate = Column(Date)
    payedAmount = Column(Float(asdecimal=True), nullable=False)
    payedSum = Column(Float(asdecimal=True), nullable=False)
    refusedAmount = Column(Float(asdecimal=True), nullable=False)
    refusedSum = Column(Float(asdecimal=True), nullable=False)
    format_id = Column(Integer, ForeignKey('rbAccountExportFormat.id'), index=True)

    payer = relationship(u'Organisation')
    orgStructure = relationship(u'Orgstructure')
    contract = relationship(u'Contract')
    format = relationship(u'Rbaccountexportformat')
    items = relationship(u'AccountItem')

    @property
    def sumInWords(self):
        sum_conv = NumToTextConverter(self.sum)
        return sum_conv.convert().getRubText() + sum_conv.convert().getKopText()

    def __unicode__(self):
        return u'%s от %s' % (self.number, self.date)


class AccountItem(Info):
    __tablename__ = u'Account_Item'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, ForeignKey('Account.id'), nullable=False, index=True)
    serviceDate = Column(Date, server_default=u"'0000-00-00'")
    event_id = Column(Integer, ForeignKey('Event.id'), index=True)
    visit_id = Column(Integer, ForeignKey('Visit.id'), index=True)
    action_id = Column(Integer, ForeignKey('Action.id'), index=True)
    price = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(Integer, ForeignKey('rbMedicalAidUnit.id'), index=True)
    amount = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    uet = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    sum = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    date = Column(Date)
    number = Column(String(20), nullable=False)
    refuseType_id = Column(Integer, ForeignKey('rbPayRefuseType.id'), index=True)
    reexposeItem_id = Column(Integer, ForeignKey('Account_Item.id'), index=True)
    note = Column(String(256), nullable=False)
    tariff_id = Column(Integer, ForeignKey('Contract_Tariff.id'), index=True)
    service_id = Column(Integer, ForeignKey('rbService.id'))
    paymentConfirmationDate = Column(Date)

    event = relationship(u'Event')
    visit = relationship(u'Visit')
    action = relationship(u'Action')
    refuseType = relationship(u'Rbpayrefusetype')
    reexposeItem = relationship(u'AccountItem', remote_side=[id])
    service = relationship(u'Rbservice')
    unit = relationship(u'Rbmedicalaidunit')

    @property
    def sumInWords(self):
        sum_conv = NumToTextConverter(self.sum)
        return sum_conv.convert().getRubText() + sum_conv.convert().getKopText()

    def __unicode__(self):
        return u'%s %s %s' % (self.serviceDate, self.event.client, self.sum)


class Action(Info):
    __tablename__ = u'Action'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    actionType_id = Column(Integer, ForeignKey('ActionType.id'), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey('Event.id'), index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    directionDate_raw = Column("directionDate", DateTime)
    status = Column(Integer, nullable=False)
    setPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    isUrgent = Column(Boolean, nullable=False, server_default=u"'0'")
    begDate_raw = Column("begDate", DateTime)
    plannedEndDate_raw = Column("plannedEndDate", DateTime, nullable=False)
    endDate_raw = Column("endDate", DateTime)
    note = Column(Text, nullable=False)
    person_id = Column(Integer, ForeignKey('Person.id'), index=True)
    office = Column(String(16), nullable=False)
    amount = Column(Float, nullable=False)
    uet = Column(Float, server_default=u"'0'")
    expose = Column(Boolean, nullable=False, server_default=u"'1'")
    payStatus = Column(Integer, nullable=False)
    account = Column(Boolean, nullable=False)
    finance_id = Column(Integer, ForeignKey('rbFinance.id'), index=True)
    prescription_id = Column(Integer, index=True)
    takenTissueJournal_id = Column(ForeignKey('TakenTissueJournal.id'), index=True)
    contract_id = Column(ForeignKey('Contract.id'), index=True)
    coordDate_raw = Column("coordDate", DateTime)
    coordAgent = Column(String(128), nullable=False, server_default=u"''")
    coordInspector = Column(String(128), nullable=False, server_default=u"''")
    coordText = Column(String, nullable=False)
    hospitalUidFrom = Column(String(128), nullable=False, server_default=u"'0'")
    pacientInQueueType = Column(Integer, server_default=u"'0'")
    AppointmentType = Column(Enum(u'0', u'amb', u'hospital', u'polyclinic', u'diagnostics', u'portal', u'otherLPU'),
                                nullable=False)
    version = Column(Integer, nullable=False, server_default=u"'0'")
    parentAction_id = Column(Integer, index=True)
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    dcm_study_uid = Column(String(50))

    actionType = relationship(u'Actiontype')
    event = relationship(u'Event')
    person = relationship(u'Person', foreign_keys='Action.person_id')
    setPerson = relationship(u'Person', foreign_keys='Action.setPerson_id')
    takenTissue = relationship(u'Takentissuejournal')
    tissues = relationship(u'Tissue', secondary=u'ActionTissue')
    properties = relationship(u'ActionProperty',
                                 primaryjoin="and_(ActionProperty.action_id==Action.id, ActionProperty.type_id==Actionpropertytype.id)",
                                 order_by="Actionpropertytype.idx")
    self_contract = relationship('Contract')
    bbt_response = relationship(u'BbtResponse', uselist=False)

    # def getPrice(self, tariffCategoryId=None):
    #     if self.price is None:
    #         event = self.getEventInfo()
    #         tariffDescr = event.getTariffDescr()
    #         tariffList = tariffDescr.actionTariffList
    #         serviceId = self.service.id
    #         tariffCategoryId = self.person.tariffCategory.id
    #         self._price = CContractTariffCache.getPrice(tariffList, serviceId, tariffCategoryId)
    #     return self._price

    @property
    def begDate(self):
        return DateTimeInfo(self.begDate_raw)

    @property
    def endDate(self):
        return DateTimeInfo(self.endDate_raw)

    @property
    def directionDate(self):
        return DateTimeInfo(self.directionDate_raw)

    @property
    def plannedEndDate(self):
        return DateTimeInfo(self.plannedEndDate_raw)

    @property
    def coordDate(self):
        return DateTimeInfo(self.coordDate_raw)

    @property
    def finance(self):
        if self.contract_id:
            return self.self_contract.finance
        elif self.event:
            return self.event.contract.finance

    @property
    def contract(self):
        if self.contract_id:
            return self.self_contract
        elif self.event:
            return self.event.contract

    def get_property_by_code(self, code):
        for property in self.properties:
            if property.type.code == code:
                return property
        property_type = self.actionType.get_property_type_by_code(code)
        if property_type:
            return property_type.default_value()
        return None

    def get_property_by_name(self, name):
        for property in self.properties:
            if property.type.name == unicode(name):
                return property
        property_type = self.actionType.get_property_type_by_name(name)
        if property_type:
            return property_type
        return None

    def get_property_by_index(self, index):
        self.properties = sorted(self.properties, key=lambda prop: prop.type.idx)
        return self.properties[index]

    @property
    def group(self):
        return self.actionType.group if self.actionType else None

    @property
    def class_(self):
        return self.actionType.class_ if self.actionType else None

    @property
    def code(self):
        return self.actionType.code if self.actionType else None

    @property
    def flatCode(self):
        return self.actionType.flatCode if self.actionType else None

    @property
    def name(self):
        return self.actionType.name if self.actionType else None

    @property
    def title(self):
        return self.actionType.title if self.actionType else None

    @property
    def service(self):
        # пока отключено, т.к. по процессу не используется в амбулатории

        # finance = self.finance
        # if finance:
        #     if not hasattr(self, '_finance_service'):
        #         _finance_service = g.printing_session.query(ActiontypeService).filter(
        #             ActiontypeService.master_id == self.actionType_id,
        #             ActiontypeService.finance_id == finance.id,
        #         ).first()
        #         self._finance_service = _finance_service
        #     if self._finance_service:
        #         return self._finance_service.service
        return self.actionType.service if self.actionType else None

    @property
    def showTime(self):
        return self.actionType.showTime if self.actionType else None

    @property
    def isMes(self):
        return self.actionType.isMes if self.actionType else None

    @property
    def nomenclatureService(self):
        return self.actionType.nomenclatureService if self.actionType else None

    @property
    def tariff(self):
        service = self.service
        if not service:
            return
        if not hasattr(self, '_tariff'):
            contract = self.contract
            tariff = None
            _tc_id = self.person.tariffCategory_id if self.person else None
            query_1 = g.printing_session.query(ContractTariff).filter(
                ContractTariff.deleted == 0,
                ContractTariff.master_id == contract.id,
                or_(
                    ContractTariff.eventType_id == self.event.eventType_id,
                    ContractTariff.eventType_id.is_(None)
                ),
                ContractTariff.tariffType == 2,
                ContractTariff.service_id == service.id
            )
            query_2 = query_1.filter(
                or_(
                    ContractTariff.tariffCategory_id == _tc_id,
                    ContractTariff.tariffCategory_id.is_(None)
                )
            ) if _tc_id else None
            query_3 = query_1.filter(
                ContractTariff.begDate >= self.begDate_raw,
                ContractTariff.endDate < self.begDate_raw
            ) if self.begDate_raw else None
            query_4 = query_1.filter(
                or_(
                    ContractTariff.tariffCategory_id == _tc_id,
                    ContractTariff.tariffCategory_id.is_(None)
                ),
                ContractTariff.begDate >= self.begDate_raw,
                ContractTariff.endDate < self.begDate_raw
            ) if _tc_id and self.begDate_raw else None
            for query in (query_4, query_3, query_2, query_1):
                if query is None:
                    continue
                tariff = query.first()
                if tariff:
                    break
            self._tariff = tariff
        return self._tariff

    @property
    def price(self):
        tariff = self.tariff
        if tariff:
            return tariff.price
        return 0.0

    @property
    def sum_total(self):
        return self.price * self.amount

    # @property
    # def isHtml(self):
    #     return self.actionType.isHtml if self.actionType else None

    def __iter__(self):
        for property in self.properties:
            yield property

    def __getitem__(self, key):
        if isinstance(key, basestring):
            return self.get_property_by_name(unicode(key))
        elif isinstance(key, tuple):
            return self.get_property_by_code(unicode(key[0]))
        elif isinstance(key, (int, long)):
            return self.get_property_by_index(key)


class ActionProperty(Info):
    __tablename__ = u'ActionProperty'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    action_id = Column(Integer, ForeignKey('Action.id'), nullable=False, index=True)
    type_id = Column(Integer, ForeignKey('ActionPropertyType.id'), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey('rbUnit.id'), index=True)
    norm = Column(String(64), nullable=False, default='')
    isAssigned = Column(Boolean, nullable=False, server_default=u"'0'")
    evaluation = Column(Integer, default=None)
    version = Column(Integer, nullable=False, server_default=u"'0'")

    action = relationship(u'Action')
    type = relationship(u'Actionpropertytype')
    unit_all = relationship(u'Rbunit')

    def get_value_class(self):
        # Следующая магия вытаскивает класс, ассоциированный с backref-пропертей, созданной этим же классом у нашего
        # ActionProperty. Объекты этого класса мы будем создавать для значений
        return getattr(self.__class__, self.__get_property_name()).property.mapper.class_

    def __get_property_name(self):
        return '_value_%s' % self.type.get_appendix()

    def get_value_instance(self):
        class_name = 'ActionProperty_%s' % self.type.get_appendix()
        cls = globals().get(class_name)
        if cls is not None:
            instance = cls()
            instance.property_object = self
            instance.idx = 0
            return instance

    @property
    def value_object(self):
        return getattr(self, self.__get_property_name())

    @value_object.setter
    def value_object(self, value):
        setattr(self, self.__get_property_name(), value)

    @property
    def value(self):
        value_object = self.value_object

        if not value_object:
            value_object = [self.get_value_instance()]

        if self.type.isVector:
            return [item.value for item in value_object]
        else:
            return value_object[0].value

    @property
    def name(self):
        return self.type.name

    @property
    def descr(self):
        return self.type.descr

    @property
    def unit(self):
        return self.unit_all.code

    @property
    def isAssignable(self):
        return self.type.isAssignable

    #     if self.type.typeName == "Table":
    #         return values[0].get_value(self.type.valueDomain) if values else ""

    def __nonzero__(self):
        return bool(self.value_object is not None and (self.value or self.value == 0))

    def __unicode__(self):
        if self.type.isVector:
            return ', '.join([unicode(item) for item in self.value])
        else:
            return unicode(self.value)
    # image = property(lambda self: self._property.getImage())
    # imageUrl = property(_getImageUrl)


class Actionpropertytemplate(Info):
    __tablename__ = u'ActionPropertyTemplate'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    group_id = Column(Integer, index=True)
    parentCode = Column(String(20), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    federalCode = Column(String(64), nullable=False, index=True)
    regionalCode = Column(String(64), nullable=False)
    name = Column(String(120), nullable=False, index=True)
    abbrev = Column(String(64), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    service_id = Column(Integer, index=True)


class Actionpropertytype(Info):
    __tablename__ = u'ActionPropertyType'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    actionType_id = Column(Integer, ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    template_id = Column(Integer, index=True)
    name = Column(String(128), nullable=False)
    descr = Column(String(128), nullable=False)
    unit_id = Column(Integer, index=True)
    typeName = Column(String(64), nullable=False)
    valueDomain = Column(Text, nullable=False)
    defaultValue = Column(String(5000), nullable=False)
    isVector = Column(Integer, nullable=False, server_default=u"'0'")
    norm = Column(String(64), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    penalty = Column(Integer, nullable=False, server_default=u"'0'")
    visibleInJobTicket = Column(Integer, nullable=False, server_default=u"'0'")
    isAssignable = Column(Integer, nullable=False, server_default=u"'0'")
    test_id = Column(Integer, index=True)
    defaultEvaluation = Column(Integer, nullable=False, server_default=u"'0'")
    toEpicrisis = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(25), index=True)
    mandatory = Column(Integer, nullable=False, server_default=u"'0'")
    readOnly = Column(Integer, nullable=False, server_default=u"'0'")
    createDatetime = Column(DateTime, nullable=False, index=True)
    createPerson_id = Column(Integer)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer)

    def get_appendix(self):
        type_name = self.typeName
        if type_name in ["Constructor", u"Жалобы"]:
            return 'Text'
        elif type_name == u"Запись в др. ЛПУ":
            return 'OtherLPURecord'
        elif type_name == "FlatDirectory":
            return 'FDRecord'
        return type_name


class ActionProperty__ValueType(Info):
    __abstract__ = True

    @classmethod
    def format_value(cls, prop, json_data):
        return json_data


class ActionProperty_Action(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Action'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('Action.id'), index=True)

    value = relationship('Action')
    property_object = relationship('ActionProperty', backref='_value_Action')


class ActionProperty_Date(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Date'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', Date)

    @property
    def value(self):
        return DateInfo(self.value_) if self.value_ else ''
    property_object = relationship('ActionProperty', backref='_value_Date')


class ActionProperty_Double(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Double'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = Column(Float, nullable=False)
    property_object = relationship('ActionProperty', backref='_value_Double')


class ActionProperty_FDRecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_FDRecord'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True)
    index = Column(Integer, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('FDRecord.id'), nullable=False, index=True)

    property_object = relationship('ActionProperty', backref='_value_FDRecord')

    @property
    def value(self):
        return g.printing_session.query(Fdrecord).filter(Fdrecord.id == self.value_).first().get_value()


class ActionProperty_HospitalBed(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBed'

    id = Column(ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('OrgStructure_HospitalBed.id'), index=True)

    value = relationship(u'OrgstructureHospitalbed')
    property_object = relationship('ActionProperty', backref='_value_HospitalBed')


class ActionProperty_HospitalBedProfile(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBedProfile'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('rbHospitalBedProfile.id'), index=True)

    value = relationship('Rbhospitalbedprofile')
    property_object = relationship('ActionProperty', backref='_value_HospitalBedProfile')


class ActionProperty_Image(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Image'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = Column(BLOB)
    property_object = relationship('ActionProperty', backref='_value_Image')


class ActionProperty_ImageMap(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_ImageMap'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = Column(String)
    property_object = relationship('ActionProperty', backref='_value_ImageMap')


class ActionProperty_Diagnosis(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Diagnosis'
    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('Diagnostic.id'), nullable=False)

    value_model = relationship('Diagnostic')
    property_object = relationship('ActionProperty', backref='_value_Diagnosis')

    @property
    def value(self):
        return self.value_model

    @value.setter
    def value(self, val):
        if self.value_model is not None and self.value_model in g.printing_session and self.value_model.id == val.id:
            self.value_model = g.printing_session.merge(val)
        else:
            self.value_model = val


class ActionProperty_Integer_Base(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Integer'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', Integer, nullable=False)


class ActionProperty_Integer(ActionProperty_Integer_Base):
    property_object = relationship('ActionProperty', backref='_value_Integer')

    @property
    def value(self):
        return self.value_

    @value.setter
    def value(self, val):
        self.value_ = val


class ActionProperty_AnalysisStatus(ActionProperty_Integer_Base):
    property_object = relationship('ActionProperty', backref='_value_AnalysisStatus')

    @property
    def value(self):
        return g.printing_session.query(Rbanalysisstatus).get(self.value_) if self.value_ else None

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None


class ActionProperty_OperationType(ActionProperty_Integer_Base):
    property_object = relationship('ActionProperty', backref='_value_OperationType')

    @property
    def value(self):
        return g.printing_session.query(Rboperationtype).get(self.value_) if self.value_ else None

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None


class ActionProperty_JobTicket(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Job_Ticket'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('Job_Ticket.id'), index=True)

    value = relationship('JobTicket')
    property_object = relationship('ActionProperty', backref='_value_JobTicket')


class ActionProperty_MKB(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_MKB'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('MKB.id'), index=True)

    value = relationship('Mkb')
    property_object = relationship('ActionProperty', backref='_value_MKB')


class ActionProperty_OrgStructure(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OrgStructure'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('OrgStructure.id'), index=True)

    value = relationship('Orgstructure')
    property_object = relationship('ActionProperty', backref='_value_OrgStructure')


class ActionProperty_Organisation(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Organisation'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('Organisation.id'), index=True)

    value = relationship('Organisation')
    property_object = relationship('ActionProperty', backref='_value_Organisation')


class ActionProperty_OtherLPURecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OtherLPURecord'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)

    property_object = relationship('ActionProperty', backref='_value_OtherLPURecord')


class ActionProperty_Person(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Person'

    id = Column(ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('Person.id'), index=True)

    value = relationship(u'Person')
    property_object = relationship('ActionProperty', backref='_value_Person')


class ActionProperty_String_Base(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_String'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', Text, nullable=False)


class ActionProperty_String(ActionProperty_String_Base):
    property_object = relationship('ActionProperty', backref='_value_String')

    @property
    def value(self):
        return self.value_ if self.value_ else ''


class ActionProperty_Text(ActionProperty_String_Base):
    property_object = relationship('ActionProperty', backref='_value_Text')

    @property
    def value(self):
        return replace_first_paragraph(convenience_HtmlRip(self.value_)) if self.value_ else ''


class ActionProperty_Html(ActionProperty_String_Base):
    property_object = relationship('ActionProperty', backref='_value_Html')

    @property
    def value(self):
        return convenience_HtmlRip(self.value_) if self.value_ else ''


class ActionProperty_Table(ActionProperty_Integer_Base):
    property_object = relationship('ActionProperty', backref='_value_Table')

    @property
    def value(self):
        table_code = self.property_object.type.valueDomain
        trfu_tables = {"trfuOrderIssueResult": Trfuorderissueresult, "trfuLaboratoryMeasure": Trfulaboratorymeasure,
                       "trfuFinalVolume": Trfufinalvolume}
        table = g.printing_session.query(Rbaptable).filter(Rbaptable.code == table_code).first()
        field_names = [field.name for field in table.fields]
        table_filed_names = [field.fieldName for field in table.fields]
        value_table_name = table.tableName
        master_field = table.masterField
        values = g.printing_session.query(trfu_tables[value_table_name]).filter("{0}.{1} = {2}".format(
            value_table_name,
            master_field,
            self.value_)
        ).all()
        template = u'''
                    <table width="100%" border="1" align="center" style="border-style:solid;" cellspacing="0">
                        <thead><tr>{% for col in field_names %}<th>{{ col }}</th>{% endfor %}</tr></thead>
                        {% for row in range(values|length) %}<tr>
                            {% for col in table_filed_names %}<td align="center" valign="middle">
                            {{values[row][col]}}
                            </td>{% endfor %}
                        </tr>{% endfor %}
                    </table>
                    '''
        return jinja2.Template(template).render(field_names=field_names, table_filed_names=table_filed_names, values=values)


class ActionProperty_Time(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Time'

    id = Column(Integer, ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', Time, nullable=False)
    property_object = relationship('ActionProperty', backref='_value_Time')

    @property
    def value(self):
        return TimeInfo(self.value_) if self.value_ else ''

    def __str__(self):
        return self.value


class ActionProperty_RLS(ActionProperty_Integer_Base):

    @property
    def value(self):
        return g.printing_session.query(v_Nomen).get(self.value_).first() if self.value_ else None
    property_object = relationship('ActionProperty', backref='_value_RLS')


class ActionProperty_ReferenceRb(ActionProperty_Integer_Base):

    @property
    def value(self):
        if not self.value_:
            return None
        if not hasattr(self, 'table_name'):
            domain = self.property_object.type.valueDomain
            self.table_name = domain.split(';')[0]
        model = get_model_by_name(self.table_name)
        return g.printing_session.query(model).get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None

    property_object = relationship('ActionProperty', backref='_value_ReferenceRb')


class ActionProperty_rbBloodComponentType(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbBloodComponentType'

    id = Column(ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False)
    value_ = Column('value', ForeignKey('rbTrfuBloodComponentType.id'), nullable=False)

    value = relationship('Rbtrfubloodcomponenttype')
    property_object = relationship('ActionProperty', backref='_value_rbBloodComponentType')


class ActionProperty_rbFinance(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbFinance'

    id = Column(ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('rbFinance.id'), index=True)

    value = relationship('Rbfinance')
    property_object = relationship('ActionProperty', backref='_value_rbFinance')


class ActionProperty_rbReasonOfAbsence(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbReasonOfAbsence'

    id = Column(ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = Column('value', ForeignKey('rbReasonOfAbsence.id'), index=True)

    value = relationship('Rbreasonofabsence')
    property_object = relationship('ActionProperty', backref='_value_rbReasonOfAbsence')


class Actiontemplate(Info):
    __tablename__ = u'ActionTemplate'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    group_id = Column(Integer, index=True)
    code = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    owner_id = Column(Integer, index=True)
    speciality_id = Column(Integer, index=True)
    action_id = Column(Integer, index=True)


t_ActionTissue = Table(
    u'ActionTissue', metadata,
    Column(u'action_id', ForeignKey('Action.id'), primary_key=True, nullable=False, index=True),
    Column(u'tissue_id', ForeignKey('Tissue.id'), primary_key=True, nullable=False, index=True)
)


class Actiontype(Info):
    __tablename__ = u'ActionType'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    hidden = Column(Integer, nullable=False, server_default=u"'0'")
    class_ = Column(u'class', Integer, nullable=False, index=True)
    group_id = Column(Integer, ForeignKey('ActionType.id'), index=True)
    code = Column(String(25), nullable=False)
    name = Column(Unicode(255), nullable=False)
    title = Column(Unicode(255), nullable=False)
    flatCode = Column(String(64), nullable=False, index=True)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    office = Column(String(32), nullable=False)
    showInForm = Column(Integer, nullable=False)
    genTimetable = Column(Integer, nullable=False)
    service_id = Column(Integer, ForeignKey('rbService.id'), index=True)
    quotaType_id = Column(Integer, index=True)
    context = Column(String(64), nullable=False)
    amount = Column(Float(asdecimal=True), nullable=False, server_default=u"'1'")
    amountEvaluation = Column(Integer, nullable=False, server_default=u"'0'")
    defaultStatus = Column(Integer, nullable=False, server_default=u"'0'")
    defaultDirectionDate = Column(Integer, nullable=False, server_default=u"'0'")
    defaultPlannedEndDate = Column(Integer, nullable=False)
    defaultEndDate = Column(Integer, nullable=False, server_default=u"'0'")
    defaultExecPerson_id = Column(Integer, index=True)
    defaultPersonInEvent = Column(Integer, nullable=False, server_default=u"'0'")
    defaultPersonInEditor = Column(Integer, nullable=False, server_default=u"'0'")
    maxOccursInEvent = Column(Integer, nullable=False, server_default=u"'0'")
    showTime = Column(Integer, nullable=False, server_default=u"'0'")
    isMES = Column(Integer)
    nomenclativeService_id = Column(Integer, ForeignKey('rbService.id'), index=True)
    isPreferable = Column(Integer, nullable=False, server_default=u"'1'")
    prescribedType_id = Column(Integer, index=True)
    shedule_id = Column(Integer, index=True)
    isRequiredCoordination = Column(Integer, nullable=False, server_default=u"'0'")
    isRequiredTissue = Column(Integer, nullable=False, server_default=u"'0'")
    testTubeType_id = Column(Integer, index=True)
    jobType_id = Column(Integer, index=True)
    mnem = Column(String(32), server_default=u"''")

    service = relationship(u'Rbservice', foreign_keys='Actiontype.service_id')
    nomenclatureService = relationship(u'Rbservice', foreign_keys='Actiontype.nomenclativeService_id')
    property_types = relationship(u'Actionpropertytype')
    group = relationship(u'Actiontype', remote_side=[id])

    def get_property_type_by_name(self, name):
        for property_type in self.property_types:
            if property_type.name == unicode(name):
                return property_type
        return None

    def get_property_type_by_code(self, code):
        for property_type in self.property_types:
            if property_type.name == code:
                return property_type
        return None


class ActiontypeEventtypeCheck(Info):
    __tablename__ = u'ActionType_EventType_check'

    id = Column(Integer, primary_key=True)
    actionType_id = Column(ForeignKey('ActionType.id'), nullable=False, index=True)
    eventType_id = Column(ForeignKey('EventType.id'), nullable=False, index=True)
    related_actionType_id = Column(ForeignKey('ActionType.id'), index=True)
    relationType = Column(Integer)

    actionType = relationship(u'Actiontype', primaryjoin='ActiontypeEventtypeCheck.actionType_id == Actiontype.id')
    eventType = relationship(u'Eventtype')
    related_actionType = relationship(u'Actiontype', primaryjoin='ActiontypeEventtypeCheck.related_actionType_id == Actiontype.id')


class ActiontypeQuotatype(Info):
    __tablename__ = u'ActionType_QuotaType'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    quotaClass = Column(Integer)
    finance_id = Column(Integer, index=True)
    quotaType_id = Column(Integer, index=True)


class ActiontypeService(Info):
    __tablename__ = u'ActionType_Service'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    finance_id = Column(ForeignKey('rbFinance.id'), index=True)
    service_id = Column(ForeignKey('rbService.id'), index=True)

    action_type = relationship('Actiontype')
    finance = relationship('Rbfinance')
    service = relationship('Rbservice')

class ActiontypeTissuetype(Info):
    __tablename__ = u'ActionType_TissueType'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    tissueType_id = Column(ForeignKey('rbTissueType.id'), index=True)
    amount = Column(Integer, nullable=False, server_default=u"'0'")
    unit_id = Column(ForeignKey('rbUnit.id'), index=True)

    master = relationship(u'Actiontype')
    tissueType = relationship(u'Rbtissuetype')
    unit = relationship(u'Rbunit')


class ActiontypeUser(Info):
    __tablename__ = u'ActionType_User'
    __table_args__ = (
        Index(u'person_id_profile_id', u'person_id', u'profile_id'),
    )

    id = Column(Integer, primary_key=True)
    actionType_id = Column(ForeignKey('ActionType.id'), nullable=False, index=True)
    person_id = Column(ForeignKey('Person.id'))
    profile_id = Column(ForeignKey('rbUserProfile.id'), index=True)

    actionType = relationship(u'Actiontype')
    person = relationship(u'Person')
    profile = relationship(u'Rbuserprofile')


class Address(Info):
    __tablename__ = u'Address'
    __table_args__ = (
        Index(u'house_id', u'house_id', u'flat'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    house_id = Column(Integer, ForeignKey('AddressHouse.id'), nullable=False)
    flat = Column(String(6), nullable=False)

    house = relationship(u'Addresshouse')

    @property
    def KLADRCode(self):
        return self.house.KLADRCode

    @property
    def KLADRStreetCode(self):
        return self.house.KLADRStreetCode

    @property
    def city(self):
        from models_utils import get_kladr_city  # TODO: fix?
        text = ''
        if self.KLADRCode:
            city_info = get_kladr_city(self.KLADRCode)
            text = city_info.get('fullname', u'-код региона не найден в кладр-')
        return text

    @property
    def city_old(self):
        if self.KLADRCode:
            record = g.printing_session.query(Kladr).filter(Kladr.CODE == self.KLADRCode).first()
            name = [" ".join([record.NAME, record.SOCR])]
            parent = record.parent
            while parent:
                record = g.printing_session.query(Kladr).filter(Kladr.CODE == parent.ljust(13, "0")).first()
                name.insert(0, " ".join([record.NAME, record.SOCR]))
                parent = record.parent
            return ", ".join(name)
        else:
            return ''

    @property
    def town(self):
        return self.city

    @property
    def text(self):
        parts = [self.city]
        if self.street:
            parts.append(self.street)
        if self.number:
            parts.append(u'д.'+self.number)
        if self.corpus:
            parts.append(u'к.'+self.corpus)
        if self.flat:
            parts.append(u'кв.'+self.flat)
        return (', '.join(parts)).strip()

    @property
    def number(self):
        return self.house.number

    @property
    def corpus(self):
        return self.house.corpus

    @property
    def street(self):
        from models_utils import get_kladr_street  # TODO: fix?
        text = ''
        if self.KLADRStreetCode:
            street_info = get_kladr_street(self.KLADRStreetCode)
            text = street_info.get('name', u'-код улицы не найден в кладр-')
        return text

    @property
    def street_old(self):
        if self.KLADRStreetCode:
            record = g.printing_session.query(Street).filter(Street.CODE == self.KLADRStreetCode).first()
            return record.NAME + " " + record.SOCR
        else:
            return ''

    def __unicode__(self):
        return self.text


class Addressareaitem(Info):
    __tablename__ = u'AddressAreaItem'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    LPU_id = Column(Integer, nullable=False, index=True)
    struct_id = Column(Integer, nullable=False, index=True)
    house_id = Column(Integer, nullable=False, index=True)
    flatRange = Column(Integer, nullable=False)
    begFlat = Column(Integer, nullable=False)
    endFlat = Column(Integer, nullable=False)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date)


class Addresshouse(Info):
    __tablename__ = u'AddressHouse'
    __table_args__ = (
        Index(u'KLADRCode', u'KLADRCode', u'KLADRStreetCode', u'number', u'corpus'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    KLADRCode = Column(String(13), nullable=False)
    KLADRStreetCode = Column(String(17), nullable=False)
    number = Column(String(8), nullable=False)
    corpus = Column(String(8), nullable=False)


class Applock(Info):
    __tablename__ = u'AppLock'

    id = Column(BigInteger, primary_key=True)
    lockTime = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    retTime = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    connectionId = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    person_id = Column(Integer)
    addr = Column(String(255), nullable=False)


t_AppLock_Detail = Table(
    u'AppLock_Detail', metadata,
    Column(u'master_id', BigInteger, nullable=False, index=True),
    Column(u'tableName', String(64), nullable=False),
    Column(u'recordId', Integer, nullable=False),
    Column(u'recordIndex', Integer, nullable=False, server_default=u"'0'"),
    Index(u'rec', u'recordId', u'tableName')
)


t_AssignmentHour = Table(
    u'AssignmentHour', metadata,
    Column(u'action_id', Integer, nullable=False),
    Column(u'createDatetime', DateTime, nullable=False),
    Column(u'hour', Integer),
    Column(u'complete', Integer, server_default=u"'0'"),
    Column(u'comments', String(120))
)


class Bank(Info):
    __tablename__ = u'Bank'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    bik = Column("BIK", String(10), nullable=False, index=True)
    name = Column(Unicode(100), nullable=False, index=True)
    branchName = Column(Unicode(100), nullable=False)
    corrAccount = Column(String(20), nullable=False)
    subAccount = Column(String(20), nullable=False)


class Blankaction(Info):
    __tablename__ = u'BlankActions'

    id = Column(Integer, primary_key=True)
    doctype_id = Column(ForeignKey('ActionType.id'), index=True)
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    checkingSerial = Column(Integer, nullable=False)
    checkingNumber = Column(Integer, nullable=False)
    checkingAmount = Column(Integer, nullable=False)

    doctype = relationship(u'Actiontype')


class BlankactionsMoving(Info):
    __tablename__ = u'BlankActions_Moving'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False)
    blankParty_id = Column(ForeignKey('BlankActions_Party.id'), nullable=False, index=True)
    serial = Column(String(8), nullable=False)
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    received = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    returnDate = Column(Date)
    returnAmount = Column(Integer, nullable=False, server_default=u"'0'")

    blankParty = relationship(u'BlankactionsParty')
    createPerson = relationship(u'Person', primaryjoin='BlankactionsMoving.createPerson_id == Person.id')
    modifyPerson = relationship(u'Person', primaryjoin='BlankactionsMoving.modifyPerson_id == Person.id')
    orgStructure = relationship(u'Orgstructure')
    person = relationship(u'Person', primaryjoin='BlankactionsMoving.person_id == Person.id')


class BlankactionsParty(Info):
    __tablename__ = u'BlankActions_Party'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False)
    doctype_id = Column(ForeignKey('rbBlankActions.id'), nullable=False, index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    serial = Column(String(8), nullable=False)
    numberFrom = Column(String(16), nullable=False)
    numberTo = Column(String(16), nullable=False)
    amount = Column(Integer, nullable=False, server_default=u"'0'")
    extradited = Column(Integer, nullable=False, server_default=u"'0'")
    balance = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    writing = Column(Integer, nullable=False, server_default=u"'0'")

    createPerson = relationship(u'Person', primaryjoin='BlankactionsParty.createPerson_id == Person.id')
    doctype = relationship(u'Rbblankaction')
    modifyPerson = relationship(u'Person', primaryjoin='BlankactionsParty.modifyPerson_id == Person.id')
    person = relationship(u'Person', primaryjoin='BlankactionsParty.person_id == Person.id')


class BlanktempinvalidMoving(Info):
    __tablename__ = u'BlankTempInvalid_Moving'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False)
    blankParty_id = Column(ForeignKey('BlankTempInvalid_Party.id'), nullable=False, index=True)
    serial = Column(String(8), nullable=False)
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    received = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    returnDate = Column(Date)
    returnAmount = Column(Integer, nullable=False, server_default=u"'0'")

    blankParty = relationship(u'BlanktempinvalidParty')
    createPerson = relationship(u'Person', primaryjoin='BlanktempinvalidMoving.createPerson_id == Person.id')
    modifyPerson = relationship(u'Person', primaryjoin='BlanktempinvalidMoving.modifyPerson_id == Person.id')
    orgStructure = relationship(u'Orgstructure')
    person = relationship(u'Person', primaryjoin='BlanktempinvalidMoving.person_id == Person.id')


class BlanktempinvalidParty(Info):
    __tablename__ = u'BlankTempInvalid_Party'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False)
    doctype_id = Column(ForeignKey('rbBlankTempInvalids.id'), nullable=False, index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    serial = Column(String(8), nullable=False)
    numberFrom = Column(String(16), nullable=False)
    numberTo = Column(String(16), nullable=False)
    amount = Column(Integer, nullable=False, server_default=u"'0'")
    extradited = Column(Integer, nullable=False, server_default=u"'0'")
    balance = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    writing = Column(Integer, nullable=False, server_default=u"'0'")

    createPerson = relationship(u'Person', primaryjoin='BlanktempinvalidParty.createPerson_id == Person.id')
    doctype = relationship(u'Rbblanktempinvalid')
    modifyPerson = relationship(u'Person', primaryjoin='BlanktempinvalidParty.modifyPerson_id == Person.id')
    person = relationship(u'Person', primaryjoin='BlanktempinvalidParty.person_id == Person.id')


class Blanktempinvalid(Info):
    __tablename__ = u'BlankTempInvalids'

    id = Column(Integer, primary_key=True)
    doctype_id = Column(ForeignKey('rbTempInvalidDocument.id'), index=True)
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    checkingSerial = Column(Integer, nullable=False)
    checkingNumber = Column(Integer, nullable=False)
    checkingAmount = Column(Integer, nullable=False)

    doctype = relationship(u'Rbtempinvaliddocument')


class Bloodhistory(Info):
    __tablename__ = u'BloodHistory'

    id = Column(Integer, primary_key=True)
    bloodDate = Column(Date, nullable=False)
    client_id = Column(Integer, nullable=False)
    bloodType_id = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False)


class Calendarexception(Info):
    __tablename__ = u'CalendarExceptions'
    __table_args__ = (
        Index(u'CHANGEDAY', u'date', u'fromDate'),
        Index(u'HOLIDAY', u'date', u'startYear')
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False)
    isHoliday = Column(Integer, nullable=False)
    startYear = Column(SmallInteger)
    finishYear = Column(SmallInteger)
    fromDate = Column(Date)
    text = Column(String(250), nullable=False)


class Client(Info):
    __tablename__ = u'Client'
    __table_args__ = (
        Index(u'lastName', u'lastName', u'firstName', u'patrName', u'birthDate', u'id'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    lastName = Column(Unicode(30), nullable=False)
    firstName = Column(Unicode(30), nullable=False)
    patrName = Column(Unicode(30), nullable=False)
    birthDate_raw = Column("birthDate", Date, nullable=False, index=True)
    sexCode = Column("sex", Integer, nullable=False)
    SNILS_short = Column("SNILS", String(11), nullable=False, index=True)
    bloodType_id = Column(ForeignKey('rbBloodType.id'), index=True)
    bloodDate = Column(Date)
    bloodNotes = Column(String, nullable=False)
    growth = Column(String(16), nullable=False)
    weight = Column(String(16), nullable=False)
    notes = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    birthPlace = Column(Unicode(128), nullable=False, server_default=u"''")
    embryonalPeriodWeek = Column(String(16), nullable=False, server_default=u"''")
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")

    bloodType = relationship(u'Rbbloodtype')
    client_attachments = relationship(u'Clientattach', primaryjoin='and_(Clientattach.client_id==Client.id, Clientattach.deleted==0)',
                                      order_by="desc(Clientattach.id)")
    socStatuses = relationship(u'Clientsocstatus',
                               primaryjoin="and_(Clientsocstatus.deleted == 0,Clientsocstatus.client_id==Client.id,"
                               "or_(Clientsocstatus.endDate == None, Clientsocstatus.endDate>='{0}'))".format(datetime.date.today()))
    documentsAll = relationship(u'Clientdocument', primaryjoin='and_(Clientdocument.clientId==Client.id,'
                                                               'Clientdocument.deleted == 0)',
                                order_by="desc(Clientdocument.documentId)")
    intolerances = relationship(u'Clientintolerancemedicament',
                                primaryjoin='and_(Clientintolerancemedicament.client_id==Client.id,'
                                            'Clientintolerancemedicament.deleted == 0)')
    allergies = relationship(u'Clientallergy', primaryjoin='and_(Clientallergy.client_id==Client.id,'
                                                           'Clientallergy.deleted == 0)')
    contacts = relationship(u'Clientcontact', primaryjoin='and_(Clientcontact.client_id==Client.id,'
                                                          'Clientcontact.deleted == 0)')
    direct_relations = relationship(u'DirectClientRelation', foreign_keys='Clientrelation.client_id')
    reversed_relations = relationship(u'ReversedClientRelation', foreign_keys='Clientrelation.relative_id')
    policies = relationship(u'Clientpolicy', primaryjoin='and_(Clientpolicy.clientId==Client.id,'
                                                         'Clientpolicy.deleted == 0)', order_by="desc(Clientpolicy.id)")
    works = relationship(u'Clientwork', primaryjoin='and_(Clientwork.client_id==Client.id, Clientwork.deleted == 0)',
                         order_by="desc(Clientwork.id)")
    reg_addresses = relationship(u'Clientaddress',
                                 primaryjoin="and_(Client.id==Clientaddress.client_id, Clientaddress.type==0)",
                                 order_by="desc(Clientaddress.id)")
    loc_addresses = relationship(u'Clientaddress',
                                 primaryjoin="and_(Client.id==Clientaddress.client_id, Clientaddress.type==1)",
                                 order_by="desc(Clientaddress.id)")
    appointments = relationship(
        u'ScheduleClientTicket',
        lazy='dynamic',  #order_by='desc(ScheduleTicket.begDateTime)',
        primaryjoin='and_('
                    'ScheduleClientTicket.deleted == 0, '
                    'ScheduleClientTicket.client_id == Client.id)',
        innerjoin=True
    )

    @property
    def birthDate(self):
        return DateInfo(self.birthDate_raw)

    @property
    def nameText(self):
        return u' '.join((u'%s %s %s' % (self.lastName, self.firstName, self.patrName)).split())

    @property
    def sex(self):
        """
        Делаем из пола строку
        sexCode - код пола (1 мужской, 2 женский)
        """
        if self.sexCode == 1:
            return u'М'
        elif self.sexCode == 2:
            return u'Ж'
        else:
            return u''

    @property
    def SNILS(self):
        if self.SNILS_short:
            s = self.SNILS_short+' '*14
            return s[0:3]+'-'+s[3:6]+'-'+s[6:9]+' '+s[9:11]
        else:
            return u''

    @property
    def permanentAttach(self):
        for attach in self.client_attachments:
            if attach.attachType.temporary == 0:
                return attach

    @property
    def temporaryAttach(self):
        for attach in self.client_attachments:
            if attach.attachType.temporary != 0:
                return attach

    @property
    def document(self):
        for document in self.documentsAll:
            if document.documentType and document.documentType.group.code == '1':
                return document

    @property
    def relations(self):
        return self.reversed_relations + self.direct_relations

    @property
    def phones(self):
        contacts = [(contact.name, contact.contact, contact.notes) for contact in self.contacts
                    if contact.contactType.code not in ('04', '05')]
        return ', '.join([(phone[0]+': '+phone[1]+' ('+phone[2]+')') if phone[2] else (phone[0]+': '+phone[1])
                          for phone in contacts])

    @property
    def compulsoryPolicy(self):
        for policy in self.policies:
            if not policy.policyType or u"ОМС" in policy.policyType.name:
                return policy

    @property
    def voluntaryPolicy(self):
        for policy in self.policies:
            if policy.policyType and policy.policyType.name.startswith(u"ДМС"):
                return policy

    @property
    def policy(self):
        return self.compulsoryPolicy if self.compulsoryPolicy else Clientpolicy()

    @property
    def policyDMS(self):
        return self.voluntaryPolicy if self.voluntaryPolicy else Clientpolicy()

    @property
    def fullName(self):
        return formatNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def shortName(self):
        return formatShortNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def work(self):
        return self.works[0]

    @property
    def ageTuple(self):
        date = self.date
        if not date:
            date = datetime.date.today()
        d = calcAgeInDays(self.birthDate, date)
        if d >= 0:
            return (d,
                    d/7,
                    calcAgeInMonths(self.birthDate, date),
                    calcAgeInYears(self.birthDate, date))
        else:
            return None
        return ""

    @property
    def age(self):
        date = self.date
        bd = self.birthDate_raw
        if not date:
            date = datetime.date.today()
        if not self.ageTuple:
            return u'ещё не родился'
        (days, weeks, months, years) = self.ageTuple
        if years > 7:
            return formatYears(years)
        elif years > 1:
            return formatYearsMonths(years, months-12*years)
        elif months > 1:
            add_year, new_month = divmod(bd.month + months, 12)
            if new_month:
                new_day = min(bd.day, calendar.monthrange(bd.year+add_year, new_month)[1])
                fmonth_date = datetime.date(bd.year+add_year, new_month, new_day)
            else:
                fmonth_date = bd
            return formatMonthsWeeks(months, (date-fmonth_date).days/7)
        else:
            return formatDays(days)

    @property
    def regAddress(self):
        return self.reg_addresses[0] if self.reg_addresses else None

    @property
    def locAddress(self):
        return self.loc_addresses[0] if self.loc_addresses else None

    def __unicode__(self):
        return self.formatShortNameInt(self.lastName, self.firstName, self.patrName)


class Patientstohs(Info):
    __tablename__ = u'PatientsToHS'

    client_id = Column(ForeignKey('Client.id'), primary_key=True)
    sendTime = Column(DateTime, nullable=False, server_default=u'CURRENT_TIMESTAMP')
    errCount = Column(Integer, nullable=False, server_default=u"'0'")
    info = Column(String(1024))


class Clientaddress(Info):
    __tablename__ = u'ClientAddress'
    __table_args__ = (
        Index(u'address_id', u'address_id', u'type'),
        Index(u'client_id', u'client_id', u'type', u'address_id')
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False)
    type = Column(Integer, nullable=False)
    address_id = Column(Integer, ForeignKey('Address.id'))
    freeInput = Column(String(200), nullable=False)
    version = Column(Integer, nullable=False)
    localityType = Column(Integer, nullable=False)

    address = relationship(u'Address')

    @property
    def KLADRCode(self):
        return self.address.house.KLADRCode if self.address else ''

    @property
    def KLADRStreetCode(self):
        return self.address.house.KLADRStreetCode if self.address else ''

    @property
    def city(self):
        return self.address.city if self.address else ''

    @property
    def town(self):
        return self.address.town if self.address else ''

    @property
    def text(self):
        return self.address.text if self.address else ''

    @property
    def number(self):
        return self.address.number if self.address else ''

    @property
    def corpus(self):
        return self.address.corpus if self.address else ''

    def __unicode__(self):
        if self.text:
            return self.text
        else:
            return self.freeInput


class Clientallergy(Info):
    __tablename__ = u'ClientAllergy'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    name = Column("nameSubstance", Unicode(128), nullable=False)
    power = Column(Integer, nullable=False)
    createDate = Column(Date)
    notes = Column(String, nullable=False)
    version = Column(Integer, nullable=False)

    client = relationship(u'Client')

    def __unicode__(self):
        return self.name


class Clientattach(Info):
    __tablename__ = u'ClientAttach'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    attachType_id = Column(ForeignKey('rbAttachType.id'), nullable=False, index=True)
    LPU_id = Column(ForeignKey('Organisation.id'), nullable=False, index=True)
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date)
    document_id = Column(ForeignKey('ClientDocument.id'), index=True)

    client = relationship(u'Client')
    self_document = relationship(u'Clientdocument')
    org = relationship(u'Organisation')
    orgStructure = relationship(u'Orgstructure')
    attachType = relationship(u'Rbattachtype')

    @property
    def code(self):
        return self.attachType.code

    @property
    def name(self):
        return self.attachType.name

    @property
    def outcome(self):
        return self.attachType.outcome

    @property
    def document(self):
        if self.document_id:
            return self.self_document
        else:
            return self.getClientDocument()

    def getClientDocument(self):
        documents = g.printing_session.query(Clientdocument).filter(Clientdocument.clientId == self.client_id).\
            filter(Clientdocument.deleted == 0).all()
        documents = [document for document in documents if document.documentType and document.documentType.group.code == "1"]
        return documents[-1]

    def __unicode__(self):
        try:
            result = self.name
            if self.outcome:
                result += ' ' + unicode(self.endDate)
            elif self.attachType.temporary:
                result += ' ' + self.org.shortName
                if self.begDate:
                    result += u' c ' + unicode(self.begDate)
                if self.endDate:
                    result += u' по ' + unicode(self.endDate)
            else:
                result += ' ' + self.org.shortName
        except AttributeError:
            result = ''
        return result


class Clientcontact(Info):
    __tablename__ = u'ClientContact'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    contactType_id = Column(Integer, ForeignKey('rbContactType.id'), nullable=False, index=True)
    contact = Column(String(32), nullable=False)
    notes = Column(Unicode(64), nullable=False)
    version = Column(Integer, nullable=False)

    client = relationship(u'Client')
    contactType = relationship(u'Rbcontacttype')

    @property
    def name(self):
        return self.contactType.name

    def __unicode__(self):
        return (self.name+': '+self.contact+' ('+self.notes+')') if self.notes else (self.name+': '+self.contact)


class Clientdocument(Info):
    __tablename__ = u'ClientDocument'
    __table_args__ = (
        Index(u'Ser_Numb', u'serial', u'number'),
    )

    documentId = Column("id", Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    clientId = Column("client_id", ForeignKey('Client.id'), nullable=False, index=True)
    documentType_id = Column(Integer, ForeignKey('rbDocumentType.id'), nullable=False, index=True)
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)
    origin = Column(String(256), nullable=False)
    version = Column(Integer, nullable=False)
    endDate = Column(Date)

    client = relationship(u'Client')
    documentType = relationship(u'Rbdocumenttype')

    @property
    def documentTypeCode(self):
        return self.documentType.regionalCode

    def __unicode__(self):
        return (' '.join([self.documentType.name if self.documentType else '', self.serial if self.serial else '',
                          self.number if self.number else ''])).strip()


class Clientfdproperty(Info):
    __tablename__ = u'ClientFDProperty'

    id = Column(Integer, primary_key=True)
    flatDirectory_id = Column(ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    version = Column(Integer, nullable=False)

    flatDirectory = relationship(u'Flatdirectory')


class Clientflatdirectory(Info):
    __tablename__ = u'ClientFlatDirectory'

    id = Column(Integer, primary_key=True)
    clientFDProperty_id = Column(ForeignKey('ClientFDProperty.id'), nullable=False, index=True)
    fdRecord_id = Column(ForeignKey('FDRecord.id'), nullable=False, index=True)
    dateStart = Column(DateTime)
    dateEnd = Column(DateTime)
    createDateTime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, nullable=False)
    modifyDateTime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer)
    deleted = Column(Integer, nullable=False)
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    comment = Column(String)
    version = Column(Integer, nullable=False)

    clientFDProperty = relationship(u'Clientfdproperty')
    client = relationship(u'Client')
    fdRecord = relationship(u'Fdrecord')


class Clientidentification(Info):
    __tablename__ = u'ClientIdentification'
    __table_args__ = (
        Index(u'accountingSystem_id', u'accountingSystem_id', u'identifier'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    accountingSystem_id = Column(Integer, ForeignKey('rbAccountingSystem.id'), nullable=False)
    identifier = Column(String(16), nullable=False)
    checkDate = Column(Date)
    version = Column(Integer, nullable=False)

    client = relationship(u'Client')
    accountingSystems = relationship(u'Rbaccountingsystem')

    @property
    def code(self):
        return self.attachType.code

    @property
    def name(self):
        return self.attachType.name

    # byCode = {code: identifier}
    # nameDict = {code: name}


class Clientintolerancemedicament(Info):
    __tablename__ = u'ClientIntoleranceMedicament'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    name = Column("nameMedicament", String(128), nullable=False)
    power = Column(Integer, nullable=False)
    createDate = Column(Date)
    notes = Column(String, nullable=False)
    version = Column(Integer, nullable=False)

    client = relationship(u'Client')

    def __unicode__(self):
        return self.name


class Clientpolicy(Info):
    __tablename__ = u'ClientPolicy'
    __table_args__ = (
        Index(u'Serial_Num', u'serial', u'number'),
        Index(u'client_insurer', u'client_id', u'insurer_id')
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    clientId = Column("client_id", ForeignKey('Client.id'), nullable=False)
    insurer_id = Column(Integer, ForeignKey('Organisation.id'), index=True)
    policyType_id = Column(Integer, ForeignKey('rbPolicyType.id'), index=True)
    serial = Column(String(16), nullable=False)
    number = Column(String(16), nullable=False)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date)
    name = Column(Unicode(64), nullable=False, server_default=u"''")
    note = Column(String(200), nullable=False, server_default=u"''")
    version = Column(Integer, nullable=False)

    client = relationship(u'Client')
    insurer = relationship(u'Organisation')
    policyType = relationship(u'Rbpolicytype')

    def __init__(self):
        self.serial = ""
        self.number = ""
        self.name = ""
        self.note = ""
        self.insurer = Organisation()
        self.policyType = Rbpolicytype()

    def __unicode__(self):
        return (' '.join([self.policyType.name, unicode(self.insurer), self.serial, self.number])).strip()


class Clientrelation(Info):
    __tablename__ = u'ClientRelation'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    relativeType_id = Column(Integer, ForeignKey('rbRelationType.id'), index=True)
    relative_id = Column(Integer, ForeignKey('Client.id'), nullable=False, index=True)
    version = Column(Integer, nullable=False)

    relativeType = relationship(u'Rbrelationtype')

    @property
    def leftName(self):
        return self.relativeType.leftName

    @property
    def rightName(self):
        return self.relativeType.rightName

    @property
    def code(self):
        return self.relativeType.code

    @property
    def name(self):
        return self.role + ' -> ' + self.otherRole


class DirectClientRelation(Clientrelation):

    other = relationship(u'Client', foreign_keys='Clientrelation.relative_id')

    @property
    def role(self):
        return self.leftName

    @property
    def otherRole(self):
        return self.rightName

    @property
    def regionalCode(self):
        return self.relativeType.regionalCode

    @property
    def clientId(self):
        return self.relative_id

    @property
    def isDirectGenetic(self):
        return self.relativeType.isDirectGenetic

    @property
    def isBackwardGenetic(self):
        return self.relativeType.isBackwardGenetic

    @property
    def isDirectRepresentative(self):
        return self.relativeType.isDirectRepresentative

    @property
    def isBackwardRepresentative(self):
        return self.relativeType.isBackwardRepresentative

    @property
    def isDirectEpidemic(self):
        return self.relativeType.isDirectEpidemic

    @property
    def isBackwardEpidemic(self):
        return self.relativeType.isBackwardEpidemic

    @property
    def isDirectDonation(self):
        return self.relativeType.isDirectDonation

    @property
    def isBackwardDonation(self):
        return self.relativeType.isBackwardDonation

    def __unicode__(self):
        return self.name + ' ' + self.other


class ReversedClientRelation(Clientrelation):

    other = relationship(u'Client', foreign_keys='Clientrelation.client_id')

    @property
    def role(self):
        return self.rightName

    @property
    def otherRole(self):
        return self.leftName

    @property
    def regionalCode(self):
        return self.relativeType.regionalReverseCode

    @property
    def clientId(self):
        return self.client_id
    @property
    def isDirectGenetic(self):
        return self.relativeType.isBackwardGenetic

    @property
    def isBackwardGenetic(self):
        return self.relativeType.isDirectGenetic

    @property
    def isDirectRepresentative(self):
        return self.relativeType.isBackwardRepresentative

    @property
    def isBackwardRepresentative(self):
        return self.relativeType.isDirectRepresentative

    @property
    def isDirectEpidemic(self):
        return self.relativeType.isBackwardEpidemic

    @property
    def isBackwardEpidemic(self):
        return self.relativeType.isDirectEpidemic

    @property
    def isDirectDonation(self):
        return self.relativeType.isBackwardDonation

    @property
    def isBackwardDonation(self):
        return self.relativeType.isDirectDonation

    def __unicode__(self):
        return self.name + ' ' + self.other


class Clientsocstatus(Info):
    __tablename__ = u'ClientSocStatus'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    socStatusClass_id = Column(ForeignKey('rbSocStatusClass.id'), index=True)
    socStatusType_id = Column(ForeignKey('rbSocStatusType.id'), nullable=False, index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date)
    document_id = Column(ForeignKey('ClientDocument.id'), index=True)
    version = Column(Integer, nullable=False)
    note = Column(String(256), nullable=False, server_default=u"''")
    benefitCategory_id = Column(Integer)

    client = relationship(u'Client')
    socStatusType = relationship(u'Rbsocstatustype')
    self_document = relationship(u'Clientdocument')

    @property
    def classes(self):
        return self.socStatusType.classes

    @property
    def code(self):
        return self.socStatusType.code

    @property
    def name(self):
        return self.socStatusType.name

    @property
    def document(self):
        if self.document_id:
            return self.self_document
        else:
            return self.getClientDocument()

    def getClientDocument(self):
        documents = g.printing_session.query(Clientdocument).filter(Clientdocument.clientId == self.client_id).\
            filter(Clientdocument.deleted == 0).all()
        documents = [document for document in documents if document.documentType and
                     document.documentType.group.code == "1"]
        return documents[-1]

    def __unicode__(self):
        return self.name


class Clientwork(Info):
    __tablename__ = u'ClientWork'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    org_id = Column(ForeignKey('Organisation.id'), index=True)
    shortName = Column('freeInput', String(200), nullable=False)
    post = Column(String(200), nullable=False)
    stage = Column(Integer, nullable=False)
    OKVED = Column(String(10), nullable=False)
    version = Column(Integer, nullable=False)
    rank_id = Column(Integer, nullable=False)
    arm_id = Column(Integer, nullable=False)

    client = relationship(u'Client')
    organisation = relationship(u'Organisation')
    hurts = relationship(u'ClientworkHurt')

    def __unicode__(self):
        parts = []
        if self.shortName:
            parts.append(self.shortName)
        if self.post:
            parts.append(self.post)
        if self.OKVED:
            parts.append(u'ОКВЭД: '+self._OKVED)
        return ', '.join(parts)

    #TODO: насл от OrgInfo


class ClientworkHurt(Info):
    __tablename__ = u'ClientWork_Hurt'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('ClientWork.id'), nullable=False, index=True)
    hurtType_id = Column(ForeignKey('rbHurtType.id'), nullable=False, index=True)
    stage = Column(Integer, nullable=False)

    clientWork = relationship(u'Clientwork')
    hurtType = relationship(u'Rbhurttype')
    factors = relationship(u'ClientworkHurtFactor')

    def hurtTypeCode(self):
        return self.hurtType.code

    def hurtTypeName(self):
        return self.hurtType.name

    code = property(hurtTypeCode)
    name = property(hurtTypeName)


class ClientworkHurtFactor(Info):
    __tablename__ = u'ClientWork_Hurt_Factor'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('ClientWork_Hurt.id'), nullable=False, index=True)
    factorType_id = Column(ForeignKey('rbHurtFactorType.id'), nullable=False, index=True)

    master = relationship(u'ClientworkHurt')
    factorType = relationship(u'Rbhurtfactortype')

    @property
    def code(self):
        return self.factorType.code

    @property
    def name(self):
        return self.factorType.name


class ClientQuoting(Info):
    __tablename__ = u'Client_Quoting'
    __table_args__ = (
        Index(u'deleted_prevTalon_event_id', u'deleted', u'prevTalon_event_id'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(ForeignKey('Client.id'), index=True)
    identifier = Column(String(16))
    quotaTicket = Column(String(20))
    quotaDetails_id = Column(ForeignKey(u'VMPQuotaDetails.id'), nullable=False, index=True)
    stage = Column(Integer)
    directionDate = Column(DateTime, nullable=False)
    freeInput = Column(String(128))
    org_id = Column(Integer)
    amount = Column(Integer, nullable=False, server_default=u"'0'")
    MKB = Column(String(8), nullable=False)
    status = Column(Integer, nullable=False, server_default=u"'0'")
    request = Column(Integer, nullable=False, server_default=u"'0'")
    statment = Column(String(255))
    dateRegistration = Column(DateTime, nullable=False)
    dateEnd = Column(DateTime, nullable=False)
    orgStructure_id = Column(Integer)
    regionCode = Column(String(13), index=True)
    event_id = Column(Integer, index=True)
    prevTalon_event_id = Column(Integer)
    version = Column(Integer, nullable=False)

    master = relationship(u'Client')


class ClientQuotingdiscussion(Info):
    __tablename__ = u'Client_QuotingDiscussion'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('Client.id'), index=True)
    dateMessage = Column(DateTime, nullable=False)
    agreementType_id = Column(Integer)
    responsiblePerson_id = Column(Integer)
    cosignatory = Column(String(25))
    cosignatoryPost = Column(String(20))
    cosignatoryName = Column(String(50))
    remark = Column(String(128))

    master = relationship(u'Client')


class Contract(Info):
    __tablename__ = u'Contract'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    number = Column(String(64), nullable=False)
    date_raw = Column("date", Date, nullable=False)
    recipient_id = Column(Integer, ForeignKey('Organisation.id'), nullable=False, index=True)
    recipientAccount_id = Column(Integer, ForeignKey('Organisation_Account.id'), index=True)
    recipientKBK = Column(String(30), nullable=False)
    payer_id = Column(Integer, ForeignKey('Organisation.id'), index=True)
    payerAccount_id = Column(Integer, ForeignKey('Organisation_Account.id'), index=True)
    payerKBK = Column(String(30), nullable=False)
    begDate_raw = Column("begDate", Date, nullable=False)
    endDate_raw = Column("endDate", Date, nullable=False)
    finance_id = Column(Integer, ForeignKey('rbFinance.id'), nullable=False, index=True)
    grouping = Column(String(64), nullable=False)
    resolution = Column(String(64), nullable=False)
    format_id = Column(Integer, index=True)
    exposeUnfinishedEventVisits = Column(Integer, nullable=False, server_default=u"'0'")
    exposeUnfinishedEventActions = Column(Integer, nullable=False, server_default=u"'0'")
    visitExposition = Column(Integer, nullable=False, server_default=u"'0'")
    actionExposition = Column(Integer, nullable=False, server_default=u"'0'")
    exposeDiscipline = Column(Integer, nullable=False, server_default=u"'0'")
    priceList_id = Column(Integer)
    coefficient = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    coefficientEx = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")

    recipient = relationship(u'Organisation', foreign_keys='Contract.recipient_id')
    payer = relationship(u'Organisation', foreign_keys='Contract.payer_id')
    finance = relationship(u'Rbfinance')
    recipientAccount = relationship(u'OrganisationAccount', foreign_keys='Contract.recipientAccount_id')
    payerAccount = relationship(u'OrganisationAccount', foreign_keys='Contract.payerAccount_id')

    @property
    def date(self):
        return DateInfo(self.date_raw)

    @property
    def begDate(self):
        return DateInfo(self.begDate_raw)

    @property
    def endDate(self):
        return DateInfo(self.endDate_raw)

    def convertToText(self, num):
        converter = NumToTextConverter(num)
        return converter.convert()

    def __unicode__(self):
        return self.number + ' ' + self.date


class ContractContingent(Info):
    __tablename__ = u'Contract_Contingent'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, nullable=False, index=True)
    client_id = Column(Integer, index=True)
    attachType_id = Column(Integer, index=True)
    org_id = Column(Integer, index=True)
    socStatusType_id = Column(Integer, index=True)
    insurer_id = Column(Integer, index=True)
    policyType_id = Column(Integer, index=True)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)


class ContractContragent(Info):
    __tablename__ = u'Contract_Contragent'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, nullable=False, index=True)
    insurer_id = Column(Integer, nullable=False, index=True)
    payer_id = Column(Integer, nullable=False, index=True)
    payerAccount_id = Column(Integer, nullable=False, index=True)
    payerKBK = Column(String(30), nullable=False)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)


class ContractSpecification(Info):
    __tablename__ = u'Contract_Specification'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, nullable=False, index=True)
    eventType_id = Column(Integer, nullable=False, index=True)


class ContractTariff(Info):
    __tablename__ = u'Contract_Tariff'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, nullable=False, index=True)
    eventType_id = Column(Integer, index=True)
    tariffType = Column(Integer, nullable=False)
    service_id = Column(Integer, index=True)
    code = Column(String(64))
    name = Column(String(256))
    tariffCategory_id = Column(Integer, index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    unit_id = Column(Integer, index=True)
    amount = Column(Float, nullable=False)
    uet = Column(Float, nullable=False, server_default=u"'0'")
    price = Column(Float, nullable=False, server_default=u"'0'")
    limitationExceedMode = Column(Integer, nullable=False, server_default=u"'0'")
    limitation = Column(Float, nullable=False, server_default=u"'0'")
    priceEx = Column(Float, nullable=False, server_default=u"'0'")
    MKB = Column(String(8), nullable=False)
    rbServiceFinance_id = Column(ForeignKey('rbServiceFinance.id'), index=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer)

    rbServiceFinance = relationship(u'Rbservicefinance')


class Couponstransferquote(Info):
    __tablename__ = u'CouponsTransferQuotes'

    id = Column(Integer, primary_key=True)
    srcQuotingType_id = Column(ForeignKey('rbTimeQuotingType.code'), nullable=False, index=True)
    dstQuotingType_id = Column(ForeignKey('rbTimeQuotingType.code'), nullable=False, index=True)
    transferDayType = Column(ForeignKey('rbTransferDateType.code'), nullable=False, index=True)
    transferTime = Column(Time, nullable=False)
    couponsEnabled = Column(Integer, server_default=u"'0'")

    dstQuotingType = relationship(u'Rbtimequotingtype', primaryjoin='Couponstransferquote.dstQuotingType_id == Rbtimequotingtype.code')
    srcQuotingType = relationship(u'Rbtimequotingtype', primaryjoin='Couponstransferquote.srcQuotingType_id == Rbtimequotingtype.code')
    rbTransferDateType = relationship(u'Rbtransferdatetype')


class Diagnosis(Info):
    __tablename__ = u'Diagnosis'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'", default=0)
    client_id = Column(ForeignKey('Client.id'), index=True, nullable=False)
    diagnosisType_id = Column(ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = Column(ForeignKey('rbDiseaseCharacter.id'), index=True)
    MKB_ = Column('MKB', String(8), ForeignKey('MKB.DiagID'), index=True)
    MKBEx = Column(String(8), ForeignKey('MKB.DiagID'), index=True)
    dispanser_id = Column(ForeignKey('rbDispanser.id'), index=True)
    traumaType_id = Column(ForeignKey('rbTraumaType.id'), index=True)
    setDate = Column(Date)
    endDate = Column(Date)
    mod_id = Column(ForeignKey('Diagnosis.id'), index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    # diagnosisName = Column(String(64), nullable=False)

    person = relationship('Person', foreign_keys=[person_id], lazy=False, innerjoin=True)
    client = relationship('Client')
    diagnosisType = relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = relationship('rbDiseaseCharacter', lazy=False)
    MKB = relationship('Mkb', foreign_keys=[MKB_])
    mkb = relationship('Mkb', foreign_keys=[MKB_])
    mkb_ex = relationship('Mkb', foreign_keys=[MKBEx])
    dispanser = relationship('rbDispanser', lazy=False)
    mod = relationship('Diagnosis', remote_side=[id])
    traumaType = relationship('rbTraumaType', lazy=False)

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'diagnosisType': self.diagnosisType,
            'character': self.character
        }


class Diagnostic(Info):
    __tablename__ = u'Diagnostic'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'", default=0)
    event_id = Column(ForeignKey('Event.id'), nullable=False, index=True)
    diagnosis_id = Column(ForeignKey('Diagnosis.id'), index=True)
    diagnosisType_id = Column(ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = Column(ForeignKey('rbDiseaseCharacter.id'), index=True)
    stage_id = Column(ForeignKey('rbDiseaseStage.id'), index=True)
    phase_id = Column(ForeignKey('rbDiseasePhases.id'), index=True)
    dispanser_id = Column(ForeignKey('rbDispanser.id'), index=True)
    sanatorium = Column(Integer, nullable=False)
    hospital = Column(Integer, nullable=False)
    traumaType_id = Column(ForeignKey('rbTraumaType.id'), index=True)
    speciality_id = Column(Integer, nullable=False, index=True)
    person_id = Column(ForeignKey('Person.id'), index=True)
    healthGroup_id = Column(ForeignKey('rbHealthGroup.id'), index=True)
    result_id = Column(ForeignKey('rbResult.id'), index=True)
    setDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime)
    notes = Column(Text, nullable=False, default='')
    rbAcheResult_id = Column(ForeignKey('rbAcheResult.id'), index=True)
    version = Column(Integer, nullable=False, default=0)
    action_id = Column(Integer, ForeignKey('Action.id'), index=True)
    diagnosis_description = Column(Text)

    rbAcheResult = relationship(u'Rbacheresult', innerjoin=True)
    result = relationship(u'Rbresult', innerjoin=True)
    person = relationship('Person', foreign_keys=[person_id])
    event = relationship('Event', foreign_keys='Diagnostic.event_id', innerjoin=True)
    diagnoses = relationship(
        'Diagnosis', innerjoin=True, lazy=False, uselist=True,
        primaryjoin='and_(Diagnostic.diagnosis_id == Diagnosis.id, Diagnosis.deleted == 0)'
    )
    diagnosis = relationship('Diagnosis')
    diagnosisType = relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = relationship('rbDiseaseCharacter')
    stage = relationship('rbDiseaseStage', lazy=False)
    phase = relationship('rbDiseasePhases', lazy=False)
    dispanser = relationship('rbDispanser')
    traumaType = relationship('rbTraumaType')
    healthGroup = relationship('rbHealthGroup', lazy=False)
    action = relationship('Action')

    def __int__(self):
        return self.id

    def __unicode__(self):
        return self.diagnosis.mkb + ', ' + self.diagnosisType


class Drugchart(Info):
    __tablename__ = u'DrugChart'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    master_id = Column(ForeignKey('DrugChart.id'), index=True)
    begDateTime = Column(DateTime, nullable=False)
    endDateTime = Column(DateTime)
    status = Column(Integer, nullable=False)
    statusDateTime = Column(Integer)
    note = Column(String(256), server_default=u"''")
    uuid = Column(String(100))
    version = Column(Integer)

    action = relationship(u'Action')
    master = relationship(u'Drugchart', remote_side=[id])


class Drugcomponent(Info):
    __tablename__ = u'DrugComponent'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    nomen = Column(Integer, index=True)
    name = Column(String(255))
    dose = Column(Float)
    unit = Column(Integer)
    createDateTime = Column(DateTime, nullable=False)
    cancelDateTime = Column(DateTime)

    action = relationship(u'Action')


class Emergencybrigade(Info):
    __tablename__ = u'EmergencyBrigade'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class EmergencybrigadePersonnel(Info):
    __tablename__ = u'EmergencyBrigade_Personnel'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    person_id = Column(Integer, nullable=False, index=True)


class Emergencycall(Info):
    __tablename__ = u'EmergencyCall'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    event_id = Column(Integer, nullable=False, index=True)
    numberCardCall = Column(String(64), nullable=False)
    brigade_id = Column(Integer, index=True)
    causeCall_id = Column(Integer, index=True)
    whoCallOnPhone = Column(String(64), nullable=False)
    numberPhone = Column(String(32), nullable=False)
    begDate = Column(DateTime, nullable=False, index=True)
    passDate = Column(DateTime, nullable=False, index=True)
    departureDate = Column(DateTime, nullable=False, index=True)
    arrivalDate = Column(DateTime, nullable=False, index=True)
    finishServiceDate = Column(DateTime, nullable=False, index=True)
    endDate = Column(DateTime, index=True)
    placeReceptionCall_id = Column(Integer, index=True)
    receivedCall_id = Column(Integer, index=True)
    reasondDelays_id = Column(Integer, index=True)
    resultCall_id = Column(Integer, index=True)
    accident_id = Column(Integer, index=True)
    death_id = Column(Integer, index=True)
    ebriety_id = Column(Integer, index=True)
    diseased_id = Column(Integer, index=True)
    placeCall_id = Column(Integer, index=True)
    methodTransport_id = Column(Integer, index=True)
    transfTransport_id = Column(Integer, index=True)
    renunOfHospital = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    faceRenunOfHospital = Column(String(64), nullable=False, index=True)
    disease = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    birth = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    pregnancyFailure = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    noteCall = Column(Text, nullable=False)


class Event(Info):
    __tablename__ = u'Event'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    externalId = Column(String(30), nullable=False)
    eventType_id = Column(Integer, ForeignKey('EventType.id'), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey('Organisation.id'))
    client_id = Column(Integer, ForeignKey('Client.id'), index=True)
    contract_id = Column(Integer, ForeignKey('Contract.id'), index=True)
    prevEventDate_row = Column("prevEventDate", DateTime)
    setDate_raw = Column("setDate", DateTime, nullable=False, index=True)
    setPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    execDate_raw = Column("execDate", DateTime, index=True)
    execPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    isPrimaryCode = Column("isPrimary", Integer, nullable=False)
    order = Column(Integer, nullable=False)
    result_id = Column(Integer, ForeignKey('rbResult.id'), index=True)
    nextEventDate_row = Column("nextEventDate", DateTime)
    payStatus = Column(Integer, nullable=False)
    typeAsset_id = Column(Integer, ForeignKey('rbEmergencyTypeAsset.id'), index=True)
    note = Column(Text, nullable=False)
    curator_id = Column(Integer, ForeignKey('Person.id'), index=True)
    assistant_id = Column(Integer, ForeignKey('Person.id'), index=True)
    pregnancyWeek = Column(Integer, nullable=False, server_default=u"'0'")
    MES_id = Column(Integer, index=True)
    mesSpecification_id = Column(ForeignKey('rbMesSpecification.id'), index=True)
    rbAcheResult_id = Column(ForeignKey('rbAcheResult.id'), index=True)
    version = Column(Integer, nullable=False, server_default=u"'0'")
    privilege = Column(Integer, server_default=u"'0'")
    urgent = Column(Integer, server_default=u"'0'")
    orgStructure_id = Column(Integer, ForeignKey('Person.orgStructure_id'))
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    lpu_transfer = Column(String(100))
    localContract_id = Column(Integer, ForeignKey('Event_LocalContract.id'))

    actions = relationship(u'Action', primaryjoin='and_(Action.event_id==Event.id,'
                                                     'Action.deleted == 0)')
    eventType = relationship(u'Eventtype')
    execPerson = relationship(u'Person', foreign_keys='Event.execPerson_id')
    setPerson = relationship(u'Person', foreign_keys='Event.setPerson_id')
    curator = relationship(u'Person', foreign_keys='Event.curator_id')
    assistant = relationship(u'Person', foreign_keys='Event.assistant_id')
    contract = relationship(u'Contract')
    organisation = relationship(u'Organisation')
    mesSpecification = relationship(u'Rbmesspecification')
    rbAcheResult = relationship(u'Rbacheresult')
    result = relationship(u'Rbresult')
    typeAsset = relationship(u'Rbemergencytypeasset')
    localContract = relationship(u'EventLocalcontract',
                                    backref=backref('event'))
    client = relationship(u'Client')
    visits = relationship(u'Visit')

    diagnosises = relationship(
        u'Diagnosis',
        secondary=Diagnostic.__table__,
        primaryjoin='and_(Diagnostic.event_id == Event.id, Diagnostic.deleted == 0)',
        secondaryjoin='and_(Diagnostic.diagnosis_id == Diagnosis.id, Diagnosis.deleted == 0)',
        uselist=True
    )

    @property
    def setDate(self):
        return DateTimeInfo(self.setDate_raw)

    @property
    def execDate(self):
        return DateTimeInfo(self.execDate_raw)

    @property
    def prevEventDate(self):
        return DateInfo(self.prevEventDate_raw)

    @property
    def nextEventDate(self):
        return DateInfo(self.nextEventDate_raw)

    @property
    def isPrimary(self):
        return self.isPrimaryCode == 1

    @property
    def finance(self):
        return self.eventType.finance

    @property
    def orgStructure(self):
        if self.eventType.requestType.code == 'policlinic' and self.orgStructure_id:
            return g.printing_session.query(Orgstructure).get(self.orgStructure_id)
        elif self.eventType.requestType.code in ('hospital', 'clinic', 'stationary'):
            movings = [action for action in self.actions if (action.endDate.datetime is None and
                                                             action.actionType.flatCode == 'moving')]
            return movings[-1][('orgStructStay',)].value if movings else None
        return None

    @property
    def departmentManager(self):
        persons = g.printing_session.query(Person).filter(Person.orgStructure_id == self.orgStructure.id).all() if self.orgStructure else []
        if persons:
            for person in persons:
                if person.post and person.post.flatCode == u'departmentManager':
                    return person
        return None

    @property
    def date(self):
        date = self.execDate if self.execDate is not None else datetime.date.today()
        return date

    def get_grouped_services_and_sum(self):
        services = defaultdict(lambda: dict(services=[], amount=0, sum=0))
        total_sum = 0
        for action in self.actions:
            if action.account and action.price != 0:
                services[action.actionType_id]['services'].append(action)
                services[action.actionType_id]['amount'] += action.amount
                services[action.actionType_id]['sum'] += action.price
                total_sum += action.price
        return {
            'services': services,
            'total_sum': total_sum
        }

    def __unicode__(self):
        return unicode(self.eventType)


class Hsintegration(Event):
    __tablename__ = u'HSIntegration'

    event_id = Column(ForeignKey('Event.id'), primary_key=True)
    status = Column(Enum(u'NEW', u'SENDED', u'ERROR'), nullable=False, server_default=u"'NEW'")
    info = Column(String(1024))


class Eventtype(RBInfo):
    __tablename__ = u'EventType'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    purpose_id = Column(Integer, ForeignKey('rbEventTypePurpose.id'), index=True)
    finance_id = Column(Integer, ForeignKey('rbFinance.id'), index=True)
    scene_id = Column(Integer, index=True)
    visitServiceModifier = Column(String(128), nullable=False)
    visitServiceFilter = Column(String(32), nullable=False)
    visitFinance = Column(Integer, nullable=False, server_default=u"'0'")
    actionFinance = Column(Integer, nullable=False, server_default=u"'0'")
    period = Column(Integer, nullable=False)
    singleInPeriod = Column(Integer, nullable=False)
    isLong = Column(Integer, nullable=False, server_default=u"'0'")
    dateInput = Column(Integer, nullable=False, server_default=u"'0'")
    service_id = Column(Integer, ForeignKey('rbService.id'), index=True)
    printContext = Column("context", String(64), nullable=False)
    form = Column(String(64), nullable=False)
    minDuration = Column(Integer, nullable=False, server_default=u"'0'")
    maxDuration = Column(Integer, nullable=False, server_default=u"'0'")
    showStatusActionsInPlanner = Column(Integer, nullable=False, server_default=u"'1'")
    showDiagnosticActionsInPlanner = Column(Integer, nullable=False, server_default=u"'1'")
    showCureActionsInPlanner = Column(Integer, nullable=False, server_default=u"'1'")
    showMiscActionsInPlanner = Column(Integer, nullable=False, server_default=u"'1'")
    limitStatusActionsInput = Column(Integer, nullable=False, server_default=u"'0'")
    limitDiagnosticActionsInput = Column(Integer, nullable=False, server_default=u"'0'")
    limitCureActionsInput = Column(Integer, nullable=False, server_default=u"'0'")
    limitMiscActionsInput = Column(Integer, nullable=False, server_default=u"'0'")
    showTime = Column(Integer, nullable=False, server_default=u"'0'")
    medicalAidType_id = Column(Integer, index=True)
    eventProfile_id = Column(Integer, index=True)
    mesRequired = Column(Integer, nullable=False, server_default=u"'0'")
    mesCodeMask = Column(String(64), server_default=u"''")
    mesNameMask = Column(String(64), server_default=u"''")
    counter_id = Column(ForeignKey('rbCounter.id'), index=True)
    isExternal = Column(Integer, nullable=False, server_default=u"'0'")
    isAssistant = Column(Integer, nullable=False, server_default=u"'0'")
    isCurator = Column(Integer, nullable=False, server_default=u"'0'")
    canHavePayableActions = Column(Integer, nullable=False, server_default=u"'0'")
    isRequiredCoordination = Column(Integer, nullable=False, server_default=u"'0'")
    isOrgStructurePriority = Column(Integer, nullable=False, server_default=u"'0'")
    isTakenTissue = Column(Integer, nullable=False, server_default=u"'0'")
    sex = Column(Integer, nullable=False, server_default=u"'0'")
    age = Column(String(9), nullable=False)
    rbMedicalKind_id = Column(ForeignKey('rbMedicalKind.id'), index=True)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    requestType_id = Column(Integer, ForeignKey('rbRequestType.id'))

    counter = relationship(u'Rbcounter')
    rbMedicalKind = relationship(u'Rbmedicalkind')
    purpose = relationship(u'Rbeventtypepurpose')
    finance = relationship(u'Rbfinance')
    service = relationship(u'Rbservice')
    requestType = relationship(u'Rbrequesttype')

    def __unicode__(self):
        return self.name


class Eventtypeform(Info):
    __tablename__ = u'EventTypeForm'

    id = Column(Integer, primary_key=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    eventType_id = Column(Integer, nullable=False, index=True)
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)
    descr = Column(String(64), nullable=False)
    pass_ = Column(u'pass', Integer, nullable=False)


class EventtypeAction(Info):
    __tablename__ = u'EventType_Action'

    id = Column(Integer, primary_key=True)
    eventType_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    actionType_id = Column(Integer, nullable=False, index=True)
    speciality_id = Column(Integer, index=True)
    tissueType_id = Column(ForeignKey('rbTissueType.id'), index=True)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    selectionGroup = Column(Integer, nullable=False, server_default=u"'0'")
    actuality = Column(Integer, nullable=False)
    expose = Column(Integer, nullable=False, server_default=u"'1'")
    payable = Column(Integer, nullable=False, server_default=u"'0'")
    academicDegree_id = Column(Integer, index=True)

    tissueType = relationship(u'Rbtissuetype')


class EventtypeDiagnostic(Info):
    __tablename__ = u'EventType_Diagnostic'

    id = Column(Integer, primary_key=True)
    eventType_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    speciality_id = Column(Integer, index=True)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    defaultHealthGroup_id = Column(Integer, index=True)
    defaultMKB = Column(String(5), nullable=False)
    defaultDispanser_id = Column(Integer, index=True)
    selectionGroup = Column(Integer, nullable=False, server_default=u"'0'")
    actuality = Column(Integer, nullable=False)
    visitType_id = Column(Integer)


class EventFeed(Info):
    __tablename__ = u'Event_Feed'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    event_id = Column(Integer, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    mealTime_id = Column(Integer, index=True)
    diet_id = Column(Integer, index=True)


class EventLocalcontract(Info):
    __tablename__ = u'Event_LocalContract'
    __table_args__ = (
        Index(u'lastName', u'lastName', u'firstName', u'patrName', u'birthDate', u'id'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    master_id = Column(Integer, nullable=False, index=True)
    coordDate = Column(DateTime)
    coordAgent = Column(String(128), nullable=False, server_default=u"''")
    coordInspector = Column(String(128), nullable=False, server_default=u"''")
    coordText = Column(String, nullable=False)
    dateContract = Column(Date, nullable=False)
    numberContract = Column(Unicode(64), nullable=False)
    sumLimit = Column(Float(asdecimal=True), nullable=False)
    lastName = Column(Unicode(30), nullable=False)
    firstName = Column(Unicode(30), nullable=False)
    patrName = Column(Unicode(30), nullable=False)
    birthDate = Column(Date, nullable=False, index=True)
    documentType_id = Column(Integer, ForeignKey('rbDocumentType.id'), index=True)
    serialLeft = Column(Unicode(8), nullable=False)
    serialRight = Column(Unicode(8), nullable=False)
    number = Column(String(16), nullable=False)
    regAddress = Column(Unicode(64), nullable=False)
    org_id = Column(Integer, ForeignKey('Organisation.id'), index=True)

    org = relationship(u'Organisation')
    documentType = relationship(u'Rbdocumenttype')

    def __unicode__(self):
        parts = []
        if self.coordDate:
            parts.append(u'согласовано ' + self.coordDate)
        if self.coordText:
            parts.append(self.coordText)
        if self.number:
            parts.append(u'№ ' + self.number)
        if self.date:
            parts.append(u'от ' + self.date)
        if self.org:
            parts.append(unicode(self.org))
        else:
            parts.append(self.lastName)
            parts.append(self.firstName)
            parts.append(self.patrName)
        return ' '.join(parts)

    @property
    def document(self):
        document = Clientdocument()
        document.documentType = self.documentType
        if self.serialLeft and self.serialRight:
            document.serial = self.serialLeft + u' ' + self.serialRight
        else:
            document.serial = self.serialLeft or self.serialRight or ''
        document.number = self.number
        return document

    @property
    def address(self):
        return self.regAddress


class EventPayment(Info):
    __tablename__ = u'Event_Payment'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    master_id = Column(Integer, ForeignKey('Event.id'), nullable=False, index=True)
    date = Column(Date, nullable=False)
    cashOperation_id = Column(ForeignKey('rbCashOperation.id'), index=True)
    sum = Column(Float(), nullable=False)
    typePayment = Column(Integer, nullable=False)
    settlementAccount = Column(String(64))
    bank_id = Column(Integer, index=True)
    numberCreditCard = Column(String(64))
    cashBox = Column(String(32), nullable=False)

    createPerson = relationship('Person')
    cashOperation = relationship(u'Rbcashoperation')
    event = relationship('Event')


class EventPerson(Info):
    __tablename__ = u'Event_Persons'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False, index=True)
    person_id = Column(Integer, nullable=False, index=True)
    begDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime)


class Fdfield(Info):
    __tablename__ = u'FDField'

    id = Column(Integer, primary_key=True)
    fdFieldType_id = Column(ForeignKey('FDFieldType.id'), nullable=False, index=True)
    flatDirectory_id = Column(ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = Column(ForeignKey('FlatDirectory.code'), index=True)
    name = Column(String(4096), nullable=False)
    description = Column(String(4096))
    mask = Column(String(4096))
    mandatory = Column(Integer)
    order = Column(Integer)

    fdFieldType = relationship(u'Fdfieldtype')
    flatDirectory = relationship(u'Flatdirectory', primaryjoin='Fdfield.flatDirectory_id == Flatdirectory.id')

    values = relationship(u'Fdfieldvalue', backref=backref('fdField'), lazy='dynamic')

    def get_value(self, record_id):
        return self.values.filter(Fdfieldvalue.fdRecord_id == record_id).first().value


class Fdfieldtype(Info):
    __tablename__ = u'FDFieldType'

    id = Column(Integer, primary_key=True)
    name = Column(String(4096), nullable=False)
    description = Column(String(4096))


class Fdfieldvalue(Info):
    __tablename__ = u'FDFieldValue'

    id = Column(Integer, primary_key=True)
    fdRecord_id = Column(ForeignKey('FDRecord.id'), nullable=False, index=True)
    fdField_id = Column(ForeignKey('FDField.id'), nullable=False, index=True)
    value = Column(String)

    # fdRecord = relationship(u'Fdrecord')


class Fdrecord(Info):
    __tablename__ = u'FDRecord'

    id = Column(Integer, primary_key=True)
    flatDirectory_id = Column(ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = Column(ForeignKey('FlatDirectory.code'), index=True)
    order = Column(Integer)
    name = Column(String(4096))
    description = Column(String(4096))
    dateStart = Column(DateTime)
    dateEnd = Column(DateTime)

    FlatDirectory = relationship(u'Flatdirectory', primaryjoin='Fdrecord.flatDirectory_code == Flatdirectory.code')
    flatDirectory = relationship(u'Flatdirectory', primaryjoin='Fdrecord.flatDirectory_id == Flatdirectory.id')
    values = relationship(u'Fdfieldvalue', backref=backref('Fdrecord'), lazy='dynamic')

    def get_value(self):
        return [value.value for value in self.values]
        #return [field.get_value(self.id) for field in self.FlatDirectory.fields] # в нтк столбцы не упорядочены


class Flatdirectory(Info):
    __tablename__ = u'FlatDirectory'

    id = Column(Integer, primary_key=True)
    name = Column(String(4096), nullable=False)
    code = Column(String(128), index=True)
    description = Column(String(4096))

    fields = relationship(u'Fdfield', foreign_keys='Fdfield.flatDirectory_code', backref=backref('FlatDirectory'),
                             lazy='dynamic')


class Informermessage(Info):
    __tablename__ = u'InformerMessage'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    subject = Column(String(128), nullable=False)
    text = Column(String, nullable=False)


class InformermessageReadmark(Info):
    __tablename__ = u'InformerMessage_readMark'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    person_id = Column(Integer, index=True)


class Job(Info):
    __tablename__ = u'Job'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    jobType_id = Column(Integer, ForeignKey('rbJobType.id'), nullable=False, index=True)
    orgStructure_id = Column(Integer, ForeignKey('OrgStructure.id'), nullable=False, index=True)
    date = Column(Date, nullable=False)
    begTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    quantity = Column(Integer, nullable=False)

    job_type = relationship(u'Rbjobtype', lazy='joined')
    org_structure = relationship(u'Orgstructure', lazy='joined')


class JobTicket(Info):
    __tablename__ = u'Job_Ticket'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey('Job.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    datetime = Column(DateTime, nullable=False)
    resTimestamp = Column(DateTime)
    resConnectionId = Column(Integer)
    status = Column(Integer, nullable=False, server_default=u"'0'")
    begDateTime = Column(DateTime)
    endDateTime = Column(DateTime)
    label = Column(String(64), nullable=False, server_default=u"''")
    note = Column(String(128), nullable=False, server_default=u"''")

    job = relationship(u'Job', lazy='joined')

    @property
    def jobType(self):
        self.job.job_type

    @property
    def orgStructure(self):
        self.job.org_structure

    def __unicode__(self):
        return u'%s, %s, %s' % (unicode(self.jobType),
                                unicode(self.datetime),
                                unicode(self.orgStructure))


class Lastchange(Info):
    __tablename__ = u'LastChanges'

    id = Column(Integer, primary_key=True)
    table = Column(String(32), nullable=False)
    table_key_id = Column(Integer, nullable=False)
    flags = Column(Text, nullable=False)


class Layoutattribute(Info):
    __tablename__ = u'LayoutAttribute'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1023), nullable=False)
    code = Column(String(255), nullable=False)
    typeName = Column(String(255))
    measure = Column(String(255))
    defaultValue = Column(String(1023))


class Layoutattributevalue(Info):
    __tablename__ = u'LayoutAttributeValue'

    id = Column(Integer, primary_key=True)
    actionPropertyType_id = Column(Integer, nullable=False)
    layoutAttribute_id = Column(ForeignKey('LayoutAttribute.id'), nullable=False, index=True)
    value = Column(String(1023), nullable=False)

    layoutAttribute = relationship(u'Layoutattribute')


class Licence(Info):
    __tablename__ = u'Licence'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)
    person_id = Column(Integer, index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)


class LicenceService(Info):
    __tablename__ = u'Licence_Service'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    service_id = Column(Integer, nullable=False, index=True)


class Mkb(Info):
    __tablename__ = u'MKB'
    __table_args__ = (
        Index(u'BlockID', u'BlockID', u'DiagID'),
        Index(u'ClassID_2', u'ClassID', u'BlockID', u'BlockName'),
        Index(u'ClassID', u'ClassID', u'ClassName')
    )

    id = Column(Integer, primary_key=True)
    ClassID = Column(String(8), nullable=False)
    ClassName = Column(String(150), nullable=False)
    BlockID = Column(String(9), nullable=False)
    BlockName = Column(String(160), nullable=False)
    DiagID = Column(String(8), nullable=False, index=True)
    DiagName = Column(String(160), nullable=False, index=True)
    Prim = Column(String(1), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(String(12), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    characters = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    service_id = Column(Integer, index=True)
    MKBSubclass_id = Column(Integer)

    def __unicode__(self):
        return self.DiagID  # + ' ' + self.DiagName

    @property
    def descr(self):
        mainCode = self.DiagID[:5]
        subclass = self.DiagID[5:]
        record = g.printing_session.query(Mkb).filter(Mkb.DiagID == mainCode).first()
        result = self.DiagID
        if record:
            result = record.DiagName
            if subclass:
                subclassId = record.MKBSubclass_id
                recordSubclass = (RbmkbsubclassItem.
                                  query.
                                  filter(RbmkbsubclassItem.master_id == subclassId,
                                         RbmkbsubclassItem.code == subclass).
                                  first())
                if recordSubclass:
                    result = u'{0} {1}'.format(result, recordSubclass.name)
                else:
                    result = u'{0} {1}'.format(result, subclass)
        return result



class MkbQuotatypePacientmodel(Info):
    __tablename__ = u'MKB_QuotaType_PacientModel'

    id = Column(Integer, primary_key=True)
    MKB_id = Column(Integer, nullable=False)
    pacientModel_id = Column(Integer, nullable=False)
    quotaType_id = Column(Integer, nullable=False)


class Media(Info):
    __tablename__ = u'Media'

    id = Column(Integer, primary_key=True)
    filename = Column(String(256, u'utf8_bin'), nullable=False)
    file = Column(MEDIUMBLOB)


class Medicalkindunit(Info):
    __tablename__ = u'MedicalKindUnit'

    id = Column(Integer, primary_key=True)
    rbMedicalKind_id = Column(ForeignKey('rbMedicalKind.id'), nullable=False, index=True)
    eventType_id = Column(ForeignKey('EventType.id'), index=True)
    rbMedicalAidUnit_id = Column(ForeignKey('rbMedicalAidUnit.id'), nullable=False, index=True)
    rbPayType_id = Column(ForeignKey('rbPayType.id'), nullable=False, index=True)
    rbTariffType_id = Column(ForeignKey('rbTariffType.id'), nullable=False, index=True)

    eventType = relationship(u'Eventtype')
    rbMedicalAidUnit = relationship(u'Rbmedicalaidunit')
    rbMedicalKind = relationship(u'Rbmedicalkind')
    rbPayType = relationship(u'Rbpaytype')
    rbTariffType = relationship(u'Rbtarifftype')


class Meta(Info):
    __tablename__ = u'Meta'

    name = Column(String(100), primary_key=True)
    value = Column(Text)


class Modeldescription(Info):
    __tablename__ = u'ModelDescription'

    id = Column(Integer, primary_key=True)
    idx = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    name = Column(String(64), nullable=False)
    fieldIdx = Column(Integer, nullable=False, server_default=u"'-1'")
    tableName = Column(String(64), nullable=False)


class Notificationoccurred(Info):
    __tablename__ = u'NotificationOccurred'

    id = Column(Integer, primary_key=True)
    eventDatetime = Column(DateTime, nullable=False)
    clientId = Column(Integer, nullable=False)
    userId = Column(ForeignKey('Person.id'), nullable=False, index=True)

    Person = relationship(u'Person')


class Orgstructure(Info):
    __tablename__ = u'OrgStructure'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    organisation_id = Column(Integer, ForeignKey('Organisation.id'), nullable=False, index=True)
    code = Column(Unicode(255), nullable=False)
    name = Column(Unicode(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('OrgStructure.id'), index=True)
    type = Column(Integer, nullable=False, server_default=u"'0'")
    net_id = Column(Integer, ForeignKey('rbNet.id'), index=True)
    isArea = Column(Integer, nullable=False, server_default=u"'0'")
    hasHospitalBeds = Column(Integer, nullable=False, server_default=u"'0'")
    hasStocks = Column(Integer, nullable=False, server_default=u"'0'")
    infisCode = Column(String(16), nullable=False)
    infisInternalCode = Column(String(16), nullable=False)
    infisDepTypeCode = Column(String(16), nullable=False)
    infisTariffCode = Column(String(16), nullable=False)
    availableForExternal = Column(Integer, nullable=False, server_default=u"'1'")
    Address = Column(String(255), nullable=False)
    inheritEventTypes = Column(Integer, nullable=False, server_default=u"'0'")
    inheritActionTypes = Column(Integer, nullable=False, server_default=u"'0'")
    inheritGaps = Column(Integer, nullable=False, server_default=u"'0'")
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")
    show = Column(Integer, nullable=False, server_default=u"'1'")

    parent = relationship(u'Orgstructure', lazy="immediate", remote_side=[id])
    organisation = relationship(u'Organisation')
    Net = relationship(u'Rbnet')

    def getNet(self):
        if self.Net is None:
            if self.parent:
                self.Net = self.parent.getNet()
            elif self.organisation:
                self.Net = self.organisation.net
        return self.Net

    def get_org_structure_full_name(self):
        names = [self.code]
        ids = set([self.id])
        parent_id = self.parent_id
        parent = self.parent

        while parent_id:
            if parent_id in ids:
                parent_id = None
            else:
                ids.add(parent_id)
                names.append(parent.code)
                parent_id = parent.parent_id
                parent = parent.parent
        return '/'.join(reversed(names))

    def getFullName(self):
        return self.get_org_structure_full_name()

    def getAddress(self):
        if not self.Address:
            if self.parent:
                self.Address = self.parent.getAddress()
            elif self.organisation:
                self.Address = self.organisation.address
            else:
                self.Address = ''
        return self.Address

    def __unicode__(self):
        return self.getFullName()

    net = property(getNet)
    fullName = property(getFullName)
    address = property(getAddress)


class OrgstructureActiontype(Info):
    __tablename__ = u'OrgStructure_ActionType'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    actionType_id = Column(Integer, index=True)


class OrgstructureAddres(Info):
    __tablename__ = u'OrgStructure_Address'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    house_id = Column(Integer, nullable=False, index=True)
    firstFlat = Column(Integer, nullable=False, server_default=u"'0'")
    lastFlat = Column(Integer, nullable=False, server_default=u"'0'")


class OrgstructureDisabledattendance(Info):
    __tablename__ = u'OrgStructure_DisabledAttendance'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    attachType_id = Column(ForeignKey('rbAttachType.id'), index=True)
    disabledType = Column(Integer, nullable=False, server_default=u"'0'")

    attachType = relationship(u'Rbattachtype')
    master = relationship(u'Orgstructure')


class OrgstructureEventtype(Info):
    __tablename__ = u'OrgStructure_EventType'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    eventType_id = Column(Integer, index=True)


class OrgstructureGap(Info):
    __tablename__ = u'OrgStructure_Gap'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    begTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    speciality_id = Column(Integer, index=True)
    person_id = Column(Integer, index=True)


class OrgstructureHospitalbed(Info):
    __tablename__ = u'OrgStructure_HospitalBed'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(16), nullable=False, server_default=u"''")
    name = Column(String(64), nullable=False, server_default=u"''")
    isPermanentCode = Column("isPermanent", Integer, nullable=False, server_default=u"'0'")
    type_id = Column(Integer, ForeignKey('rbHospitalBedType.id'), index=True)
    profile_id = Column(Integer, ForeignKey('rbHospitalBedProfile.id'), index=True)
    relief = Column(Integer, nullable=False, server_default=u"'0'")
    schedule_id = Column(Integer, ForeignKey('rbHospitalBedShedule.id'), index=True)
    begDate = Column(Date)
    endDate = Column(Date)
    sex = Column(Integer, nullable=False, server_default=u"'0'")
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    involution = Column(Integer, nullable=False, server_default=u"'0'")
    begDateInvolute = Column(Date)
    endDateInvolute = Column(Date)

    orgStructure = relationship(u'Orgstructure')
    type = relationship(u'Rbhospitalbedtype')
    profile = relationship(u'Rbhospitalbedprofile')
    schedule = relationship(u'Rbhospitalbedshedule')

    @property
    def isPermanent(self):
        return self.isPermanentCode == 1


class OrgstructureJob(Info):
    __tablename__ = u'OrgStructure_Job'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    jobType_id = Column(Integer, index=True)
    begTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)
    quantity = Column(Integer, nullable=False)


class OrgstructureStock(Info):
    __tablename__ = u'OrgStructure_Stock'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    nomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    finance_id = Column(ForeignKey('rbFinance.id'), index=True)
    constrainedQnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    orderQnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")

    finance = relationship(u'Rbfinance')
    master = relationship(u'Orgstructure')
    nomenclature = relationship(u'Rbnomenclature')


class Organisation(Info):
    __tablename__ = u'Organisation'
    __table_args__ = (
        Index(u'shortName', u'shortName', u'INN', u'OGRN'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    fullName = Column(Unicode(255), nullable=False)
    shortName = Column(Unicode(255), nullable=False)
    title = Column(Unicode(255), nullable=False, index=True)
    net_id = Column(Integer, ForeignKey('rbNet.id'), index=True)
    infisCode = Column(String(12), nullable=False, index=True)
    obsoleteInfisCode = Column(String(60), nullable=False)
    OKVED = Column(String(64), nullable=False, index=True)
    INN = Column(String(15), nullable=False, index=True)
    KPP = Column(String(15), nullable=False)
    OGRN = Column(String(15), nullable=False, index=True)
    OKATO = Column(String(15), nullable=False)
    OKPF_code = Column(String(4), nullable=False)
    OKPF_id = Column(Integer, ForeignKey('rbOKPF.id'), index=True)
    OKFS_code = Column(Integer, nullable=False)
    OKFS_id = Column(Integer, ForeignKey('rbOKFS.id'), index=True)
    OKPO = Column(String(15), nullable=False)
    FSS = Column(String(10), nullable=False)
    region = Column(Unicode(40), nullable=False)
    Address = Column(Unicode(255), nullable=False)
    chief = Column(String(64), nullable=False)
    phone = Column(String(255), nullable=False)
    accountant = Column(String(64), nullable=False)
    isInsurer = Column(Integer, nullable=False, index=True)
    compulsoryServiceStop = Column(Integer, nullable=False, server_default=u"'0'")
    voluntaryServiceStop = Column(Integer, nullable=False, server_default=u"'0'")
    area = Column(String(13), nullable=False)
    isHospital = Column(Integer, nullable=False, server_default=u"'0'")
    notes = Column(String, nullable=False)
    head_id = Column(Integer, index=True)
    miacCode = Column(String(10), nullable=False)
    isOrganisation = Column(Integer, nullable=False, server_default=u"'0'")
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")


    net = relationship(u'Rbnet')
    OKPF = relationship(u'Rbokpf')
    OKFS = relationship(u'Rbokfs')
    org_accounts = relationship(u'OrganisationAccount')

    def __init__(self):
        self.title = ""
        self.fullName = ""
        self.shortName = ""

    @property
    def bank(self):
        return [account.bank for account in self.org_accounts]

    def __unicode__(self):
        return self.shortName


class OrganisationAccount(Info):
    __tablename__ = u'Organisation_Account'

    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('Organisation.id'), nullable=False, index=True)
    bankName = Column(Unicode(128), nullable=False)
    name = Column(String(20), nullable=False)
    notes = Column(String, nullable=False)
    bank_id = Column(Integer, ForeignKey('Bank.id'), nullable=False, index=True)
    cash = Column(Integer, nullable=False)

    org = relationship(u'Organisation')
    bank = relationship(u'Bank')


class OrganisationPolicyserial(Info):
    __tablename__ = u'Organisation_PolicySerial'

    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, nullable=False, index=True)
    serial = Column(String(16), nullable=False)
    policyType_id = Column(Integer, index=True)


class Person(Info):
    __tablename__ = u'Person'
    __table_args__ = (
        Index(u'lastName', u'lastName', u'firstName', u'patrName'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(12), nullable=False)
    federalCode = Column(Unicode(255), nullable=False)
    regionalCode = Column(String(16), nullable=False)
    lastName = Column(Unicode(30), nullable=False)
    firstName = Column(Unicode(30), nullable=False)
    patrName = Column(Unicode(30), nullable=False)
    post_id = Column(Integer, ForeignKey('rbPost.id'), index=True)
    speciality_id = Column(Integer, ForeignKey('rbSpeciality.id'), index=True)
    org_id = Column(Integer, ForeignKey('Organisation.id'), index=True)
    orgStructure_id = Column(Integer, ForeignKey('OrgStructure.id'), index=True)
    office = Column(Unicode(8), nullable=False)
    office2 = Column(Unicode(8), nullable=False)
    tariffCategory_id = Column(Integer, ForeignKey('rbTariffCategory.id'), index=True)
    finance_id = Column(Integer, ForeignKey('rbFinance.id'), index=True)
    retireDate = Column(Date, index=True)
    ambPlan = Column(SmallInteger, nullable=False)
    ambPlan2 = Column(SmallInteger, nullable=False)
    ambNorm = Column(SmallInteger, nullable=False)
    homPlan = Column(SmallInteger, nullable=False)
    homPlan2 = Column(SmallInteger, nullable=False)
    homNorm = Column(SmallInteger, nullable=False)
    expPlan = Column(SmallInteger, nullable=False)
    expNorm = Column(SmallInteger, nullable=False)
    login = Column(Unicode(32), nullable=False)
    password = Column(String(32), nullable=False)
    userProfile_id = Column(Integer, index=True)
    retired = Column(Integer, nullable=False)
    birthDate = Column(Date, nullable=False)
    birthPlace = Column(String(64), nullable=False)
    sex = Column(Integer, nullable=False)
    SNILS = Column(String(11), nullable=False)
    INN = Column(String(15), nullable=False)
    availableForExternal = Column(Integer, nullable=False, server_default=u"'1'")
    primaryQuota = Column(SmallInteger, nullable=False, server_default=u"'50'")
    ownQuota = Column(SmallInteger, nullable=False, server_default=u"'25'")
    consultancyQuota = Column(SmallInteger, nullable=False, server_default=u"'25'")
    externalQuota = Column(SmallInteger, nullable=False, server_default=u"'10'")
    lastAccessibleTimelineDate = Column(Date)
    timelineAccessibleDays = Column(Integer, nullable=False, server_default=u"'0'")
    typeTimeLinePerson = Column(Integer, nullable=False)
    maxOverQueue = Column(Integer, server_default=u"'0'")
    maxCito = Column(Integer, server_default=u"'0'")
    quotUnit = Column(Integer, server_default=u"'0'")
    academicdegree_id = Column(Integer, ForeignKey('rbAcademicDegree.id'))
    academicTitle_id = Column(Integer, ForeignKey('rbAcademicTitle.id'))

    post = relationship(u'Rbpost')
    speciality = relationship(u'Rbspeciality')
    organisation = relationship(u'Organisation')
    orgStructure = relationship(u'Orgstructure')
    academicDegree = relationship(u'Rbacademicdegree')
    academicTitle = relationship(u'Rbacademictitle')
    tariffCategory = relationship(u'Rbtariffcategory')

    @property
    def fullName(self):
        return formatNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def shortName(self):
        return formatShortNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def longName(self):
        return formatNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def name(self):
        return formatShortNameInt(self.lastName, self.firstName, self.patrName)

    def __unicode__(self):
        result = formatShortNameInt(self.lastName, self.firstName, self.patrName)
        if self.speciality:
            result += ', '+self.speciality.name
        return unicode(result)


class Personaddres(Info):
    __tablename__ = u'PersonAddress'
    __table_args__ = (
        Index(u'person_id', u'person_id', u'type', u'address_id'),
    )

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False)
    type = Column(Integer, nullable=False)
    address_id = Column(Integer)


class Persondocument(Info):
    __tablename__ = u'PersonDocument'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False, index=True)
    documentType_id = Column(Integer, index=True)
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)
    origin = Column(String(64), nullable=False)


class Personeducation(Info):
    __tablename__ = u'PersonEducation'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False, index=True)
    documentType_id = Column(Integer, index=True)
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    date = Column(Date, nullable=False)
    origin = Column(String(64), nullable=False)
    status = Column(String(64), nullable=False)
    validFromDate = Column(Date)
    validToDate = Column(Date)
    speciality_id = Column(Integer)
    educationCost = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    cost = Column(Float(asdecimal=True))


class Personorder(Info):
    __tablename__ = u'PersonOrder'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    person_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False)
    type = Column(String(64), nullable=False)
    documentDate = Column(Date, nullable=False)
    documentNumber = Column(String(16), nullable=False)
    documentType_id = Column(Integer, index=True)
    salary = Column(String(64), nullable=False)
    validFromDate = Column(Date)
    validToDate = Column(Date)
    orgStructure_id = Column(Integer, index=True)
    post_id = Column(Integer, index=True)


class Persontimetemplate(Info):
    __tablename__ = u'PersonTimeTemplate'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    ambBegTime = Column(Time)
    ambEndTime = Column(Time)
    ambPlan = Column(SmallInteger, nullable=False)
    office = Column(String(8), nullable=False)
    ambBegTime2 = Column(Time)
    ambEndTime2 = Column(Time)
    ambPlan2 = Column(SmallInteger, nullable=False)
    office2 = Column(String(8), nullable=False)
    homBegTime = Column(Time)
    homEndTime = Column(Time)
    homPlan = Column(SmallInteger, nullable=False)
    homBegTime2 = Column(Time)
    homEndTime2 = Column(Time)
    homPlan2 = Column(SmallInteger, nullable=False)


class PersonActivity(Info):
    __tablename__ = u'Person_Activity'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    activity_id = Column(Integer, index=True)


class PersonProfile(Info):
    __tablename__ = u'Person_Profiles'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, nullable=False, index=True)
    userProfile_id = Column(Integer, nullable=False, index=True)


class PersonTimetemplate(Info):
    __tablename__ = u'Person_TimeTemplate'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(ForeignKey('Person.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    ambBegTime = Column(Time)
    ambEndTime = Column(Time)
    ambPlan = Column(SmallInteger, nullable=False)
    office = Column(String(8), nullable=False)
    ambBegTime2 = Column(Time)
    ambEndTime2 = Column(Time)
    ambPlan2 = Column(SmallInteger, nullable=False)
    office2 = Column(String(8), nullable=False)
    homBegTime = Column(Time)
    homEndTime = Column(Time)
    homPlan = Column(SmallInteger, nullable=False)
    homBegTime2 = Column(Time)
    homEndTime2 = Column(Time)
    homPlan2 = Column(SmallInteger, nullable=False)

    createPerson = relationship(u'Person', primaryjoin='PersonTimetemplate.createPerson_id == Person.id')
    master = relationship(u'Person', primaryjoin='PersonTimetemplate.master_id == Person.id')
    modifyPerson = relationship(u'Person', primaryjoin='PersonTimetemplate.modifyPerson_id == Person.id')


class Pharmacy(Info):
    __tablename__ = u'Pharmacy'

    actionId = Column(Integer, primary_key=True)
    flatCode = Column(String(255))
    attempts = Column(Integer, server_default=u"'0'")
    status = Column(Enum(u'ADDED', u'COMPLETE', u'ERROR'), server_default=u"'ADDED'")
    uuid = Column(String(255), server_default=u"'0'")
    result = Column(String(255), server_default=u"''")
    error_string = Column(String(255))
    rev = Column(String(255), server_default=u"''")
    value = Column(Integer, server_default=u"'0'")


class Prescriptionsendingre(Info):
    __tablename__ = u'PrescriptionSendingRes'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(100))
    version = Column(Integer)
    interval_id = Column(ForeignKey('DrugChart.id'), index=True)
    drugComponent_id = Column(ForeignKey('DrugComponent.id'), index=True)

    drugComponent = relationship(u'Drugcomponent')
    interval = relationship(u'Drugchart')


class Prescriptionsto1c(Info):
    __tablename__ = u'PrescriptionsTo1C'

    interval_id = Column(Integer, primary_key=True)
    errCount = Column(Integer, nullable=False, server_default=u"'0'")
    info = Column(String(1024))
    is_prescription = Column(Integer)
    new_status = Column(Integer)
    old_status = Column(Integer)
    sendTime = Column(DateTime, nullable=False, server_default=u'CURRENT_TIMESTAMP')


class QuotaCatalog(Info):
    __tablename__ = u'QuotaCatalog'

    id = Column(Integer, primary_key=True)
    finance_id = Column(ForeignKey('rbFinance.id'), nullable=False, index=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)
    catalogNumber = Column(Unicode(45), nullable=False, server_default=u"''")
    documentDate = Column(Date, nullable=True)
    documentNumber = Column(Unicode(45), nullable=True)
    documentCorresp = Column(Unicode(256), nullable=True)
    comment = Column(UnicodeText, nullable=True)


class QuotaType(Info):
    __tablename__ = u'QuotaType'

    id = Column(Integer, primary_key=True)
    catalog_id = Column(ForeignKey('QuotaCatalog.id'), nullable=False, index=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    class_ = Column(u'class', Integer, nullable=False)
    profile_code = Column(String(16))
    group_code = Column(String(16))
    type_code = Column(String(16))
    code = Column(String(16), nullable=False)
    name = Column(Unicode(255), nullable=False)
    teenOlder = Column(Integer, nullable=False)
    price = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")

    def __unicode__(self):
        return self.name


class VMPQuotaDetails(Info):
    __tablename__ = u'VMPQuotaDetails'

    id = Column(Integer, primary_key=True)
    pacientModel_id = Column(ForeignKey('rbPacientModel.id'), nullable=False, index=True)
    treatment_id = Column(ForeignKey('rbTreatment.id'), nullable=False, index=True)
    quotaType_id = Column(ForeignKey('QuotaType.id'), nullable=False, index=True)


class MKB_VMPQuotaFilter(Info):
    __tablename__ = u'MKB_VMPQuotaFilter'

    id = Column(Integer, primary_key=True)
    MKB_id = Column(ForeignKey('MKB.id'), nullable=False, index=True)
    quotaDetails_id = Column(ForeignKey('VMPQuotaDetails.id'), nullable=False, index=True)


class Quoting(Info):
    __tablename__ = u'Quoting'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    quotaType_id = Column(Integer)
    beginDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    limitation = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    confirmed = Column(Integer, nullable=False, server_default=u"'0'")
    inQueue = Column(Integer, nullable=False, server_default=u"'0'")


class Quotingbyspeciality(Info):
    __tablename__ = u'QuotingBySpeciality'

    id = Column(Integer, primary_key=True)
    speciality_id = Column(ForeignKey('rbSpeciality.id'), nullable=False, index=True)
    organisation_id = Column(ForeignKey('Organisation.id'), nullable=False, index=True)
    coupons_quote = Column(Integer)
    coupons_remaining = Column(Integer)

    organisation = relationship(u'Organisation')
    speciality = relationship(u'Rbspeciality')


class Quotingbytime(Info):
    __tablename__ = u'QuotingByTime'

    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer)
    quoting_date = Column(Date, nullable=False)
    QuotingTimeStart = Column(Time, nullable=False)
    QuotingTimeEnd = Column(Time, nullable=False)
    QuotingType = Column(Integer)


class QuotingRegion(Info):
    __tablename__ = u'Quoting_Region'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(Integer, index=True)
    region_code = Column(String(13), index=True)
    limitation = Column(Integer, nullable=False, server_default=u"'0'")
    used = Column(Integer, nullable=False, server_default=u"'0'")
    confirmed = Column(Integer, nullable=False, server_default=u"'0'")
    inQueue = Column(Integer, nullable=False, server_default=u"'0'")


class Setting(Info):
    __tablename__ = u'Setting'

    id = Column(Integer, primary_key=True)
    path = Column(String(255), nullable=False, unique=True)
    value = Column(Text, nullable=False)


class Socstatu(Info):
    __tablename__ = u'SocStatus'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    socStatusClass_id = Column(Integer, nullable=False, index=True)
    socStatusType_id = Column(Integer, nullable=False, index=True)


class Stockmotion(Info):
    __tablename__ = u'StockMotion'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False)
    type = Column(Integer, server_default=u"'0'")
    date = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    supplier_id = Column(ForeignKey('OrgStructure.id'), index=True)
    receiver_id = Column(ForeignKey('OrgStructure.id'), index=True)
    note = Column(String, nullable=False)
    supplierPerson_id = Column(ForeignKey('Person.id'), index=True)
    receiverPerson_id = Column(ForeignKey('Person.id'), index=True)

    createPerson = relationship(u'Person', primaryjoin='Stockmotion.createPerson_id == Person.id')
    modifyPerson = relationship(u'Person', primaryjoin='Stockmotion.modifyPerson_id == Person.id')
    receiverPerson = relationship(u'Person', primaryjoin='Stockmotion.receiverPerson_id == Person.id')
    receiver = relationship(u'Orgstructure', primaryjoin='Stockmotion.receiver_id == Orgstructure.id')
    supplierPerson = relationship(u'Person', primaryjoin='Stockmotion.supplierPerson_id == Person.id')
    supplier = relationship(u'Orgstructure', primaryjoin='Stockmotion.supplier_id == Orgstructure.id')


class StockmotionItem(Info):
    __tablename__ = u'StockMotion_Item'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('StockMotion.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    nomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    finance_id = Column(ForeignKey('rbFinance.id'), index=True)
    qnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    sum = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    oldQnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    oldSum = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    oldFinance_id = Column(ForeignKey('rbFinance.id'), index=True)
    isOut = Column(Integer, nullable=False, server_default=u"'0'")
    note = Column(String, nullable=False)

    finance = relationship(u'Rbfinance', primaryjoin='StockmotionItem.finance_id == Rbfinance.id')
    master = relationship(u'Stockmotion')
    nomenclature = relationship(u'Rbnomenclature')
    oldFinance = relationship(u'Rbfinance', primaryjoin='StockmotionItem.oldFinance_id == Rbfinance.id')


class Stockrecipe(Info):
    __tablename__ = u'StockRecipe'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False)
    group_id = Column(ForeignKey('StockRecipe.id'), index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)

    createPerson = relationship(u'Person', primaryjoin='Stockrecipe.createPerson_id == Person.id')
    group = relationship(u'Stockrecipe', remote_side=[id])
    modifyPerson = relationship(u'Person', primaryjoin='Stockrecipe.modifyPerson_id == Person.id')


class StockrecipeItem(Info):
    __tablename__ = u'StockRecipe_Item'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('StockRecipe.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    nomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    qnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    isOut = Column(Integer, nullable=False, server_default=u"'0'")

    master = relationship(u'Stockrecipe')
    nomenclature = relationship(u'Rbnomenclature')


class Stockrequisition(Info):
    __tablename__ = u'StockRequisition'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    createPerson_id = Column(ForeignKey('Person.id'), index=True)
    modifyDatetime = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    modifyPerson_id = Column(ForeignKey('Person.id'), index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    date = Column(Date, nullable=False, server_default=u"'0000-00-00'")
    deadline = Column(DateTime)
    supplier_id = Column(ForeignKey('OrgStructure.id'), index=True)
    recipient_id = Column(ForeignKey('OrgStructure.id'), index=True)
    revoked = Column(Integer, nullable=False, server_default=u"'0'")
    note = Column(String, nullable=False)

    createPerson = relationship(u'Person', primaryjoin='Stockrequisition.createPerson_id == Person.id')
    modifyPerson = relationship(u'Person', primaryjoin='Stockrequisition.modifyPerson_id == Person.id')
    recipient = relationship(u'Orgstructure', primaryjoin='Stockrequisition.recipient_id == Orgstructure.id')
    supplier = relationship(u'Orgstructure', primaryjoin='Stockrequisition.supplier_id == Orgstructure.id')


class StockrequisitionItem(Info):
    __tablename__ = u'StockRequisition_Item'

    id = Column(Integer, primary_key=True)
    master_id = Column(ForeignKey('StockRequisition.id'), nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    nomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    finance_id = Column(ForeignKey('rbFinance.id'), index=True)
    qnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    satisfiedQnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")

    finance = relationship(u'Rbfinance')
    master = relationship(u'Stockrequisition')
    nomenclature = relationship(u'Rbnomenclature')


class Stocktran(Info):
    __tablename__ = u'StockTrans'
    __table_args__ = (
        Index(u'cre', u'creOrgStructure_id', u'creNomenclature_id', u'creFinance_id'),
        Index(u'deb', u'debOrgStructure_id', u'debNomenclature_id', u'debFinance_id')
    )

    id = Column(BigInteger, primary_key=True)
    stockMotionItem_id = Column(ForeignKey('StockMotion_Item.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, server_default=u"'0000-00-00 00:00:00'")
    qnt = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    sum = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    debOrgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)
    debNomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    debFinance_id = Column(ForeignKey('rbFinance.id'), index=True)
    creOrgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)
    creNomenclature_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    creFinance_id = Column(ForeignKey('rbFinance.id'), index=True)

    creFinance = relationship(u'Rbfinance', primaryjoin='Stocktran.creFinance_id == Rbfinance.id')
    creNomenclature = relationship(u'Rbnomenclature', primaryjoin='Stocktran.creNomenclature_id == Rbnomenclature.id')
    creOrgStructure = relationship(u'Orgstructure', primaryjoin='Stocktran.creOrgStructure_id == Orgstructure.id')
    debFinance = relationship(u'Rbfinance', primaryjoin='Stocktran.debFinance_id == Rbfinance.id')
    debNomenclature = relationship(u'Rbnomenclature', primaryjoin='Stocktran.debNomenclature_id == Rbnomenclature.id')
    debOrgStructure = relationship(u'Orgstructure', primaryjoin='Stocktran.debOrgStructure_id == Orgstructure.id')
    stockMotionItem = relationship(u'StockmotionItem')


class Takentissuejournal(Info):
    __tablename__ = u'TakenTissueJournal'
    __table_args__ = (
        Index(u'period_barcode', u'period', u'barcode'),
    )

    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('Client.id'), nullable=False, index=True)
    tissueType_id = Column(ForeignKey('rbTissueType.id'), nullable=False, index=True)
    externalId = Column(String(30), nullable=False)
    amount = Column(Integer, nullable=False, server_default=u"'0'")
    unit_id = Column(ForeignKey('rbUnit.id'), index=True)
    datetimeTaken = Column(DateTime, nullable=False)
    execPerson_id = Column(ForeignKey('Person.id'), index=True)
    note = Column(String(128), nullable=False)
    barcode = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)

    client = relationship(u'Client')
    execPerson = relationship(u'Person')
    tissueType = relationship(u'Rbtissuetype')
    unit = relationship(u'Rbunit')

    @property
    def barcode_s(self):
        return code128C(self.barcode).decode('windows-1252')


class Tempinvalid(Info):
    __tablename__ = u'TempInvalid'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    type = Column(Integer, nullable=False, server_default=u"'0'")
    doctype = Column(Integer, nullable=False)
    doctype_id = Column(Integer, index=True)
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    client_id = Column(Integer, nullable=False, index=True)
    tempInvalidReason_id = Column(Integer, index=True)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False, index=True)
    person_id = Column(Integer, index=True)
    diagnosis_id = Column(Integer, index=True)
    sex = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    notes = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    closed = Column(Integer, nullable=False)
    prev_id = Column(Integer, index=True)
    insuranceOfficeMark = Column(Integer, nullable=False, server_default=u"'0'")
    caseBegDate = Column(Date, nullable=False)
    event_id = Column(Integer)


class Tempinvalidduplicate(Info):
    __tablename__ = u'TempInvalidDuplicate'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False)
    tempInvalid_id = Column(Integer, nullable=False, index=True)
    person_id = Column(Integer, index=True)
    date = Column(Date, nullable=False)
    serial = Column(String(8), nullable=False)
    number = Column(String(16), nullable=False)
    destination = Column(String(128), nullable=False)
    reason_id = Column(Integer, index=True)
    note = Column(String, nullable=False)
    insuranceOfficeMark = Column(Integer, nullable=False, server_default=u"'0'")


class TempinvalidPeriod(Info):
    __tablename__ = u'TempInvalid_Period'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    diagnosis_id = Column(Integer, index=True)
    begPerson_id = Column(Integer, index=True)
    begDate = Column(Date, nullable=False)
    endPerson_id = Column(Integer, index=True)
    endDate = Column(Date, nullable=False)
    isExternal = Column(Integer, nullable=False)
    regime_id = Column(Integer, index=True)
    break_id = Column(Integer, index=True)
    result_id = Column(Integer, index=True)
    note = Column(String(256), nullable=False)


class Tissue(Info):
    __tablename__ = u'Tissue'

    id = Column(Integer, primary_key=True)
    type_id = Column(ForeignKey('rbTissueType.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    barcode = Column(String(255), nullable=False, index=True)
    event_id = Column(ForeignKey('Event.id'), nullable=False, index=True)

    event = relationship(u'Event')
    type = relationship(u'Rbtissuetype')


class Uuid(Info):
    __tablename__ = u'UUID'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(100), nullable=False, unique=True)


class Variablesforsql(Info):
    __tablename__ = u'VariablesforSQL'

    id = Column(Integer, primary_key=True)
    specialVarName_id = Column(Integer, nullable=False)
    name = Column(String(64), nullable=False)
    var_type = Column(String(64), nullable=False)
    label = Column(String(64), nullable=False)


class Version(Info):
    __tablename__ = u'Versions'

    id = Column(Integer, primary_key=True)
    table = Column(String(64), nullable=False, unique=True)
    version = Column(Integer, nullable=False, server_default=u"'0'")


class Visit(Info):
    __tablename__ = u'Visit'

    id = Column(Integer, primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(Integer, index=True)
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(Integer, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")
    event_id = Column(Integer, ForeignKey('Event.id'), nullable=False, index=True)
    scene_id = Column(Integer, ForeignKey('rbScene.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    visitType_id = Column(Integer, ForeignKey('rbVisitType.id'), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey('Person.id'), nullable=False, index=True)
    isPrimary = Column(Integer, nullable=False)
    finance_id = Column(Integer, ForeignKey('rbFinance.id'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('rbService.id'), index=True)
    payStatus = Column(Integer, nullable=False)

    service = relationship(u'Rbservice')
    person = relationship(u'Person')
    finance = relationship(u'Rbfinance')
    scene = relationship(u'Rbscene')
    type = relationship(u'Rbvisittype')
    event = relationship(u'Event')


class ActionDocument(Info):
    __tablename__ = u'action_document'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    modify_date = Column(DateTime, nullable=False)
    template_id = Column(ForeignKey('rbPrintTemplate.id'), nullable=False, index=True)
    document = Column(MEDIUMBLOB, nullable=False)

    action = relationship(u'Action')
    template = relationship(u'Rbprinttemplate')


class BbtResponse(Info):
    __tablename__ = u'bbtResponse'

    id = Column(ForeignKey('Action.id'), primary_key=True)
    final = Column(Integer, nullable=False, server_default=u"'0'")
    defects = Column(Text)
    doctor_id = Column(ForeignKey('Person.id'), nullable=False, index=True)
    codeLIS = Column(String(20), nullable=False)

    doctor = relationship(u'Person')
    values_organism = relationship(
        u'BbtResultOrganism',
        primaryjoin='BbtResponse.id == BbtResultOrganism.action_id',
        foreign_keys=[id],
        uselist=True
    )
    values_text = relationship(
        u'BbtResultText',
        primaryjoin='BbtResponse.id == BbtResultText.action_id',
        foreign_keys=[id],
        uselist=True
    )
    # values_table = relationship(u'BbtResultTable')
    # values_image = relationship(u'BbtResultImage')


class BbtResultOrganism(Info):
    __tablename__ = u'bbtResult_Organism'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    organism_id = Column(ForeignKey('rbMicroorganism.id'), nullable=False, index=True)
    concentration = Column(String(256), nullable=False)

    microorganism = relationship(u'rbMicroorganism', lazy='joined')
    sens_values = relationship(u'BbtOrganism_SensValues', lazy='joined')


class BbtOrganism_SensValues(Info):
    __tablename__ = u'bbtOrganism_SensValues'
    __table_args__ = (
        Index(u'bbtResult_Organism_id_index', u'bbtResult_Organism_id'),
    )

    id = Column(Integer, primary_key=True)
    bbtResult_Organism_id = Column(ForeignKey('bbtResult_Organism.id'), nullable=False)
    antibiotic_id = Column(ForeignKey('rbAntibiotic.id'), index=True)
    MIC = Column(String(20), nullable=False)
    activity = Column(String(5), nullable=False)

    antibiotic = relationship(u'rbAntibiotic', lazy='joined')


class BbtResultText(Info):
    __tablename__ = u'bbtResult_Text'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    valueText = Column(Text)


class BbtResultTable(Info):
    __tablename__ = u'bbtResult_Table'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    indicator_id = Column(ForeignKey('rbBacIndicator.id'), nullable=False, index=True)
    normString = Column(String(256))
    normalityIndex = Column(Float)
    unit = Column(String(20))
    signDateTime = Column(DateTime, nullable=False)
    status = Column(Text)
    comment = Column(Text)

    indicator = relationship(u'rbBacIndicator')


class BbtResultImage(Info):
    __tablename__ = u'bbtResult_Image'
    __table_args__ = (
        Index(u'action_id_index', u'action_id', u'idx'),
    )

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False)
    idx = Column(Integer, nullable=False)
    description = Column(String(256))
    image = Column(BLOB, nullable=False)


class Mrbmodelagegroup(Info):
    __tablename__ = u'mrbModelAgeGroup'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelaidcase(Info):
    __tablename__ = u'mrbModelAidCase'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelaidpurpose(Info):
    __tablename__ = u'mrbModelAidPurpose'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelcategory(Info):
    __tablename__ = u'mrbModelCategory'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelcontinuation(Info):
    __tablename__ = u'mrbModelContinuation'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodeldiseaseclas(Info):
    __tablename__ = u'mrbModelDiseaseClass'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelexpectedresult(Info):
    __tablename__ = u'mrbModelExpectedResult'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelinstitutiontype(Info):
    __tablename__ = u'mrbModelInstitutionType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelsertificationrequirement(Info):
    __tablename__ = u'mrbModelSertificationRequirement'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class Mrbmodelstatebadnes(Info):
    __tablename__ = u'mrbModelStateBadness'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(128), nullable=False)


class NewTable(Info):
    __tablename__ = u'new_table'

    idnew_table = Column(Integer, primary_key=True)


class Rb64district(Info):
    __tablename__ = u'rb64District'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code_tfoms = Column(Integer, nullable=False)
    socr = Column(String(10), nullable=False)
    code = Column(String(15), nullable=False)
    index = Column(Integer)
    gninmb = Column(Integer, nullable=False)
    uno = Column(Integer)
    ocatd = Column(String(15), nullable=False)
    status = Column(Integer, nullable=False, server_default=u"'0'")
    parent = Column(Integer, nullable=False)
    infis = Column(String(15))
    prefix = Column(Integer, nullable=False)


class Rb64placetype(Info):
    __tablename__ = u'rb64PlaceType'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


class Rb64reason(Info):
    __tablename__ = u'rb64Reason'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class Rb64streettype(Info):
    __tablename__ = u'rb64StreetType'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


class Rbaptable(Info):
    __tablename__ = u'rbAPTable'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(256), nullable=False)
    tableName = Column(String(256), nullable=False)
    masterField = Column(String(256), nullable=False)


class Rbaptablefield(Info):
    __tablename__ = u'rbAPTableField'

    id = Column(Integer, primary_key=True)
    idx = Column(Integer, nullable=False)
    master_id = Column(ForeignKey('rbAPTable.id'), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    fieldName = Column(String(256), nullable=False)
    referenceTable = Column(String(256))

    master = relationship(u'Rbaptable', backref="fields")


class Rbacademicdegree(RBInfo):
    __tablename__ = u'rbAcademicDegree'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(Unicode(64), nullable=False)

    def __unicode__(self):
        return self.name


class Rbacademictitle(RBInfo):
    __tablename__ = u'rbAcademicTitle'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)

    def __unicode__(self):
        return self.name


class Rbaccountexportformat(RBInfo):
    __tablename__ = u'rbAccountExportFormat'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    prog = Column(String(128), nullable=False)
    preferentArchiver = Column(String(128), nullable=False)
    emailRequired = Column(Integer, nullable=False)
    emailTo = Column(String(64), nullable=False)
    subject = Column(Unicode(128), nullable=False)
    message = Column(Text, nullable=False)


class Rbaccountingsystem(RBInfo):
    __tablename__ = u'rbAccountingSystem'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    isEditable = Column(Integer, nullable=False, server_default=u"'0'")
    showInClientInfo = Column(Integer, nullable=False, server_default=u"'0'")


class Rbacheresult(RBInfo):
    __tablename__ = u'rbAcheResult'

    id = Column(Integer, primary_key=True)
    eventPurpose_id = Column(ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = Column(String(3, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(64, u'utf8_unicode_ci'), nullable=False)

    eventPurpose = relationship(u'Rbeventtypepurpose')


class Rbactionshedule(Info):
    __tablename__ = u'rbActionShedule'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, server_default=u"''")
    name = Column(String(64), nullable=False, server_default=u"''")
    period = Column(Integer, nullable=False, server_default=u"'1'")


class RbactionsheduleItem(Info):
    __tablename__ = u'rbActionShedule_Item'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    offset = Column(Integer, nullable=False, server_default=u"'0'")
    time = Column(Time, nullable=False, server_default=u"'00:00:00'")


class Rbactivity(Info):
    __tablename__ = u'rbActivity'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    regionalCode = Column(String(8), nullable=False, index=True)


class Rbagreementtype(Info):
    __tablename__ = u'rbAgreementType'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)
    quotaStatusModifier = Column(Integer, server_default=u"'0'")


class Rbanalysisstatus(Info):
    __tablename__ = u'rbAnalysisStatus'

    id = Column(Integer, primary_key=True)
    statusName = Column(String(80), nullable=False, unique=True)


class Rbanalyticalreport(Info):
    __tablename__ = u'rbAnalyticalReports'

    id = Column(Integer, primary_key=True)
    name = Column(String(45))
    PrintTemplate_id = Column(Integer)


class rbAntibiotic(RBInfo):
    __tablename__ = u'rbAntibiotic'

    id = Column(Integer, primary_key=True)
    code = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)


class Rbattachtype(Info):
    __tablename__ = u'rbAttachType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    temporary = Column(Integer, nullable=False)
    outcome = Column(Integer, nullable=False)
    finance_id = Column(Integer, nullable=False, index=True)


class rbBacIndicator(RBInfo):
    __tablename__ = u'rbBacIndicator'

    id = Column(Integer, primary_key=True)
    code = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)


class Rbblankaction(Info):
    __tablename__ = u'rbBlankActions'

    id = Column(Integer, primary_key=True)
    doctype_id = Column(ForeignKey('ActionType.id'), nullable=False, index=True)
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    checkingSerial = Column(Integer, nullable=False)
    checkingNumber = Column(Integer, nullable=False)
    checkingAmount = Column(Integer, nullable=False)

    doctype = relationship(u'Actiontype')


class Rbblanktempinvalid(Info):
    __tablename__ = u'rbBlankTempInvalids'

    id = Column(Integer, primary_key=True)
    doctype_id = Column(ForeignKey('rbTempInvalidDocument.id'), nullable=False, index=True)
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    checkingSerial = Column(Integer, nullable=False)
    checkingNumber = Column(Integer, nullable=False)
    checkingAmount = Column(Integer, nullable=False)

    doctype = relationship(u'Rbtempinvaliddocument')


class Rbbloodtype(RBInfo):
    __tablename__ = u'rbBloodType'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)


class Rbcashoperation(RBInfo):
    __tablename__ = u'rbCashOperation'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False)


class Rbcomplain(Info):
    __tablename__ = u'rbComplain'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, index=True)
    code = Column(String(64), nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)


class Rbcontacttype(RBInfo):
    __tablename__ = u'rbContactType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbcoreactionproperty(Info):
    __tablename__ = u'rbCoreActionProperty'

    id = Column(Integer, primary_key=True)
    actionType_id = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    actionPropertyType_id = Column(Integer, nullable=False)


class Rbcounter(Info):
    __tablename__ = u'rbCounter'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)
    value = Column(Integer, nullable=False, server_default=u"'0'")
    prefix = Column(String(32))
    separator = Column(String(8), server_default=u"' '")
    reset = Column(Integer, nullable=False, server_default=u"'0'")
    startDate = Column(DateTime, nullable=False)
    resetDate = Column(DateTime)
    sequenceFlag = Column(Integer, nullable=False, server_default=u"'0'")


class rbDiagnosisType(RBInfo):
    __tablename__ = u'rbDiagnosisType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    replaceInDiagnosis = Column(String(8), nullable=False)
    flatCode = Column(String(64), nullable=False)


class Rbdiet(Info):
    __tablename__ = u'rbDiet'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class rbDiseaseCharacter(RBInfo):
    __tablename__ = u'rbDiseaseCharacter'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    replaceInDiagnosis = Column(String(8), nullable=False)


class rbDiseasePhases(Info):
    __tablename__ = u'rbDiseasePhases'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    characterRelation = Column(Integer, nullable=False, server_default=u"'0'")


class rbDiseaseStage(Info):
    __tablename__ = u'rbDiseaseStage'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    characterRelation = Column(Integer, nullable=False, server_default=u"'0'")


class rbDispanser(RBInfo):
    __tablename__ = u'rbDispanser'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    observed = Column(Integer, nullable=False)


class Rbdocumenttype(RBInfo):
    __tablename__ = u'rbDocumentType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    regionalCode = Column(String(16), nullable=False)
    name = Column(Unicode(64), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey('rbDocumentTypeGroup.id'), nullable=False, index=True)
    serial_format = Column(Integer, nullable=False)
    number_format = Column(Integer, nullable=False)
    federalCode = Column(String(16), nullable=False)
    socCode = Column(String(8), nullable=False, index=True)
    TFOMSCode = Column(Integer)

    group = relationship(u'Rbdocumenttypegroup')

    def __init__(self):
        RBInfo.__init__(self)


class Rbdocumenttypegroup(RBInfo):
    __tablename__ = u'rbDocumentTypeGroup'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)

    def __init__(self):
        RBInfo.__init__(self)


class Rbemergencyaccident(Info):
    __tablename__ = u'rbEmergencyAccident'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencycausecall(Info):
    __tablename__ = u'rbEmergencyCauseCall'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)
    typeCause = Column(Integer, nullable=False, server_default=u"'0'")


class Rbemergencydeath(Info):
    __tablename__ = u'rbEmergencyDeath'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencydiseased(Info):
    __tablename__ = u'rbEmergencyDiseased'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyebriety(Info):
    __tablename__ = u'rbEmergencyEbriety'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencymethodtransportation(Info):
    __tablename__ = u'rbEmergencyMethodTransportation'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyplacecall(Info):
    __tablename__ = u'rbEmergencyPlaceCall'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyplacereceptioncall(Info):
    __tablename__ = u'rbEmergencyPlaceReceptionCall'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyreasonddelay(Info):
    __tablename__ = u'rbEmergencyReasondDelays'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyreceivedcall(Info):
    __tablename__ = u'rbEmergencyReceivedCall'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencyresult(Info):
    __tablename__ = u'rbEmergencyResult'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencytransferredtransportation(Info):
    __tablename__ = u'rbEmergencyTransferredTransportation'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbemergencytypeasset(RBInfo):
    __tablename__ = u'rbEmergencyTypeAsset'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    codeRegional = Column(String(8), nullable=False, index=True)


class Rbeventprofile(Info):
    __tablename__ = u'rbEventProfile'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    regionalCode = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class Rbeventtypepurpose(RBInfo):
    __tablename__ = u'rbEventTypePurpose'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    codePlace = Column(String(2))

    def __init__(self):
        RBInfo.__init__(self)


class Rbfinance(RBInfo):
    __tablename__ = u'rbFinance'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)

    def __init__(self):
        RBInfo.__init__(self)


class Rbfinance1c(Info):
    __tablename__ = u'rbFinance1C'

    id = Column(Integer, primary_key=True)
    code1C = Column(String(127), nullable=False)
    finance_id = Column(ForeignKey('rbFinance.id'), nullable=False, index=True)

    finance = relationship(u'Rbfinance')


class rbHealthGroup(Info):
    __tablename__ = u'rbHealthGroup'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class Rbhospitalbedprofile(RBInfo):
    __tablename__ = u'rbHospitalBedProfile'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    service_id = Column(Integer, index=True)

    def __init__(self):
        RBInfo.__init__(self)


class RbhospitalbedprofileService(Info):
    __tablename__ = u'rbHospitalBedProfile_Service'

    id = Column(Integer, primary_key=True)
    rbHospitalBedProfile_id = Column(ForeignKey('rbHospitalBedProfile.id'), nullable=False, index=True)
    rbService_id = Column(ForeignKey('rbService.id'), nullable=False, index=True)

    rbHospitalBedProfile = relationship(u'Rbhospitalbedprofile')
    rbService = relationship(u'Rbservice')


class Rbhospitalbedshedule(RBInfo):
    __tablename__ = u'rbHospitalBedShedule'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbhospitalbedtype(RBInfo):
    __tablename__ = u'rbHospitalBedType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbhurtfactortype(Info):
    __tablename__ = u'rbHurtFactorType'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(250), nullable=False, index=True)


class Rbhurttype(RBInfo):
    __tablename__ = u'rbHurtType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(256), nullable=False, index=True)


class Rbimagemap(Info):
    __tablename__ = u'rbImageMap'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)
    image = Column(MEDIUMBLOB, nullable=False)
    markSize = Column(Integer)


class Rbjobtype(RBInfo):
    __tablename__ = u'rbJobType'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, index=True)
    code = Column(String(64), nullable=False)
    regionalCode = Column(String(64), nullable=False)
    name = Column(Unicode(128), nullable=False)
    laboratory_id = Column(Integer, index=True)
    isInstant = Column(Integer, nullable=False, server_default=u"'0'")

    def __init__(self):
        RBInfo.__init__(self)


class Rblaboratory(Info):
    __tablename__ = u'rbLaboratory'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    protocol = Column(Integer, nullable=False)
    address = Column(String(128), nullable=False)
    ownName = Column(String(128), nullable=False)
    labName = Column(String(128), nullable=False)


class RblaboratoryTest(Info):
    __tablename__ = u'rbLaboratory_Test'
    __table_args__ = (
        Index(u'code', u'book', u'code'),
    )

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    test_id = Column(Integer, nullable=False, index=True)
    book = Column(String(64), nullable=False)
    code = Column(String(64), nullable=False)


class Rbmkbsubclas(Info):
    __tablename__ = u'rbMKBSubclass'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(String(128), nullable=False)


class RbmkbsubclassItem(Info):
    __tablename__ = u'rbMKBSubclass_Item'
    __table_args__ = (
        Index(u'master_id', u'master_id', u'code'),
    )

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False)
    code = Column(String(8), nullable=False)
    name = Column(String(128), nullable=False)


class Rbmealtime(Info):
    __tablename__ = u'rbMealTime'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    begTime = Column(Time, nullable=False)
    endTime = Column(Time, nullable=False)


class Rbmedicalaidprofile(Info):
    __tablename__ = u'rbMedicalAidProfile'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    regionalCode = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)


class Rbmedicalaidtype(Info):
    __tablename__ = u'rbMedicalAidType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False)


class Rbmedicalaidunit(Info):
    __tablename__ = u'rbMedicalAidUnit'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    descr = Column(String(64), nullable=False)
    regionalCode = Column(String(1), nullable=False)


class Rbmedicalkind(Info):
    __tablename__ = u'rbMedicalKind'

    id = Column(Integer, primary_key=True)
    code = Column(String(1, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(64, u'utf8_unicode_ci'), nullable=False)


class Rbmenu(Info):
    __tablename__ = u'rbMenu'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class RbmenuContent(Info):
    __tablename__ = u'rbMenu_Content'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    mealTime_id = Column(Integer, nullable=False, index=True)
    diet_id = Column(Integer, nullable=False, index=True)


class Rbmesspecification(RBInfo):
    __tablename__ = u'rbMesSpecification'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    regionalCode = Column(String(16), nullable=False)
    name = Column(Unicode(64), nullable=False)
    done = Column(Integer, nullable=False)


class Rbmethodofadministration(Info):
    __tablename__ = u'rbMethodOfAdministration'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class rbMicroorganism(RBInfo):
    __tablename__ = u'rbMicroorganism'

    id = Column(Integer, primary_key=True)
    code = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)


class Rbnet(RBInfo):
    __tablename__ = u'rbNet'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    sexCode = Column("sex", Integer, nullable=False, server_default=u"'0'")
    age = Column(Unicode(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)

    @property
    def sex(self):
        return formatSex(self.sexCode)


class Rbnomenclature(Info):
    __tablename__ = u'rbNomenclature'

    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey('rbNomenclature.id'), index=True)
    code = Column(String(64), nullable=False)
    regionalCode = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)

    group = relationship(u'Rbnomenclature', remote_side=[id])


class Rbokfs(RBInfo):
    __tablename__ = u'rbOKFS'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    ownership = Column(Integer, nullable=False, server_default=u"'0'")


class Rbokpf(RBInfo):
    __tablename__ = u'rbOKPF'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbokved(Info):
    __tablename__ = u'rbOKVED'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, index=True)
    div = Column(String(10), nullable=False)
    class_ = Column(u'class', String(2), nullable=False)
    group_ = Column(String(2), nullable=False)
    vid = Column(String(2), nullable=False)
    OKVED = Column(String(8), nullable=False, index=True)
    name = Column(String(250), nullable=False, index=True)


class Rboperationtype(Info):
    __tablename__ = u'rbOperationType'

    id = Column(Integer, primary_key=True)
    cd_r = Column(Integer, nullable=False)
    cd_subr = Column(Integer, nullable=False)
    code = Column(String(8), nullable=False, index=True)
    ktso = Column(Integer, nullable=False)
    name = Column(String(64), nullable=False, index=True)


class Rbpacientmodel(RBInfo):
    __tablename__ = u'rbPacientModel'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False)
    name = Column(Text, nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbpayrefusetype(RBInfo):
    __tablename__ = u'rbPayRefuseType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(128), nullable=False, index=True)
    finance_id = Column(Integer, nullable=False, index=True)
    rerun = Column(Integer, nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbpaytype(Info):
    __tablename__ = u'rbPayType'

    id = Column(Integer, primary_key=True)
    code = Column(String(2, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(64, u'utf8_unicode_ci'), nullable=False)


class Rbpolicytype(RBInfo):
    __tablename__ = u'rbPolicyType'

    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True)
    name = Column(Unicode(256), nullable=False, index=True)
    TFOMSCode = Column(String(8))

    def __init__(self):
        RBInfo.__init__(self)


class Rbpost(RBInfo):
    __tablename__ = u'rbPost'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    regionalCode = Column(String(8), nullable=False)
    key = Column(String(6), nullable=False, index=True)
    high = Column(String(6), nullable=False)
    flatCode = Column(String(65), nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbprinttemplate(Info):
    __tablename__ = u'rbPrintTemplate'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    context = Column(String(64), nullable=False)
    fileName = Column(String(128), nullable=False)
    default = Column(String, nullable=False)
    dpdAgreement = Column(Integer, nullable=False, server_default=u"'0'")
    render = Column(Integer, nullable=False, server_default=u"'0'")
    templateText = Column(String, nullable=False)

    meta_data = relationship('Rbprinttemplatemeta', lazy=False)


class Rbquotastatu(Info):
    __tablename__ = u'rbQuotaStatus'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)


class Rbreasonofabsence(RBInfo):
    __tablename__ = u'rbReasonOfAbsence'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)

    def __init__(self):
        RBInfo.__init__(self)


class Rbrelationtype(RBInfo):
    __tablename__ = u'rbRelationType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    leftName = Column(String(64), nullable=False)
    rightName = Column(String(64), nullable=False)
    isDirectGenetic = Column(Integer, nullable=False, server_default=u"'0'")
    isBackwardGenetic = Column(Integer, nullable=False, server_default=u"'0'")
    isDirectRepresentative = Column(Integer, nullable=False, server_default=u"'0'")
    isBackwardRepresentative = Column(Integer, nullable=False, server_default=u"'0'")
    isDirectEpidemic = Column(Integer, nullable=False, server_default=u"'0'")
    isBackwardEpidemic = Column(Integer, nullable=False, server_default=u"'0'")
    isDirectDonation = Column(Integer, nullable=False, server_default=u"'0'")
    isBackwardDonation = Column(Integer, nullable=False, server_default=u"'0'")
    leftSex = Column(Integer, nullable=False, server_default=u"'0'")
    rightSex = Column(Integer, nullable=False, server_default=u"'0'")
    regionalCode = Column(String(64), nullable=False)
    regionalReverseCode = Column(String(64), nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbrequesttype(RBInfo):
    __tablename__ = u'rbRequestType'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    relevant = Column(Integer, nullable=False, server_default=u"'1'")

    def __init__(self):
        RBInfo.__init__(self)


class Rbresult(RBInfo):
    __tablename__ = u'rbResult'

    id = Column(Integer, primary_key=True)
    eventPurpose_id = Column(Integer, nullable=False, index=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    continued = Column(Integer, nullable=False)
    regionalCode = Column(String(8), nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbscene(RBInfo):
    __tablename__ = u'rbScene'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    serviceModifier = Column(Unicode(128), nullable=False)

    def __init__(self):
        RBInfo.__init__(self)


class Rbservice(RBInfo):
    __tablename__ = u'rbService'
    __table_args__ = (
        Index(u'infis', u'infis', u'eisLegacy'),
    )

    id = Column(Integer, primary_key=True)
    code = Column(String(31), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    eisLegacy = Column(Boolean, nullable=False)
    nomenclatureLegacy = Column(Integer, nullable=False, server_default=u"'0'")
    license = Column(Integer, nullable=False)
    infis = Column(String(31), nullable=False)
    begDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)
    medicalAidProfile_id = Column(ForeignKey('rbMedicalAidProfile.id'), index=True)
    adultUetDoctor = Column(Float(asdecimal=True), server_default=u"'0'")
    adultUetAverageMedWorker = Column(Float(asdecimal=True), server_default=u"'0'")
    childUetDoctor = Column(Float(asdecimal=True), server_default=u"'0'")
    childUetAverageMedWorker = Column(Float(asdecimal=True), server_default=u"'0'")
    rbMedicalKind_id = Column(ForeignKey('rbMedicalKind.id'), index=True)
    UET = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")
    departCode = Column(String(3))

    medicalAidProfile = relationship(u'Rbmedicalaidprofile')
    rbMedicalKind = relationship(u'Rbmedicalkind')

    def __init__(self):
        RBInfo.__init__(self)


class Rbserviceclas(Info):
    __tablename__ = u'rbServiceClass'
    __table_args__ = (
        Index(u'section', u'section', u'code'),
    )

    id = Column(Integer, primary_key=True)
    section = Column(String(1), nullable=False)
    code = Column(String(3), nullable=False)
    name = Column(String(200), nullable=False)


class Rbservicefinance(Info):
    __tablename__ = u'rbServiceFinance'

    id = Column(Integer, primary_key=True)
    code = Column(String(2, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(64, u'utf8_unicode_ci'), nullable=False)


class Rbservicegroup(Info):
    __tablename__ = u'rbServiceGroup'
    __table_args__ = (
        Index(u'group_id', u'group_id', u'service_id'),
    )

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, nullable=False)
    service_id = Column(Integer, nullable=False)
    required = Column(Integer, nullable=False, server_default=u"'0'")


class Rbservicesection(Info):
    __tablename__ = u'rbServiceSection'

    id = Column(Integer, primary_key=True)
    code = Column(String(1), nullable=False)
    name = Column(String(100), nullable=False)


class Rbservicetype(Info):
    __tablename__ = u'rbServiceType'
    __table_args__ = (
        Index(u'section', u'section', u'code'),
    )

    id = Column(Integer, primary_key=True)
    section = Column(String(1), nullable=False)
    code = Column(String(3), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)


class Rbserviceuet(Info):
    __tablename__ = u'rbServiceUET'

    id = Column(Integer, primary_key=True)
    rbService_id = Column(ForeignKey('rbService.id'), nullable=False, index=True)
    age = Column(String(10, u'utf8_unicode_ci'), nullable=False)
    UET = Column(Float(asdecimal=True), nullable=False, server_default=u"'0'")

    rbService = relationship(u'Rbservice')


class RbserviceProfile(Info):
    __tablename__ = u'rbService_Profile'
    __table_args__ = (
        Index(u'id', u'id', u'idx'),
    )

    id = Column(Integer, primary_key=True)
    idx = Column(Integer, nullable=False, server_default=u"'0'")
    master_id = Column(ForeignKey('rbService.id'), nullable=False, index=True)
    speciality_id = Column(ForeignKey('rbSpeciality.id'), index=True)
    sex = Column(Integer, nullable=False, server_default=u"'0'")
    age = Column(String(9), nullable=False, server_default=u"''")
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    mkbRegExp = Column(String(64), nullable=False, server_default=u"''")
    medicalAidProfile_id = Column(ForeignKey('rbMedicalAidProfile.id'), index=True)

    master = relationship(u'Rbservice')
    medicalAidProfile = relationship(u'Rbmedicalaidprofile')
    speciality = relationship(u'Rbspeciality')


class Rbsocstatusclass(Info):
    __tablename__ = u'rbSocStatusClass'

    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey('rbSocStatusClass.id'), index=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)

    group = relationship(u'Rbsocstatusclass', remote_side=[id])

    def __unicode__(self):
        return self.name

# class Rbsocstatusclasstypeassoc(Info):
#     __tablename__ = u'rbSocStatusClassTypeAssoc'
#     __table_args__ = (
#         Index(u'type_id', u'type_id', u'class_id'),
#     )
#
#     id = Column(Integer, primary_key=True)
#     class_id = Column(Integer, ForeignKey('rbSocStatusClass.id'), nullable=False, index=True)
#     type_id = Column(Integer, ForeignKey('rbSocStatusType.id'), nullable=False)
Rbsocstatusclasstypeassoc = Table('rbSocStatusClassTypeAssoc', metadata,
    Column('class_id', Integer, ForeignKey('rbSocStatusClass.id')),
    Column('type_id', Integer, ForeignKey('rbSocStatusType.id'))
    )


class Rbsocstatustype(Info):
    __tablename__ = u'rbSocStatusType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(250), nullable=False, index=True)
    socCode = Column(String(8), nullable=False, index=True)
    TFOMSCode = Column(Integer)
    regionalCode = Column(String(8), nullable=False)

    classes = relationship(u'Rbsocstatusclass', secondary=Rbsocstatusclasstypeassoc)


class Rbspecialvariablespreference(Info):
    __tablename__ = u'rbSpecialVariablesPreferences'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    arguments_raw = Column('arguments', Text)
    query_text = Column('query', Text, nullable=False)

    @property
    def arguments(self):
        import json
        try:
            return json.loads(self.arguments_raw) or []
        except:
            return []


class Rbspeciality(RBInfo):
    __tablename__ = u'rbSpeciality'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    OKSOName = Column(Unicode(60), nullable=False)
    OKSOCode = Column(String(8), nullable=False)
    service_id = Column(Integer, index=True)
    sex = Column(Integer, nullable=False)
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)
    mkbFilter = Column(String(32), nullable=False)
    regionalCode = Column(String(16), nullable=False)
    quotingEnabled = Column(Integer, server_default=u"'0'")

    def __init__(self):
        RBInfo.__init__(self)


class Rbstorage(Info):
    __tablename__ = u'rbStorage'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(50), nullable=False, unique=True)
    name = Column(String(256))
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), index=True)

    orgStructure = relationship(u'Orgstructure')


class Rbtariffcategory(RBInfo):
    __tablename__ = u'rbTariffCategory'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class Rbtarifftype(Info):
    __tablename__ = u'rbTariffType'

    id = Column(Integer, primary_key=True)
    code = Column(String(2, u'utf8_unicode_ci'), nullable=False)
    name = Column(String(64, u'utf8_unicode_ci'), nullable=False)


class Rbtempinvalidbreak(Info):
    __tablename__ = u'rbTempInvalidBreak'

    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(80), nullable=False, index=True)


class Rbtempinvaliddocument(Info):
    __tablename__ = u'rbTempInvalidDocument'

    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(80), nullable=False, index=True)
    checkingSerial = Column(Enum(u'???', u'?????', u'??????'), nullable=False)
    checkingNumber = Column(Enum(u'???', u'?????', u'??????'), nullable=False)
    checkingAmount = Column(Enum(u'???', u'????????'), nullable=False)


class Rbtempinvalidduplicatereason(Info):
    __tablename__ = u'rbTempInvalidDuplicateReason'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False)


class Rbtempinvalidreason(Info):
    __tablename__ = u'rbTempInvalidReason'

    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    requiredDiagnosis = Column(Integer, nullable=False)
    grouping = Column(Integer, nullable=False)
    primary = Column(Integer, nullable=False)
    prolongate = Column(Integer, nullable=False)
    restriction = Column(Integer, nullable=False)
    regionalCode = Column(String(3), nullable=False)


class Rbtempinvalidregime(Info):
    __tablename__ = u'rbTempInvalidRegime'

    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False, server_default=u"'0'")
    doctype_id = Column(Integer, index=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class Rbtempinvalidresult(Info):
    __tablename__ = u'rbTempInvalidResult'

    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False, server_default=u"'0'")
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(80), nullable=False, index=True)
    able = Column(Integer, nullable=False)
    closed = Column(Integer, nullable=False, server_default=u"'0'")
    status = Column(Integer, nullable=False)


class Rbtest(Info):
    __tablename__ = u'rbTest'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    deleted = Column(Integer, nullable=False, server_default=u"'0'")


class Rbtesttubetype(Info):
    __tablename__ = u'rbTestTubeType'

    id = Column(Integer, primary_key=True)
    code = Column(String(64))
    name = Column(String(128), nullable=False)
    volume = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey('rbUnit.id'), nullable=False, index=True)
    covCol = Column(String(64))
    image = Column(MEDIUMBLOB)
    color = Column(String(8))

    unit = relationship(u'Rbunit')


class Rbthesauru(Info):
    __tablename__ = u'rbThesaurus'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, index=True)
    code = Column(String(30), nullable=False, index=True)
    name = Column(String(255), nullable=False, server_default=u"''")
    template = Column(String(255), nullable=False, server_default=u"''")


class Rbtimequotingtype(Info):
    __tablename__ = u'rbTimeQuotingType'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, nullable=False, unique=True)
    name = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)


class Rbtissuetype(RBInfo):
    __tablename__ = u'rbTissueType'

    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    group_id = Column(ForeignKey('rbTissueType.id'), index=True)
    sexCode = Column("sex", Integer, nullable=False, server_default=u"'0'")

    group = relationship(u'Rbtissuetype', remote_side=[id])

    @property
    def sex(self):
        return {0: u'Любой',
                1: u'М',
                2: u'Ж'}[self.sexCode]


class Rbtransferdatetype(Info):
    __tablename__ = u'rbTransferDateType'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, nullable=False, unique=True)
    name = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)


class rbTraumaType(RBInfo):
    __tablename__ = u'rbTraumaType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)

    def __init__(self):
        RBInfo.__init__(self)

class Rbtreatment(RBInfo):
    __tablename__ = u'rbTreatment'

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False)
    name = Column(Text, nullable=False)


class Rbtrfubloodcomponenttype(RBInfo):
    __tablename__ = u'rbTrfuBloodComponentType'

    id = Column(Integer, primary_key=True)
    trfu_id = Column(Integer)
    code = Column(String(32))
    name = Column(String(256))
    unused = Column(Integer, nullable=False, server_default=u"'0'")


class Rbtrfulaboratorymeasuretype(Info):
    __tablename__ = u'rbTrfuLaboratoryMeasureTypes'

    id = Column(Integer, primary_key=True)
    trfu_id = Column(Integer)
    name = Column(String(255))


class Rbtrfuproceduretype(Info):
    __tablename__ = u'rbTrfuProcedureTypes'

    id = Column(Integer, primary_key=True)
    trfu_id = Column(Integer)
    name = Column(String(255))
    unused = Column(Integer, nullable=False, server_default=u"'0'")


class Rbufms(Info):
    __tablename__ = u'rbUFMS'

    id = Column(Integer, primary_key=True)
    code = Column(String(50, u'utf8_bin'), nullable=False)
    name = Column(String(256, u'utf8_bin'), nullable=False)


class Rbunit(RBInfo):
    __tablename__ = u'rbUnit'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode(256), index=True)
    name = Column(Unicode(256), index=True)


class Rbuserprofile(Info):
    __tablename__ = u'rbUserProfile'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    withDep = Column(Integer, nullable=False, server_default=u"'0'")


class RbuserprofileRight(Info):
    __tablename__ = u'rbUserProfile_Right'

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, nullable=False, index=True)
    userRight_id = Column(Integer, nullable=False, index=True)


class Rbuserright(Info):
    __tablename__ = u'rbUserRight'

    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)


class Rbvisittype(RBInfo):
    __tablename__ = u'rbVisitType'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    serviceModifier = Column(Unicode(128), nullable=False)


class RbF001Tfom(Info):
    __tablename__ = u'rb_F001_Tfoms'

    tf_kod = Column(String(255), primary_key=True)
    address = Column(String(255))
    d_edit = Column(Date)
    d_end = Column(Date)
    e_mail = Column(String(255))
    fam_dir = Column(String(255))
    fax = Column(String(255))
    idx = Column(String(255))
    im_dir = Column(String(255))
    kf_tf = Column(BigInteger)
    name_tfk = Column(String(255))
    name_tfp = Column(String(255))
    ot_dir = Column(String(255))
    phone = Column(String(255))
    tf_ogrn = Column(String(255))
    tf_okato = Column(String(255))
    www = Column(String(255))


class RbF002Smo(Info):
    __tablename__ = u'rb_F002_SMO'

    smocod = Column(String(255), primary_key=True)
    addr_f = Column(String(255))
    addr_j = Column(String(255))
    d_begin = Column(Date)
    d_edit = Column(Date)
    d_end = Column(Date)
    d_start = Column(Date)
    data_e = Column(Date)
    duved = Column(Date)
    e_mail = Column(String(255))
    fam_ruk = Column(String(255))
    fax = Column(String(255))
    im_ruk = Column(String(255))
    index_f = Column(String(255))
    index_j = Column(String(255))
    inn = Column(String(255))
    kol_zl = Column(BigInteger)
    kpp = Column(String(255))
    n_doc = Column(String(255))
    nal_p = Column(String(255))
    nam_smok = Column(String(255))
    nam_smop = Column(String(255))
    name_e = Column(String(255))
    ogrn = Column(String(255))
    okopf = Column(String(255))
    org = Column(BigInteger)
    ot_ruk = Column(String(255))
    phone = Column(String(255))
    tf_okato = Column(String(255))
    www = Column(String(255))


class RbF003Mo(Info):
    __tablename__ = u'rb_F003_MO'

    mcod = Column(String(255), primary_key=True)
    addr_j = Column(String(255))
    d_begin = Column(Date)
    d_edit = Column(Date)
    d_end = Column(Date)
    d_start = Column(Date)
    data_e = Column(Date)
    duved = Column(Date)
    e_mail = Column(String(255))
    fam_ruk = Column(String(255))
    fax = Column(String(255))
    im_ruk = Column(String(255))
    index_j = Column(String(255))
    inn = Column(String(255))
    kpp = Column(String(255))
    lpu = Column(Integer)
    mp = Column(String(255))
    n_doc = Column(String(255))
    nam_mok = Column(String(255))
    nam_mop = Column(String(255))
    name_e = Column(String(255))
    ogrn = Column(String(255))
    okopf = Column(String(255))
    org = Column(BigInteger)
    ot_ruk = Column(String(255))
    phone = Column(String(255))
    tf_okato = Column(String(255))
    vedpri = Column(BigInteger)
    www = Column(String(255))


class RbF007Vedom(Info):
    __tablename__ = u'rb_F007_Vedom'

    idved = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    vedname = Column(String(255))


class RbF008Tipom(Info):
    __tablename__ = u'rb_F008_TipOMS'

    iddoc = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    docname = Column(String(255))


class RbF009Statzl(Info):
    __tablename__ = u'rb_F009_StatZL'

    idstatus = Column(String(255), primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    statusname = Column(String(255))


class RbF010Subekti(Info):
    __tablename__ = u'rb_F010_Subekti'

    kod_tf = Column(String(255), primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    kod_okato = Column(String(255))
    okrug = Column(BigInteger)
    subname = Column(String(255))


class RbF011Tipdoc(Info):
    __tablename__ = u'rb_F011_Tipdoc'

    iddoc = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    docname = Column(String(255))
    docnum = Column(String(255))
    docser = Column(String(255))


class RbF015Fedokr(Info):
    __tablename__ = u'rb_F015_FedOkr'

    kod_ok = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    okrname = Column(String(255))


class RbKladr(Info):
    __tablename__ = u'rb_Kladr'

    code = Column(String(255), primary_key=True)
    gninmb = Column(String(255))
    idx = Column(String(255))
    name = Column(String(255))
    ocatd = Column(String(255))
    socr = Column(String(255))
    status = Column(String(255))
    uno = Column(String(255))


class RbKladrstreet(Info):
    __tablename__ = u'rb_KladrStreet'

    code = Column(String(255), primary_key=True)
    gninmb = Column(String(255))
    idx = Column(String(255))
    name = Column(String(255))
    ocatd = Column(String(255))
    socr = Column(String(255))
    uno = Column(String(255))


class RbM001Mkb10(Info):
    __tablename__ = u'rb_M001_MKB10'

    idds = Column(String(255), primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    dsname = Column(String(255))


class RbO001Oksm(Info):
    __tablename__ = u'rb_O001_Oksm'

    kod = Column(String(255), primary_key=True)
    alfa2 = Column(String(255))
    alfa3 = Column(String(255))
    data_upd = Column(Date)
    name11 = Column(String(255))
    name12 = Column(String(255))
    nomakt = Column(String(255))
    nomdescr = Column(String(255))
    status = Column(BigInteger)


class RbO002Okato(Info):
    __tablename__ = u'rb_O002_Okato'

    ter = Column(String(255), primary_key=True)
    centrum = Column(String(255))
    data_upd = Column(Date)
    kod1 = Column(String(255))
    kod2 = Column(String(255))
    kod3 = Column(String(255))
    name1 = Column(String(255))
    nomakt = Column(String(255))
    nomdescr = Column(String(255))
    razdel = Column(String(255))
    status = Column(BigInteger)


class RbO003Okved(Info):
    __tablename__ = u'rb_O003_Okved'

    kod = Column(String(255), primary_key=True)
    data_upd = Column(Date)
    name11 = Column(String(255))
    name12 = Column(String(255))
    nomakt = Column(String(255))
    nomdescr = Column(String(255))
    prazdel = Column(String(255))
    razdel = Column(String(255))
    status = Column(BigInteger)


class RbO004Okf(Info):
    __tablename__ = u'rb_O004_Okfs'

    kod = Column(String(255), primary_key=True)
    alg = Column(String(255))
    data_upd = Column(Date)
    name1 = Column(String(255))
    nomakt = Column(String(255))
    status = Column(BigInteger)


class RbO005Okopf(Info):
    __tablename__ = u'rb_O005_Okopf'

    kod = Column(String(255), primary_key=True)
    alg = Column(String(255))
    data_upd = Column(Date)
    name1 = Column(String(255))
    nomakt = Column(String(255))
    status = Column(BigInteger)


class RbV001Nomerclr(Info):
    __tablename__ = u'rb_V001_Nomerclr'

    idrb = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    rbname = Column(String(255))


class RbV002Profot(Info):
    __tablename__ = u'rb_V002_ProfOt'

    idpr = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    prname = Column(String(255))


class RbV003Licusl(Info):
    __tablename__ = u'rb_V003_LicUsl'

    idrl = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    ierarh = Column(BigInteger)
    licname = Column(String(255))
    prim = Column(BigInteger)


class RbV004Medspec(Info):
    __tablename__ = u'rb_V004_Medspec'

    idmsp = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    mspname = Column(String(255))


class RbV005Pol(Info):
    __tablename__ = u'rb_V005_Pol'

    idpol = Column(BigInteger, primary_key=True)
    polname = Column(String(255))


class RbV006Uslmp(Info):
    __tablename__ = u'rb_V006_UslMp'

    idump = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    umpname = Column(String(255))


class RbV007Nommo(Info):
    __tablename__ = u'rb_V007_NomMO'

    idnmo = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    nmoname = Column(String(255))


class RbV008Vidmp(Info):
    __tablename__ = u'rb_V008_VidMp'

    idvmp = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    vmpname = Column(String(255))


class RbV009Rezult(Info):
    __tablename__ = u'rb_V009_Rezult'

    idrmp = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    iduslov = Column(BigInteger)
    rmpname = Column(String(255))


class RbV010Sposob(Info):
    __tablename__ = u'rb_V010_Sposob'

    idsp = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    spname = Column(String(255))


class RbV012Ishod(Info):
    __tablename__ = u'rb_V012_Ishod'

    idiz = Column(BigInteger, primary_key=True)
    datebeg = Column(Date)
    dateend = Column(Date)
    iduslov = Column(BigInteger)
    izname = Column(String(255))


class Rdfirstname(Info):
    __tablename__ = u'rdFirstName'
    __table_args__ = (
        Index(u'sex', u'sex', u'name'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, index=True)
    sex = Column(Integer, nullable=False)


class Rdpolis(Info):
    __tablename__ = u'rdPOLIS_S'

    id = Column(Integer, primary_key=True)
    CODE = Column(String(10), nullable=False, index=True)
    PAYER = Column(String(5), nullable=False)
    TYPEINS = Column(String(1), nullable=False)


class Rdpatrname(Info):
    __tablename__ = u'rdPatrName'
    __table_args__ = (
        Index(u'sex', u'sex', u'name'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, index=True)
    sex = Column(Integer, nullable=False)


class Rlsactmatter(Info):
    __tablename__ = u'rlsActMatters'
    __table_args__ = (
        Index(u'name_localName', u'name', u'localName'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    localName = Column(String(255))


class Rlsbalanceofgood(Info):
    __tablename__ = u'rlsBalanceOfGoods'

    id = Column(Integer, primary_key=True)
    rlsNomen_id = Column(ForeignKey('rlsNomen.id'), nullable=False, index=True)
    value = Column(Float(asdecimal=True), nullable=False)
    bestBefore = Column(Date, nullable=False)
    disabled = Column(Integer, nullable=False, server_default=u"'0'")
    updateDateTime = Column(DateTime)
    storage_id = Column(ForeignKey('rbStorage.id'), index=True)

    rlsNomen = relationship(u'Rlsnoman')
    storage = relationship(u'Rbstorage')


class Rlsfilling(Info):
    __tablename__ = u'rlsFilling'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)


class Rlsform(Info):
    __tablename__ = u'rlsForm'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)


class Rlsnoman(Info):
    __tablename__ = u'rlsNomen'

    id = Column(Integer, primary_key=True)
    actMatters_id = Column(ForeignKey('rlsActMatters.id'), index=True)
    tradeName_id = Column(ForeignKey('rlsTradeName.id'), nullable=False, index=True)
    form_id = Column(ForeignKey('rlsForm.id'), index=True)
    packing_id = Column(ForeignKey('rlsPacking.id'), index=True)
    filling_id = Column(ForeignKey('rlsFilling.id'), index=True)
    unit_id = Column(ForeignKey('rbUnit.id'), index=True)
    dosageValue = Column(String(128))
    dosageUnit_id = Column(ForeignKey('rbUnit.id'), index=True)
    drugLifetime = Column(Integer)
    regDate = Column(Date)
    annDate = Column(Date)

    actMatters = relationship(u'Rlsactmatter')
    dosageUnit = relationship(u'Rbunit', primaryjoin='Rlsnoman.dosageUnit_id == Rbunit.id')
    filling = relationship(u'Rlsfilling')
    form = relationship(u'Rlsform')
    packing = relationship(u'Rlspacking')
    tradeName = relationship(u'Rlstradename')
    unit = relationship(u'Rbunit', primaryjoin='Rlsnoman.unit_id == Rbunit.id')


class Rlspacking(Info):
    __tablename__ = u'rlsPacking'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)


class Rlspharmgroup(Info):
    __tablename__ = u'rlsPharmGroup'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    code = Column(String(8))
    name = Column(String(128))
    path = Column(String(128))
    pathx = Column(String(128))
    nameRaw = Column(String(128), index=True)


class Rlspharmgrouptocode(Info):
    __tablename__ = u'rlsPharmGroupToCode'

    rlsPharmGroup_id = Column(Integer, primary_key=True, nullable=False, server_default=u"'0'")
    code = Column(Integer, primary_key=True, nullable=False, index=True, server_default=u"'0'")


class Rlstradename(Info):
    __tablename__ = u'rlsTradeName'
    __table_args__ = (
        Index(u'name_localName', u'name', u'localName'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    localName = Column(String(255))


class Trfufinalvolume(Info):
    __tablename__ = u'trfuFinalVolume'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    time = Column(Float(asdecimal=True))
    anticoagulantVolume = Column(Float(asdecimal=True))
    inletVolume = Column(Float(asdecimal=True))
    plasmaVolume = Column(Float(asdecimal=True))
    collectVolume = Column(Float(asdecimal=True))
    anticoagulantInCollect = Column(Float(asdecimal=True))
    anticoagulantInPlasma = Column(Float(asdecimal=True))

    action = relationship(u'Action')

    def __getitem__(self, name):
        columns = {'time': self.time,
                   'anticoagulantVolume': self.anticoagulantVolume,
                   'inletVolume': self.inletVolume,
                   'plasmaVolume': self.plasmaVolume,
                   'collectVolume': self.collectVolume,
                   'anticoagulantInCollect': self.anticoagulantInCollect,
                   'anticoagulantInPlasma': self.anticoagulantInPlasma}
        return columns[name]


class Trfulaboratorymeasure(Info):
    __tablename__ = u'trfuLaboratoryMeasure'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    trfu_lab_measure_id = Column(ForeignKey('rbTrfuLaboratoryMeasureTypes.id'), index=True)
    time = Column(Float(asdecimal=True))
    beforeOperation = Column(String(255))
    duringOperation = Column(String(255))
    inProduct = Column(String(255))
    afterOperation = Column(String(255))

    action = relationship(u'Action')
    trfu_lab_measure = relationship(u'Rbtrfulaboratorymeasuretype')

    def __getitem__(self, name):
        columns = {'trfu_lab_measure_id': self.trfu_lab_measure,
                   'time': self.time,
                   'beforeOperation': self.beforeOperation,
                   'duringOperation': self.duringOperation,
                   'inProduct': self.inProduct,
                   'afterOperation': self.afterOperation}
        return columns[name]


class Trfuorderissueresult(Info):
    __tablename__ = u'trfuOrderIssueResult'

    id = Column(Integer, primary_key=True)
    action_id = Column(ForeignKey('Action.id'), nullable=False, index=True)
    trfu_blood_comp = Column(Integer)
    comp_number = Column(String(40))
    comp_type_id = Column(ForeignKey('rbTrfuBloodComponentType.id'), index=True)
    blood_type_id = Column(ForeignKey('rbBloodType.id'), index=True)
    volume = Column(Integer)
    dose_count = Column(Float(asdecimal=True))
    trfu_donor_id = Column(Integer)
    stickerUrl = Column(String(2083))

    action = relationship(u'Action', backref="trfuOrderIssueResult")
    blood_type = relationship(u'Rbbloodtype')
    comp_type = relationship(u'Rbtrfubloodcomponenttype')

    def __getitem__(self, name):
        columns = {'trfu_blood_comp': self.trfu_blood_comp,
                   'comp_number': self.comp_number,
                   'comp_type_id': self.comp_type,
                   'blood_type_id': self.blood_type,
                   'volume': self.volume,
                   'dose_count': self.dose_count,
                   'trfu_donor_id': self.trfu_donor_id}
        return columns[name]


class v_Client_Quoting(Info):
    __tablename__ = u'vClient_Quoting'

    quotaId = Column(u'id', Integer, primary_key=True)
    createDatetime = Column(u'createDatetime', DateTime)
    createPerson_id = Column(u'createPerson_id', Integer)
    modifyDatetime = Column(u'modifyDatetime', DateTime)
    modifyPerson_id = Column(u'modifyPerson_id', Integer)
    deleted = Column(u'deleted', Integer, server_default=u"'0'")
    clientId = Column(u'master_id', Integer, ForeignKey("Client.id"))
    identifier = Column(u'identifier', String(16))
    quotaTicket = Column(u'quotaTicket', String(20))
    quotaType_id = Column(u'quotaType_id', Integer, ForeignKey("QuotaType.id"))
    stage = Column(u'stage', Integer)
    directionDate = Column(u'directionDate', DateTime)
    freeInput = Column(u'freeInput', String(128))
    org_id = Column(u'org_id', Integer, ForeignKey("Organisation.id"))
    amount = Column(u'amount', Integer, server_default=u"'0'")
    MKB = Column(u'MKB', String(8))
    status = Column(u'status', Integer, server_default=u"'0'")
    request = Column(u'request', Integer, server_default=u"'0'")
    statment = Column(u'statment', String(255))
    dateRegistration = Column(u'dateRegistration', DateTime)
    dateEnd = Column(u'dateEnd', DateTime)
    orgStructure_id = Column(u'orgStructure_id', Integer, ForeignKey("OrgStructure.id"))
    regionCode = Column(u'regionCode', String(13))
    pacientModel_id = Column(u'pacientModel_id', Integer, ForeignKey("rbPacientModel.id"))
    treatment_id = Column(u'treatment_id', Integer, ForeignKey("rbTreatment.id"))
    event_id = Column(u'event_id', Integer, ForeignKey("Event.id"))
    prevTalon_event_id = Column(u'prevTalon_event_id', Integer)

    quotaType = relationship(u"QuotaType")
    organisation = relationship(u"Organisation")
    orgstructure = relationship(u"Orgstructure")
    pacientModel = relationship(u"Rbpacientmodel")
    treatment = relationship(u"Rbtreatment")


class v_Nomen(Info):
    __tablename__ = u'vNomen'

    id = Column(u'id', Integer, primary_key=True)
    tradeName = Column(u'tradeName', String(255))
    tradeLocalName = Column(u'tradeLocalName', String(255))
    tradeName_id = Column(u'tradeName_id', Integer)
    actMattersName = Column(u'actMattersName', String(255))
    actMattersLocalName = Column(u'actMattersLocalName', String(255))
    actMatters_id = Column(u'actMatters_id', Integer)
    form = Column(u'form', String(128))
    packing = Column(u'packing', String(128))
    filling = Column(u'filling', String(128))
    unit_id = Column(u'unit_id', Integer)
    unitCode = Column(u'unitCode', String(256))
    unitName = Column(u'unitName', String(256))
    dosageValue = Column(u'dosageValue', String(128))
    dosageUnit_id = Column(u'dosageUnit_id', Integer)
    dosageUnitCode = Column(u'dosageUnitCode', String(256))
    dosageUnitName = Column(u'dosageUnitName', String(256))
    regDate = Column(u'regDate', Date)
    annDate = Column(u'annDate', Date)
    drugLifetime = Column(u'drugLifetime', Integer)

    def __unicode__(self):
        return ', '.join(unicode(field) for field in (self.tradeName, self.form, self.dosageValue, self.filling))


class Rbprinttemplatemeta(Info):
    __tablename__ = 'rbPrintTemplateMeta'
    __table_args__ = (
        Index('template_id_name', 'template_id', 'name'),
    )

    id = Column(Integer, primary_key=True)
    template_id = Column(ForeignKey('rbPrintTemplate.id'), nullable=False, index=True)
    type = Column(Enum(
        u'Integer', u'Float', u'String', u'Boolean', u'Date', u'Time',
        u'List', u'Multilist',
        u'RefBook', u'Organisation', u'OrgStructure', u'Person', u'Service', u'SpecialVariable'
    ), nullable=False)
    name = Column(String(128), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    arguments = Column(String)
    defaultValue = Column(Text)

    template = relationship(u'Rbprinttemplate')

    def __json__(self):
        import json
        if self.arguments:
            try:
                args = json.loads(self.arguments)
            except ValueError:
                args = []
        else:
            args = []
        if self.defaultValue:
            try:
                default = json.loads(self.defaultValue)
            except ValueError:
                default = None
        else:
            default = None
        return {
            'name': self.name,
            'type': self.type,
            'title': self.title,
            'descr': self.description,
            'arguments': args,
            'default': default,
        }
