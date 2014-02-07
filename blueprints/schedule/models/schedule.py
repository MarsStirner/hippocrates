# -*- coding: utf-8 -*-
from application.database import db


class Client(db.Model):
    __tablename__ = 'Client'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName', u'birthDate', u'id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    lastName = db.Column(db.Unicode(30), nullable=False)
    firstName = db.Column(db.Unicode(30), nullable=False)
    patrName = db.Column(db.Unicode(30), nullable=False)
    birthDate = db.Column(db.Date, nullable=False, index=True)
    sexCode = db.Column("sex", db.Integer, nullable=False)
    SNILS = db.Column(db.String(11), nullable=False, index=True)
    bloodType_id = db.Column(db.ForeignKey('rbBloodType.id'), index=True)
    bloodDate = db.Column(db.Date)
    bloodNotes = db.Column(db.String, nullable=False)
    growth = db.Column(db.String(16), nullable=False)
    weight = db.Column(db.String(16), nullable=False)
    notes = db.Column(db.String, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    birthPlace = db.Column(db.String(128), nullable=False, server_default=u"''")
    embryonalPeriodWeek = db.Column(db.String(16), nullable=False, server_default=u"''")
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")

    contacts = db.relationship('ClientContact')
    documentsAll = db.relationship('ClientDocument')
    policies = db.relationship('ClientPolicy')


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
        # TODO: order by db.Date code?
        for policy in self.policies:
            if not policy.policyType or u"ОМС" in policy.policyType.name:
                return policy

    @property
    def voluntaryPolicy(self):
        # TODO: order by db.Date code?
        for policy in self.policies:
            if policy.policyType and policy.policyType.name.startswith(u"ДМС"):
                return policy
    @property
    def policy(self):
        return self.compulsoryPolicy

    @property
    def policyDMS(self):
        return self.voluntaryPolicy


class ClientContact(db.Model):
    __tablename__ = 'ClientContact'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    contactType_id = db.Column(db.Integer, db.ForeignKey('rbContactType.id'), nullable=False, index=True)
    contact = db.Column(db.String(32), nullable=False)
    notes = db.Column(db.Unicode(64), nullable=False)
    version = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')
    contactType = db.relationship(u'rbContactType')

    @property
    def name(self):
        return self.contactType.names


class ClientDocument(db.Model):
    __tablename__ = 'ClientDocument'
    __table_args__ = (
        db.Index(u'Ser_Numb', u'serial', u'number'),
    )

    documentId = db.Column("id", db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    clientId = db.Column("client_id", db.ForeignKey('Client.id'), nullable=False, index=True)
    documentType_id = db.Column(db.Integer, db.ForeignKey('rbDocumentType.id'), nullable=False, index=True)
    serial = db.Column(db.String(8), nullable=False)
    number = db.Column(db.String(16), nullable=False)
    date = db.Column(db.Date, nullable=False)
    origin = db.Column(db.String(256), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    endDate = db.Column(db.Date)

    client = db.relationship(u'Client')
    documentType = db.relationship(u'rbDocumentType')

    @property
    def documentTypeCode(self):
        return self.documentType.regionalCode

    def __unicode__(self):
        return (' '.join([self.documentType, self.serial, self.number])).strip()


class rbDocumentTypeGroup(db.Model):
    __tablename__ = 'rbDocumentTypeGroup'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class rbFinance(db.Model):
    __tablename__ = 'rbFinance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class rbBloodType(db.Model):
    __tablename__ = 'rbBloodType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class ClientPolicy(db.Model):
    __tablename__ = 'ClientPolicy'
    __table_args__ = (
        db.Index(u'Serial_Num', u'serial', u'number'),
        db.Index(u'client_insurer', u'client_id', u'insurer_id')
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    clientId = db.Column("client_id", db.ForeignKey('Client.id'), nullable=False)
    insurer_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)
    policyType_id = db.Column(db.Integer, db.ForeignKey('rbPolicyType.id'), index=True)
    serial = db.Column(db.String(16), nullable=False)
    number = db.Column(db.String(16), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)
    name = db.Column(db.Unicode(64), nullable=False, server_default=u"''")
    note = db.Column(db.String(200), nullable=False, server_default=u"''")
    version = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')
    insurer = db.relationship(u'Organisation')
    policyType = db.relationship(u'rbPolicyType')

    def __unicode__(self):
        return (' '.join([self.policyType, db.Unicode(self.insurer), self.serial, self.number])).strip()


class Organisation(db.Model):
    __tablename__ = 'Organisation'
    __table_args__ = (
        db.Index(u'shortName', u'shortName', u'INN', u'OGRN'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    fullName = db.Column(db.String(255), nullable=False)
    shortName = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False, index=True)
    net_id = db.Column(db.Integer, db.ForeignKey('rbNet.id'), index=True)
    infisCode = db.Column(db.String(12), nullable=False, index=True)
    obsoleteInfisCode = db.Column(db.String(60), nullable=False)
    OKVED = db.Column(db.String(64), nullable=False, index=True)
    INN = db.Column(db.String(15), nullable=False, index=True)
    KPP = db.Column(db.String(15), nullable=False)
    OGRN = db.Column(db.String(15), nullable=False, index=True)
    OKATO = db.Column(db.String(15), nullable=False)
    OKPF_code = db.Column(db.String(4), nullable=False)
    OKPF_id = db.Column(db.Integer, db.ForeignKey('rbOKPF.id'), index=True)
    OKFS_code = db.Column(db.Integer, nullable=False)
    OKFS_id = db.Column(db.Integer, db.ForeignKey('rbOKFS.id'), index=True)
    OKPO = db.Column(db.String(15), nullable=False)
    FSS = db.Column(db.String(10), nullable=False)
    region = db.Column(db.String(40), nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    chief = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    accountant = db.Column(db.String(64), nullable=False)
    isInsurer = db.Column(db.Integer, nullable=False, index=True)
    compulsoryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    voluntaryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    area = db.Column(db.String(13), nullable=False)
    isHospital = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    notes = db.Column(db.String, nullable=False)
    head_id = db.Column(db.Integer, index=True)
    miacCode = db.Column(db.String(10), nullable=False)
    isOrganisation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")


    net = db.relationship('rbNet')
    OKPF = db.relationship('rbOKPF')
    OKFS = db.relationship('rbOKFS')


class OrgStructure(db.Model):
    __tablename__ = 'OrgStructure'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    code = db.Column(db.Unicode(255), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), index=True)
    type = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    net_id = db.Column(db.Integer, db.ForeignKey('rbNet.id'), index=True)
    isArea = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hasHospitalBeds = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hasStocks = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    infisCode = db.Column(db.String(16), nullable=False)
    infisInternalCode = db.Column(db.String(16), nullable=False)
    infisDepTypeCode = db.Column(db.String(16), nullable=False)
    infisTariffCode = db.Column(db.String(16), nullable=False)
    availableForExternal = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    Address = db.Column(db.String(255), nullable=False)
    inheritEventTypes = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    inheritActionTypes = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    inheritGaps = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")
    show = db.Column(db.Integer, nullable=False, server_default=u"'1'")

    parent = db.relationship('OrgStructure', remote_side=[id])
    organisation = db.relationship('Organisation')
    Net = db.relationship('rbNet')

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


class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(12), nullable=False)
    federalCode = db.Column(db.Unicode(255), nullable=False)
    regionalCode = db.Column(db.String(16), nullable=False)
    lastName = db.Column(db.Unicode(30), nullable=False)
    firstName = db.Column(db.Unicode(30), nullable=False)
    patrName = db.Column(db.Unicode(30), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('rbPost.id'), index=True)
    speciality_id = db.Column(db.Integer, db.ForeignKey('rbSpeciality.id'), index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), index=True)
    office = db.Column(db.Unicode(8), nullable=False)
    office2 = db.Column(db.Unicode(8), nullable=False)
    tariffCategory_id = db.Column(db.Integer, db.ForeignKey('rbTariffCategory.id'), index=True)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    retireDate = db.Column(db.Date, index=True)
    ambPlan = db.Column(db.SmallInteger, nullable=False)
    ambPlan2 = db.Column(db.SmallInteger, nullable=False)
    ambNorm = db.Column(db.SmallInteger, nullable=False)
    homPlan = db.Column(db.SmallInteger, nullable=False)
    homPlan2 = db.Column(db.SmallInteger, nullable=False)
    homNorm = db.Column(db.SmallInteger, nullable=False)
    expPlan = db.Column(db.SmallInteger, nullable=False)
    expNorm = db.Column(db.SmallInteger, nullable=False)
    login = db.Column(db.Unicode(32), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    userProfile_id = db.Column(db.Integer, index=True)
    retired = db.Column(db.Integer, nullable=False)
    birthDate = db.Column(db.Date, nullable=False)
    birthPlace = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    SNILS = db.Column(db.String(11), nullable=False)
    INN = db.Column(db.String(15), nullable=False)
    availableForExternal = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    primaryQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'50'")
    ownQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'25'")
    consultancyQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'25'")
    externalQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'10'")
    lastAccessibleTimelineDate = db.Column(db.Date)
    timelineAccessibleDays = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    typeTimeLinePerson = db.Column(db.Integer, nullable=False)
    maxOverQueue = db.Column(db.Integer, server_default=u"'0'")
    maxCito = db.Column(db.Integer, server_default=u"'0'")
    quotUnit = db.Column(db.Integer, server_default=u"'0'")
    academicdegree_id = db.Column(db.Integer, db.ForeignKey('rbAcademicDegree.id'))
    academicTitle_id = db.Column(db.Integer, db.ForeignKey('rbAcademicTitle.id'))

    post = db.relationship('rbPost')
    speciality = db.relationship('rbSpeciality')
    organisation = db.relationship('Organisation')
    OrgStructure = db.relationship('OrgStructure')
    academicDegree = db.relationship('rbAcademicDegree')
    academicTitle = db.relationship('rbAcademicTitle')
    tariffCategory = db.relationship('rbTariffCategory')


class rbAcademicDegree(db.Model):
    __tablename__ = 'rbAcademicDegree'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)


class rbAcademicTitle(db.Model):
    __tablename__ = 'rbAcademicTitle'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)


class rbContactType(db.Model):
    __tablename__ = 'rbContactType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    

class rbDocumentType(db.Model):
    __tablename__ = 'rbDocumentType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(64), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('rbDocumentTypeGroup.id'), nullable=False, index=True)
    serial_format = db.Column(db.Integer, nullable=False)
    number_format = db.Column(db.Integer, nullable=False)
    federalCode = db.Column(db.String(16), nullable=False)
    socCode = db.Column(db.String(8), nullable=False, index=True)
    TFOMSCode = db.Column(db.Integer)

    group = db.relationship(u'rbDocumentTypeGroup')


class rbNet(db.Model):
    __tablename__ = 'rbNet'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)


class rbOKFS(db.Model):
    __tablename__ = 'rbOKFS'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    ownership = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbOKPF(db.Model):
    __tablename__ = 'rbOKPF'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)


class rbPolicyType(db.Model):
    __tablename__ = 'rbPolicyType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.Unicode(256), nullable=False, index=True)
    TFOMSCode = db.Column(db.String(8))


class rbPost(db.Model):
    __tablename__ = 'rbPost'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(8), nullable=False)
    key = db.Column(db.String(6), nullable=False, index=True)
    high = db.Column(db.String(6), nullable=False)
    flatCode = db.Column(db.String(65), nullable=False)


class rbReasonOfAbsence(db.Model):
    __tablename__ = 'rbReasonOfAbsence'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)


class rbSpeciality(db.Model):
    __tablename__ = 'rbSpeciality'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    OKSOName = db.Column(db.Unicode(60), nullable=False)
    OKSOCode = db.Column(db.String(8), nullable=False)
    service_id = db.Column(db.Integer, index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    mkbFilter = db.Column(db.String(32), nullable=False)
    regionalCode = db.Column(db.String(16), nullable=False)
    quotingEnabled = db.Column(db.Integer, server_default=u"'0'")


class rbTariffCategory(db.Model):
    __tablename__ = 'rbTariffCategory'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)