# -*- coding: utf-8 -*-
from application.database import db
from sqlalchemy import BigInteger, Column, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, SmallInteger, \
    String, Table, Text, Time, Unicode
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Info(object):
    u"""Базовый класс для представления объектов при передаче в шаблоны печати"""

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
    def __unicode__(self):
        return self.name


class Client(Base, Info):
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
    birthDate = Column(Date, nullable=False, index=True)
    sexCode = Column("sex", Integer, nullable=False)
    SNILS = Column(String(11), nullable=False, index=True)
    bloodType_id = Column(ForeignKey('rbBloodType.id'), index=True)
    bloodDate = Column(Date)
    bloodNotes = Column(String, nullable=False)
    growth = Column(String(16), nullable=False)
    weight = Column(String(16), nullable=False)
    notes = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    birthPlace = Column(String(128), nullable=False, server_default=u"''")
    embryonalPeriodWeek = Column(String(16), nullable=False, server_default=u"''")
    uuid_id = Column(Integer, nullable=False, index=True, server_default=u"'0'")


    contacts = relationship(u'Clientcontact')
    documentsAll = relationship(u'Clientdocument')
    policies = relationship(u'Clientpolicy')


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
        if self.SNILS:
            s = self.SNILS+' '*14
            return s[0:3]+'-'+s[3:6]+'-'+s[6:9]+' '+s[9:11]
        else:
            return u''

    @property
    def document(self):
        # TODO: отстортировать по дате
        for document in self.documents:
            if document.deleted == 0 and document.documentType.group.code == '1':
                return document

    @property
    def phones(self):
        contacts = [(contact.name, contact.contact, contact.notes) for contact in self.contacts if contact.deleted == 0]
        return ', '.join([(phone[0]+': '+phone[1]+' ('+phone[2]+')') if phone[2] else (phone[0]+': '+phone[1])
                          for phone in contacts])

    @property
    def compulsoryPolicy(self):
        # TODO: order by date code?
        for policy in self.policies:
            if not policy.policyType or u"ОМС" in policy.policyType.name:
                return policy

    @property
    def voluntaryPolicy(self):
        # TODO: order by date code?
        for policy in self.policies:
            if policy.policyType and policy.policyType.name.startswith(u"ДМС"):
                return policy
    @property
    def policy(self):
        return self.compulsoryPolicy

    @property
    def policyDMS(self):
        return self.voluntaryPolicy

    @property
    def fullName(self):
        return formatNameInt(self.lastName, self.firstName, self.patrName)

    @property
    def shortName(self):
        return formatShortNameInt(self.lastName, self.firstName, self.patrName)

    def __unicode__(self):
        return self.formatShortNameInt(self.lastName, self.firstName, self.patrName)


class Clientcontact(Base, Info):
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
        return self.contactType.names


class Clientdocument(Base):
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
        return (' '.join([self.documentType, self.serial, self.number])).strip()


class Clientpolicy(Base, Info):
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

    def __unicode__(self):
        return (' '.join([self.policyType, unicode(self.insurer), self.serial, self.number])).strip()


class Organisation(Base, Info):
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
    fullName = Column(String(255), nullable=False)
    shortName = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False, index=True)
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
    region = Column(String(40), nullable=False)
    Address = Column(String(255), nullable=False)
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


class Orgstructure(Base, Info):
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

    parent = relationship(u'Orgstructure', remote_side=[id])
    organisation = relationship(u'Organisation')
    Net = relationship(u'Rbnet')

    def getNet(self):
        if self.Net is None:
            if self.parent:
                self.Net = self.parent.getNet()
            elif self.organisation:
                self.Net = self.organisation.net
        return self.Net

    def get_org_structure_full_name(self, org_structure_id):
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
        return self.get_org_structure_full_name(self.id)

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


class Person(Base):
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
        result = formatShortNameInt(self._lastName, self._firstName, self._patrName)
        if self.speciality:
            result += ', '+self.speciality.name
        return unicode(result)


class Rbacademicdegree(Base, RBInfo):
    __tablename__ = u'rbAcademicDegree'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(Unicode(64), nullable=False)


class Rbacademictitle(Base, RBInfo):
    __tablename__ = u'rbAcademicTitle'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbcontacttype(Base, RBInfo):
    __tablename__ = u'rbContactType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    

class Rbdocumenttype(Base, RBInfo):
    __tablename__ = u'rbDocumentType'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    regionalCode = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey('rbDocumentTypeGroup.id'), nullable=False, index=True)
    serial_format = Column(Integer, nullable=False)
    number_format = Column(Integer, nullable=False)
    federalCode = Column(String(16), nullable=False)
    socCode = Column(String(8), nullable=False, index=True)
    TFOMSCode = Column(Integer)

    group = relationship(u'Rbdocumenttypegroup')


class Rbnet(Base, RBInfo):
    __tablename__ = u'rbNet'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    sex = Column(Integer, nullable=False, server_default=u"'0'")
    age = Column(String(9), nullable=False)
    age_bu = Column(Integer)
    age_bc = Column(SmallInteger)
    age_eu = Column(Integer)
    age_ec = Column(SmallInteger)


class Rbokfs(Base, RBInfo):
    __tablename__ = u'rbOKFS'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    ownership = Column(Integer, nullable=False, server_default=u"'0'")


class Rbokpf(Base, RBInfo):
    __tablename__ = u'rbOKPF'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


class Rbpolicytype(Base, RBInfo):
    __tablename__ = u'rbPolicyType'

    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True)
    name = Column(Unicode(256), nullable=False, index=True)
    TFOMSCode = Column(String(8))


class Rbpost(Base, RBInfo):
    __tablename__ = u'rbPost'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)
    regionalCode = Column(String(8), nullable=False)
    key = Column(String(6), nullable=False, index=True)
    high = Column(String(6), nullable=False)
    flatCode = Column(String(65), nullable=False)


class Rbreasonofabsence(Base, RBInfo):
    __tablename__ = u'rbReasonOfAbsence'

    id = Column(Integer, primary_key=True)
    code = Column(Unicode(8), nullable=False, index=True)
    name = Column(Unicode(64), nullable=False, index=True)


class Rbspeciality(Base, RBInfo):
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


class Rbtariffcategory(Base, RBInfo):
    __tablename__ = u'rbTariffCategory'

    id = Column(Integer, primary_key=True)
    code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)


def trim(s):
    return u' '.join(unicode(s).split())


def formatShortNameInt(lastName, firstName, patrName):
    return trim(lastName + ' ' + ((firstName[:1]+'.') if firstName else '') + ((patrName[:1]+'.') if patrName else ''))


def formatNameInt(lastName, firstName, patrName):
    return trim(lastName+' '+firstName+' '+patrName)