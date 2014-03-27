# -*- coding: utf-8 -*
import datetime
from application.database import db
from application.lib.agesex import AgeSex
from application.models.kladr_models import Kladr, Street
# from application.models.actions import Action


class Address(db.Model):
    __tablename__ = u'Address'
    __table_args__ = (
        db.Index(u'house_id', u'house_id', u'flat'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    house_id = db.Column(db.Integer, db.ForeignKey('AddressHouse.id'), nullable=False)
    flat = db.Column(db.String(6), nullable=False)

    house = db.relationship(u'AddressHouse')

    @property
    def KLADRCode(self):
        return self.house.KLADRCode

    @property
    def KLADRStreetCode(self):
        return self.house.KLADRStreetCode

    @property
    def city(self):
        if self.KLADRCode:
            record = Kladr.query.filter(Kladr.CODE == self.KLADRCode).first()
            name = [" ".join([record.NAME, record.SOCR])]
            parent = record.parent
            while parent:
                record = Kladr.query.filter(Kladr.CODE == parent.ljust(13, "0")).first()
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
        if self.KLADRStreetCode:
            record = Street.query.filter(Street.CODE == self.KLADRStreetCode).first()
            return record.NAME + " " + record.SOCR
        else:
            return ''

    def __unicode__(self):
        return self.text

    def __int__(self):
        return self.id


class AddressAreaItem(db.Model):
    __tablename__ = u'AddressAreaItem'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    LPU_id = db.Column(db.Integer, nullable=False, index=True)
    struct_id = db.Column(db.Integer, nullable=False, index=True)
    house_id = db.Column(db.Integer, nullable=False, index=True)
    flatRange = db.Column(db.Integer, nullable=False)
    begFlat = db.Column(db.Integer, nullable=False)
    endFlat = db.Column(db.Integer, nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)

    def __int__(self):
        return self.id


class AddressHouse(db.Model):
    __tablename__ = u'AddressHouse'
    __table_args__ = (
        db.Index(u'KLADRCode', u'KLADRCode', u'KLADRStreetCode', u'number', u'corpus'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    KLADRCode = db.Column(db.String(13), nullable=False)
    KLADRStreetCode = db.Column(db.String(17), nullable=False)
    number = db.Column(db.String(8), nullable=False)
    corpus = db.Column(db.String(8), nullable=False)

    def __int__(self):
        return self.id


class Bloodhistory(db.Model):
    __tablename__ = u'BloodHistory'

    id = db.Column(db.Integer, primary_key=True)
    bloodDate = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    bloodType_id = db.Column(db.Integer, db.ForeignKey('rbBloodType.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), nullable=False)

    bloodType = db.relationship("rbBloodType")
    person = db.relationship("Person")

    def __int__(self):
        return self.id


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

    contacts = db.relationship('ClientContact', primaryjoin='and_(ClientContact.client_id==Client.id,'
                                                            'ClientContact.deleted == 0)', lazy='dynamic')
    documentsAll = db.relationship(u'ClientDocument', primaryjoin='and_(ClientDocument.clientId==Client.id,'
                                                                  'ClientDocument.deleted == 0)',
                                   order_by="desc(ClientDocument.documentId)")
    policies = db.relationship(u'ClientPolicy', primaryjoin='and_(ClientPolicy.clientId==Client.id,'
                                                            'ClientPolicy.deleted == 0)',
                               order_by="desc(ClientPolicy.id)")
    reg_address = db.relationship(u'ClientAddress',
                                    primaryjoin="and_(Client.id==ClientAddress.client_id, ClientAddress.type==0)",
                                    order_by="desc(ClientAddress.id)", uselist=False)
    loc_address = db.relationship(u'ClientAddress',
                                    primaryjoin="and_(Client.id==ClientAddress.client_id, ClientAddress.type==1)",
                                    order_by="desc(ClientAddress.id)", uselist=False)
    socStatuses = db.relationship(u'ClientSocStatus',
                                  primaryjoin='and_(ClientSocStatus.deleted == 0,ClientSocStatus.client_id==Client.id,'
                                  'or_(ClientSocStatus.endDate == None, ClientSocStatus.endDate>={0}))'.format(datetime.date.today()))
    intolerances = db.relationship(u'ClientIntoleranceMedicament',
                                   primaryjoin='and_(ClientIntoleranceMedicament.client_id==Client.id,'
                                               'ClientIntoleranceMedicament.deleted == 0)')
    identifications = db.relationship(u'ClientIdentification',
                                      primaryjoin='and_(ClientIdentification.client_id==Client.id,'
                                      'ClientIdentification.deleted == 0)')
    allergies = db.relationship(u'ClientAllergy', primaryjoin='and_(ClientAllergy.client_id==Client.id,'
                                                              'ClientAllergy.deleted == 0)')
    blood_history = db.relationship(u'Bloodhistory')
    direct_relations = db.relationship(u'DirectClientRelation', foreign_keys='ClientRelation.client_id')
    reversed_relations = db.relationship(u'ReversedClientRelation', foreign_keys='ClientRelation.relative_id')
    events = db.relationship(
        u'Event', lazy='dynamic', order_by='desc(Event.createDatetime)',
        primaryjoin='and_(Event.deleted == 0, Event.client_id == Client.id)')
    appointments = db.relationship(
        u'ScheduleClientTicket', lazy='dynamic', #order_by='desc(ScheduleTicket.begDateTime)',
        primaryjoin='and_(ScheduleClientTicket.deleted == 0, ScheduleClientTicket.client_id == Client.id)',
        innerjoin=True
    )

    @property
    def nameText(self):
        return u' '.join((u'%s %s %s' % (self.lastName, self.firstName, self.patrName)).split())

    @property
    def shortNameText(self):
        words = self.firstName.split() + self.patrName.split()
        initials = ['%s.' % word[0].upper() for word in words if word]
        return u'%s %s' % (self.lastName, u' '.join(initials))

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
    def formatted_SNILS(self):
        if self.SNILS:
            s = self.SNILS + ' ' * 14
            return u'%s-%s-%s %s' % (s[0:3], s[3:6], s[6:9], s[9:11])
        else:
            return u''

    @property
    def document(self):
        try:
            return self.documents.\
                filter(ClientDocument.deleted == 0).\
                filter(rbDocumentTypeGroup.code == '1').\
                order_by(ClientDocument.date.desc()).first()
        except:
            return None

    @property
    def phones(self):
        contacts = [(contact.name, contact.contact, contact.notes) for contact in self.contacts]
        return ', '.join([
            (u'%s: %s (%s)' % (phone[0], phone[1], phone[2])) if phone[2]
            else (u'%s: %s' % (phone[0], phone[1]))
            for phone in contacts
        ])

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
    def relations(self):
        return self.reversed_relations + self.direct_relations

    @property
    def policy(self):
        return self.compulsoryPolicy

    @property
    def policyDMS(self):
        return self.voluntaryPolicy

    def __unicode__(self):
        return self.nameText

    def __int__(self):
        return self.id


class ClientAddress(db.Model):
    __tablename__ = u'ClientAddress'
    __table_args__ = (
        db.Index(u'address_id', u'address_id', u'type'),
        db.Index(u'client_id', u'client_id', u'type', u'address_id')
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('Address.id'))
    freeInput = db.Column(db.String(200), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    localityType = db.Column(db.Integer, nullable=False)

    address = db.relationship(u'Address')

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

    def __int__(self):
        return self.id


class ClientAllergy(db.Model):
    __tablename__ = u'ClientAllergy'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    name = db.Column("nameSubstance", db.Unicode(128), nullable=False)
    power = db.Column(db.Integer, nullable=False)
    createDate = db.Column(db.Date)
    notes = db.Column(db.String, nullable=False)
    version = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')

    def __unicode__(self):
        return self.name

    def __int__(self):
        return self.id


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
    contactType = db.relationship(u'rbContactType', lazy=False)

    @property
    def name(self):
        return self.contactType.name

    def __int__(self):
        return self.id


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

    client = db.relationship(u'Client', backref=db.backref('documents', lazy='dynamic'))
    documentType = db.relationship(u'rbDocumentType', lazy=False)

    @property
    def documentTypeCode(self):
        return self.documentType.regionalCode

    def __unicode__(self):
        return (' '.join([self.documentType.name, self.serial, self.number])).strip()

    def __json__(self):
        return {
            'id': self.documentId,
            'serial': self.serial,
            'number': self.number,
            'date': self.date,
            'origin': self.origin,
            'endDate': self.endDate,
            'document_type': self.documentType
        }

    def __int__(self):
        return self.id


class ClientIdentification(db.Model):
    __tablename__ = u'ClientIdentification'
    __table_args__ = (
        db.Index(u'accountingSystem_id', u'accountingSystem_id', u'identifier'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    accountingSystem_id = db.Column(db.Integer, db.ForeignKey('rbAccountingSystem.id'), nullable=False)
    identifier = db.Column(db.String(16), nullable=False)
    checkDate = db.Column(db.Date)
    version = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')
    accountingSystems = db.relationship(u'rbAccountingSystem', lazy=False)

    @property
    def code(self):
        return self.attachType.code

    @property
    def name(self):
        return self.attachType.name

    def __json__(self):
        return {
            'id': self.id,
            'accounting_system': self.accountingSystems,
            'identifier': self.identifier,
            'chechDate': self.checkDate,
        }

    def __int__(self):
        return self.id


class ClientIntoleranceMedicament(db.Model):
    __tablename__ = u'ClientIntoleranceMedicament'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    name = db.Column("nameMedicament", db.Unicode(128), nullable=False)
    power = db.Column(db.Integer, nullable=False)
    createDate = db.Column(db.Date)
    notes = db.Column(db.String, nullable=False)
    version = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')

    def __unicode__(self):
        return self.name

    def __int__(self):
        return self.id


class ClientRelation(db.Model):
    __tablename__ = u'ClientRelation'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    relativeType_id = db.Column(db.Integer, db.ForeignKey('rbRelationType.id'), index=True)
    relative_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)

    relativeType = db.relationship(u'rbRelationType', lazy=False)

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

    def __int__(self):
        return self.id


class DirectClientRelation(ClientRelation):

    other = db.relationship(u'Client', foreign_keys='ClientRelation.relative_id')

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


class ReversedClientRelation(ClientRelation):

    other = db.relationship(u'Client', foreign_keys='ClientRelation.client_id')

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


class ClientSocStatus(db.Model):
    __tablename__ = u'ClientSocStatus'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    socStatusClass_id = db.Column(db.ForeignKey('rbSocStatusClass.id'), index=True)
    socStatusType_id = db.Column(db.ForeignKey('rbSocStatusType.id'), nullable=False, index=True)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)
    document_id = db.Column(db.ForeignKey('ClientDocument.id'), index=True)
    version = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(256), nullable=False, server_default=u"''")
    benefitCategory_id = db.Column(db.Integer)

    client = db.relationship(u'Client')
    soc_status_class = db.relationship(u'rbSocStatusClass', lazy=False)
    socStatusType = db.relationship(u'rbSocStatusType', lazy=False)
    self_document = db.relationship(u'ClientDocument', lazy=False)

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
        documents = ClientDocument.query().filter(ClientDocument.clientId == self.client_id).\
            filter(ClientDocument.deleted == 0).all()
        documents = [document for document in documents if document.documentType and
                     document.documentType.group.code == "1"]
        return documents[-1]

    def __unicode__(self):
        return self.name

    def __int__(self):
        return self.id


class rbDocumentTypeGroup(db.Model):
    __tablename__ = 'rbDocumentTypeGroup'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbFinance(db.Model):
    __tablename__ = 'rbFinance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbBloodType(db.Model):
    __tablename__ = 'rbBloodType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


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
    note = db.Column(db.Unicode(200), nullable=False, server_default=u"''")
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    client = db.relationship(u'Client')
    insurer = db.relationship(u'Organisation', lazy=False)
    policyType = db.relationship(u'rbPolicyType', lazy=False)

    def __unicode__(self):
        return (' '.join([self.policyType.name, unicode(self.insurer), self.serial, self.number])).strip()

    def __int__(self):
        return self.id


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

    def __unicode__(self):
        return self.fullName

    def __json__(self):
        return {
            'id': self.id,
            'full_name': self.fullName,
            'short_name': self.shortName,
            'title': self.title,
            'net': self.net,
            'infis': self.infisCode,
        }

    def __int__(self):
        return self.id


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
        ids = {self.id}
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

    def __int__(self):
        return self.id


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

    @property
    def nameText(self):
        return u' '.join((u'%s %s %s' % (self.lastName, self.firstName, self.patrName)).split())

    @property
    def shortNameText(self):
        words = self.firstName.split() + self.patrName.split()
        initials = ['%s.' % word[0].upper() for word in words if word]
        return u'%s %s' % (self.lastName, u' '.join(initials))

    def __unicode__(self):
        return self.nameText

    def __json__(self):
        return {
            'id': self.id,
            'name': self.nameText,
            'code': self.code,
            'birth_date': self.birthDate,
            'speciality': self.speciality,
            'federal_code': self.federalCode,
            'regional_code': self.regionalCode,
            'post': self.post,
            'organisation': self.organisation,
            'org_structure': self.OrgStructure,
            'academic_degree': self.academicDegree,
            'academic_title': self.academicTitle,
        }

    def __int__(self):
        return self.id


class rbAcademicDegree(db.Model):
    __tablename__ = 'rbAcademicDegree'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAcademicTitle(db.Model):
    __tablename__ = 'rbAcademicTitle'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbAccountingSystem(db.Model):
    __tablename__ = u'rbAccountingSystem'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    isEditable = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showInClientInfo = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'is_editable': bool(self.isEditable),
            'show_in_client_info': bool(self.showInClientInfo),
        }

    def __int__(self):
        return self.id


class rbContactType(db.Model):
    __tablename__ = 'rbContactType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    
    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


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

    group = db.relationship(u'rbDocumentTypeGroup', lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'federal_code': self.federalCode,
            'soc_code': self.socCode,
            'TFOMS_code': self.TFOMSCode
        }

    def __int__(self):
        return self.id


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

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'restrictions': AgeSex(self),
        }

    def __int__(self):
        return self.id


class rbOKFS(db.Model):
    __tablename__ = 'rbOKFS'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    ownership = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'ownership': self.ownership,
        }

    def __int__(self):
        return self.id


class rbOKPF(db.Model):
    __tablename__ = 'rbOKPF'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbPolicyType(db.Model):
    __tablename__ = 'rbPolicyType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.Unicode(256), nullable=False, index=True)
    TFOMSCode = db.Column(db.String(8))

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'TFOMS_code': self.TFOMSCode,
        }

    def __int__(self):
        return self.id


class rbPost(db.Model):
    __tablename__ = 'rbPost'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(8), nullable=False)
    key = db.Column(db.String(6), nullable=False, index=True)
    high = db.Column(db.String(6), nullable=False)
    flatCode = db.Column(db.String(65), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'key': self.key,
            'high': self.high,
            'flat_code': self.flatCode,
        }

    def __int__(self):
        return self.id


class rbReasonOfAbsence(db.Model):
    __tablename__ = 'rbReasonOfAbsence'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbRelationType(db.Model):
    __tablename__ = u'rbRelationType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    leftName = db.Column(db.String(64), nullable=False)
    rightName = db.Column(db.String(64), nullable=False)
    isDirectGenetic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardGenetic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectRepresentative = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardRepresentative = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectEpidemic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardEpidemic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectDonation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardDonation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    leftSex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    rightSex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    regionalCode = db.Column(db.String(64), nullable=False)
    regionalReverseCode = db.Column(db.String(64), nullable=False)

    def __int__(self):
        return self.id


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

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'OKSO_name': self.OKSOName,
            'OKSO_code': self.OKSOCode,
            'MKB_filter': self.mkbFilter,
            'regional_code': self.regionalCode,
            'quoting_qnabled': bool(self.quotingEnabled),
        }

    def __int__(self):
        return self.id


class rbSocStatusClass(db.Model):
    __tablename__ = u'rbSocStatusClass'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.ForeignKey('rbSocStatusClass.id'), index=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    group = db.relationship(u'rbSocStatusClass', remote_side=[id])

    def __unicode__(self):
        return self.name

    def __int__(self):
        return self.id


rbSocStatusClassTypeAssoc = db.Table('rbSocStatusClassTypeAssoc', db.Model.metadata,
                                     db.Column('class_id', db.Integer, db.ForeignKey('rbSocStatusClass.id')),
                                     db.Column('type_id', db.Integer, db.ForeignKey('rbSocStatusType.id'))
                                     )


class rbSocStatusType(db.Model):
    __tablename__ = u'rbSocStatusType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(250), nullable=False, index=True)
    socCode = db.Column(db.String(8), nullable=False, index=True)
    TFOMSCode = db.Column(db.Integer)
    regionalCode = db.Column(db.String(8), nullable=False)

    classes = db.relationship(u'rbSocStatusClass', secondary=rbSocStatusClassTypeAssoc)

    def __int__(self):
        return self.id


class rbTariffCategory(db.Model):
    __tablename__ = 'rbTariffCategory'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbUFMS(db.Model):
    __tablename__ = u'rbUFMS'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50, u'utf8_bin'), nullable=False)
    name = db.Column(db.Unicode(256), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class Diagnosis(db.Model):
    __tablename__ = u'Diagnosis'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), index=True, nullable=False)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = db.Column(db.ForeignKey('rbDiseaseCharacter.id'), index=True)
    MKB = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    MKBEx = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    dispanser_id = db.Column(db.ForeignKey('rbDispanser.id'), index=True)
    traumaType_id = db.Column(db.ForeignKey('rbTraumaType.id'), index=True)
    setDate = db.Column(db.Date)
    endDate = db.Column(db.Date, nullable=False)
    mod_id = db.Column(db.ForeignKey('Diagnosis.id'), index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    # diagnosisName = db.Column(db.String(64), nullable=False)

    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])
    person = db.relationship('Person', foreign_keys=[person_id], lazy=False, innerjoin=True)
    client = db.relationship('Client')
    diagnosisType = db.relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = db.relationship('rbDiseaseCharacter', lazy=False)
    mkb = db.relationship('MKB', foreign_keys=[MKB])
    mkb_ex = db.relationship('MKB', foreign_keys=[MKB])
    dispanser = db.relationship('rbDispanser', lazy=False)
    mod = db.relationship('Diagnosis', remote_side=[id])
    traumaType = db.relationship('rbTraumaType', lazy=False)

    def __int__(self):
        return self.id


class Diagnostic(db.Model):
    __tablename__ = u'Diagnostic'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False, index=True)
    diagnosis_id = db.Column(db.ForeignKey('Diagnosis.id'), index=True)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = db.Column(db.ForeignKey('rbDiseaseCharacter.id'), index=True)
    stage_id = db.Column(db.ForeignKey('rbDiseaseStage.id'), index=True)
    phase_id = db.Column(db.ForeignKey('rbDiseasePhases.id'), index=True)
    dispanser_id = db.Column(db.ForeignKey('rbDispanser.id'), index=True)
    sanatorium = db.Column(db.Integer, nullable=False)
    hospital = db.Column(db.Integer, nullable=False)
    traumaType_id = db.Column(db.ForeignKey('rbTraumaType.id'), index=True)
    speciality_id = db.Column(db.Integer, nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    healthGroup_id = db.Column(db.ForeignKey('rbHealthGroup.id'), index=True)
    result_id = db.Column(db.ForeignKey('rbResult.id'), index=True)
    setDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime)
    notes = db.Column(db.Text, nullable=False)
    rbAcheResult_id = db.Column(db.ForeignKey('rbAcheResult.id'), index=True)
    version = db.Column(db.Integer, nullable=False)
    action_id = db.Column(db.Integer, index=True)

    rbAcheResult = db.relationship(u'rbAcheResult', innerjoin=True)
    result = db.relationship(u'rbResult', innerjoin=True)
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])
    person = db.relationship('Person', foreign_keys=[person_id])
    event = db.relationship('Event', innerjoin=True)
    diagnoses = db.relationship(
        'Diagnosis', innerjoin=True, lazy=False, uselist=True,
        primaryjoin='and_(Diagnostic.diagnosis_id == Diagnosis.id, Diagnosis.deleted == 0)'
    )
    diagnosis = db.relationship('Diagnosis')
    diagnosisType = db.relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = db.relationship('rbDiseaseCharacter')
    stage = db.relationship('rbDiseaseStage', lazy=False)
    phase = db.relationship('rbDiseasePhases', lazy=False)
    dispanser = db.relationship('rbDispanser')
    traumaType = db.relationship('rbTraumaType')
    healthGroup = db.relationship('rbHealthGroup', lazy=False)

    def __int__(self):
        return self.id


class Event(db.Model):
    __tablename__ = u'Event'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    externalId = db.Column(db.String(30), nullable=False)
    eventType_id = db.Column(db.Integer, db.ForeignKey('EventType.id'), nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), index=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), index=True)
    prevEventDate = db.Column(db.DateTime)
    setDate = db.Column(db.DateTime, nullable=False, index=True)
    setPerson_id = db.Column(db.Integer, index=True)
    execDate = db.Column(db.DateTime, index=True)
    execPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    isPrimaryCode = db.Column("isPrimary", db.Integer, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    result_id = db.Column(db.Integer, db.ForeignKey('rbResult.id'), index=True)
    nextEventDate = db.Column(db.DateTime)
    payStatus = db.Column(db.Integer, nullable=False)
    typeAsset_id = db.Column(db.Integer, db.ForeignKey('rbEmergencyTypeAsset.id'), index=True)
    note = db.Column(db.Text, nullable=False)
    curator_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    assistant_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    pregnancyWeek = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    MES_id = db.Column(db.Integer, index=True)
    mesSpecification_id = db.Column(db.ForeignKey('rbMesSpecification.id'), index=True)
    rbAcheResult_id = db.Column(db.ForeignKey('rbAcheResult.id'), index=True)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    privilege = db.Column(db.Integer, server_default=u"'0'")
    urgent = db.Column(db.Integer, server_default=u"'0'")
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('Person.orgStructure_id'))
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")
    lpu_transfer = db.Column(db.String(100))

    actions = db.relationship(u'Action', primaryjoin="and_(Action.event_id == Event.id, Action.deleted == 0)")
    eventType = db.relationship(u'EventType', lazy=False)
    execPerson = db.relationship(u'Person', foreign_keys='Event.execPerson_id', lazy=False)
    curator = db.relationship(u'Person', foreign_keys='Event.curator_id', lazy=False)
    assistant = db.relationship(u'Person', foreign_keys='Event.assistant_id', lazy=False)
    contract = db.relationship(u'Contract')
    organisation = db.relationship(u'Organisation')
    mesSpecification = db.relationship(u'rbMesSpecification', lazy=False)
    rbAcheResult = db.relationship(u'rbAcheResult', lazy=False)
    result = db.relationship(u'rbResult', lazy=False)
    typeAsset = db.relationship(u'rbEmergencyTypeAsset', lazy=False)
    localContract = db.relationship(u'EventLocalContract')
    client = db.relationship(u'Client')
    diagnostics = db.relationship(
        u'Diagnostic', lazy=True, innerjoin=True, primaryjoin=
        "and_(Event.id == Diagnostic.event_id, Diagnostic.deleted == 0)"
    )

    @property
    def isPrimary(self):
        return self.isPrimaryCode == 1

    @property
    def finance(self):
        return self.eventType.finance

    @property
    def departmentManager(self):
        return Person.join(rbPost).filter(
            Person.orgStructure_id == self.orgStructure_id,
            rbPost.flatCode == u'departmentManager'
        ).first()

    @property
    def date(self):
        date = self.execDate if self.execDate is not None else datetime.date.today()
        return date

    def __unicode__(self):
        return unicode(self.eventType)

    def __int__(self):
        return self.id


class EventType(db.Model):
    __tablename__ = u'EventType'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    purpose_id = db.Column(db.Integer, db.ForeignKey('rbEventTypePurpose.id'), index=True)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    scene_id = db.Column(db.Integer, index=True)
    visitServiceModifier = db.Column(db.String(128), nullable=False)
    visitServiceFilter = db.Column(db.String(32), nullable=False)
    visitFinance = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionFinance = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    period = db.Column(db.Integer, nullable=False)
    singleInPeriod = db.Column(db.Integer, nullable=False)
    isLong = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    dateInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    printContext = db.Column("context", db.String(64), nullable=False)
    form = db.Column(db.String(64), nullable=False)
    minDuration = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    maxDuration = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showStatusActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showDiagnosticActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showCureActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showMiscActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    limitStatusActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitDiagnosticActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitCureActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitMiscActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showTime = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    medicalAidType_id = db.Column(db.Integer, index=True)
    eventProfile_id = db.Column(db.Integer, index=True)
    mesRequired = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    mesCodeMask = db.Column(db.String(64), server_default=u"''")
    mesNameMask = db.Column(db.String(64), server_default=u"''")
    counter_id = db.Column(db.ForeignKey('rbCounter.id'), index=True)
    isExternal = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isAssistant = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isCurator = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    canHavePayableActions = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isRequiredCoordination = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isOrgStructurePriority = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isTakenTissue = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    rbMedicalKind_id = db.Column(db.ForeignKey('rbMedicalKind.id'), index=True)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    requestType_id = db.Column(db.Integer, db.ForeignKey('rbRequestType.id'))

    counter = db.relationship(u'rbCounter')
    rbMedicalKind = db.relationship(u'rbMedicalKind')
    purpose = db.relationship(u'rbEventTypePurpose')
    finance = db.relationship(u'rbFinance')
    service = db.relationship(u'rbService')
    requestType = db.relationship(u'rbRequestType', lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'purpose': self.purpose,
            'finance': self.finance,
            'print_context': self.printContext,
            'form': self.form,
            'mes': {
                'required': self.mesRequired,
                'code_mask': self.mesCodeMask,
                'name_mask': self.mesNameMask,
            },
            'restrictions': AgeSex(self),
            'medical_kind': self.rbMedicalKind,
            'service': self.service,
            'request_type': self.requestType,
        }

    def __int__(self):
        return self.id


class rbCounter(db.Model):
    __tablename__ = u'rbCounter'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    prefix = db.Column(db.String(32))
    separator = db.Column(db.String(8), server_default=u"' '")
    reset = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    startDate = db.Column(db.DateTime, nullable=False)
    resetDate = db.Column(db.DateTime)
    sequenceFlag = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbMedicalKind(db.Model):
    __tablename__ = u'rbMedicalKind'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(1, u'utf8_unicode_ci'), nullable=False)
    name = db.Column(db.String(64, u'utf8_unicode_ci'), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbEventTypePurpose(db.Model):
    __tablename__ = u'rbEventTypePurpose'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    codePlace = db.Column(db.String(2))

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'code_place': self.codePlace,
        }

    def __int__(self):
        return self.id


class rbPrintTemplate(db.Model):
    __tablename__ = u'rbPrintTemplate'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    context = db.Column(db.String(64), nullable=False)
    fileName = db.Column(db.String(128), nullable=False)
    default = db.Column(db.Unicode, nullable=False)
    dpdAgreement = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    render = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbService(db.Model):
    __tablename__ = u'rbService'
    __table_args__ = (
        db.Index(u'infis', u'infis', u'eisLegacy'),
        db.Index(u'group_id_idx', u'group_id', u'idx')
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(31), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    eisLegacy = db.Column(db.Boolean, nullable=False)
    nomenclatureLegacy = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    license = db.Column(db.Boolean, nullable=False)
    infis = db.Column(db.String(31), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    medicalAidProfile_id = db.Column(db.ForeignKey('rbMedicalAidProfile.id'), index=True)
    adultUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    adultUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    rbMedicalKind_id = db.Column(db.ForeignKey('rbMedicalKind.id'), index=True)
    UET = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    departCode = db.Column(db.String(3))
    group_id = db.Column(db.ForeignKey('rbService.id'))
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    group = db.relationship(u'rbService', remote_side=[id])
    medicalAidProfile = db.relationship(u'rbMedicalAidProfile')
    rbMedicalKind = db.relationship(u'rbMedicalKind')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'infis': self.infis,
            'begDate': self.begDate,
            'endDate': self.endDate,
            'adult_uet_doctor': self.adultUetDoctor,
            'adult_uet_average_medical_worker': self.adultUetAverageMedWorker,
            'child_uet_doctor': self.childUetDoctor,
            'child_uet_average_medical_worker': self.childUetAverageMedWorker,
            'uet': self.UET,
            'department_code': self.departCode,
            'medical_aid_profile': self.medicalAidProfile,
            'medical_kind': self.rbMedicalKind,
        }

    def __int__(self):
        return self.id


class rbRequestType(db.Model):
    __tablename__ = u'rbRequestType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    relevant = db.Column(db.Integer, nullable=False, server_default=u"'1'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbResult(db.Model):
    __tablename__ = u'rbResult'

    id = db.Column(db.Integer, primary_key=True)
    eventPurpose_id = db.Column(db.ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    continued = db.Column(db.Integer, nullable=False)
    regionalCode = db.Column(db.String(8), nullable=False)

    eventPurpose = db.relationship(u'rbEventTypePurpose')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'continued': bool(self.continued),
            'regional_code': self.regionalCode,
        }

    def __int__(self):
        return self.id


class rbAcheResult(db.Model):
    __tablename__ = u'rbAcheResult'

    id = db.Column(db.Integer, primary_key=True)
    eventPurpose_id = db.Column(db.ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = db.Column(db.String(3, u'utf8_unicode_ci'), nullable=False)
    name = db.Column(db.String(64, u'utf8_unicode_ci'), nullable=False)

    eventPurpose = db.relationship(u'rbEventTypePurpose')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class Contract(db.Model):
    __tablename__ = u'Contract'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    number = db.Column(db.String(64), nullable=False)
    date = db.Column(db.Date, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    recipientAccount_id = db.Column(db.Integer, db.ForeignKey('Organisation_Account.id'), index=True)
    recipientKBK = db.Column(db.String(30), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)
    payerAccount_id = db.Column(db.Integer, db.ForeignKey('Organisation_Account.id'), index=True)
    payerKBK = db.Column(db.String(30), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), nullable=False, index=True)
    grouping = db.Column(db.String(64), nullable=False)
    resolution = db.Column(db.String(64), nullable=False)
    format_id = db.Column(db.Integer, index=True)
    exposeUnfinishedEventVisits = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    exposeUnfinishedEventActions = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    visitExposition = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionExposition = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    exposeDiscipline = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    priceList_id = db.Column(db.Integer)
    coefficient = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    coefficientEx = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")

    recipient = db.relationship(u'Organisation', foreign_keys='Contract.recipient_id')
    payer = db.relationship(u'Organisation', foreign_keys='Contract.payer_id')
    finance = db.relationship(u'rbFinance')
    recipientAccount = db.relationship(u'OrganisationAccount', foreign_keys='Contract.recipientAccount_id')
    payerAccount = db.relationship(u'OrganisationAccount', foreign_keys='Contract.payerAccount_id')

    def __unicode__(self):
        return u'%s %s' % (self.number, self.date)

    def __json__(self):
        return {
            'id': self.id,
            'number': self.number,
            'date': self.date,
            'begDate': self.begDate,
            'endDate': self.endDate,
            'grouping': self.grouping,
            'resolution': self.resolution,
            # format_id = db.Column(db.Integer, index=True)
            'exposeUnfinishedEventVisits': bool(self.exposeUnfinishedEventVisits),
            'exposeUnfinishedEventActions': bool(self.exposeUnfinishedEventActions),
            'visitExposition': self.visitExposition,
            'actionExposition': self.actionExposition,
            'exposeDiscipline': self.exposeDiscipline,
            # priceList_id = db.Column(db.Integer)
            'coefficient': float(self.coefficient),
            'coefficientEx': float(self.coefficientEx),

            'recipient': self.recipient,
            'recipientKBK': self.recipientKBK,
            'recipientAccount': self.recipientAccount,

            'payer': self.payer,
            'payerKBK': self.payerKBK,
            'payerAccount': self.payerAccount,

            'finance': self.finance,

        }

    def __int__(self):
        return self.id


class OrganisationAccount(db.Model):
    __tablename__ = u'Organisation_Account'

    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    bankName = db.Column(db.Unicode(128), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String, nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('Bank.id'), nullable=False, index=True)
    cash = db.Column(db.Integer, nullable=False)

    org = db.relationship(u'Organisation')
    bank = db.relationship(u'Bank')

    def __json__(self):
        return {
            'id': self.id,
            'bank_name': self.bankName,
            'name': self.name,
            'notes': self.notes,
            'cash': self.cash,
            # 'organisation': self.org,
            'bank': self.bank,
        }

    def __int__(self):
        return self.id


class Bank(db.Model):
    __tablename__ = u'Bank'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    bik = db.Column("BIK", db.String(10), nullable=False, index=True)
    name = db.Column(db.Unicode(100), nullable=False, index=True)
    branchName = db.Column(db.Unicode(100), nullable=False)
    corrAccount = db.Column(db.String(20), nullable=False)
    subAccount = db.Column(db.String(20), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'bik': self.bik,
            'branch_name': self.branchName,
            'corr_account': self.corrAccount,
            'sub_account': self.subAccount,
        }

    def __int__(self):
        return self.id


class EventLocalContract(db.Model):
    __tablename__ = u'Event_LocalContract'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName', u'birthDate', u'id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False)
    master_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=False, index=True)
    coordDate = db.Column(db.DateTime)
    coordAgent = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordInspector = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordText = db.Column(db.String, nullable=False)
    dateContract = db.Column(db.Date, nullable=False)
    numberContract = db.Column(db.Unicode(64), nullable=False)
    sumLimit = db.Column(db.Float(asdecimal=True), nullable=False)
    lastName = db.Column(db.Unicode(30), nullable=False)
    firstName = db.Column(db.Unicode(30), nullable=False)
    patrName = db.Column(db.Unicode(30), nullable=False)
    birthDate = db.Column(db.Date, nullable=False, index=True)
    documentType_id = db.Column(db.Integer, db.ForeignKey('rbDocumentType.id'), index=True)
    serialLeft = db.Column(db.Unicode(8), nullable=False)
    serialRight = db.Column(db.Unicode(8), nullable=False)
    number = db.Column(db.String(16), nullable=False)
    regAddress = db.Column(db.Unicode(64), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)

    org = db.relationship(u'Organisation')
    documentType = db.relationship(u'rbDocumentType')

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

    # Это что вообще?!
    @property
    def document(self):
        document = ClientDocument()
        document.documentType = self.documentType
        document.serial = u'%s %s' % (self.serialLeft, self.serialRight)
        document.number = self.number
        return document

    def __int__(self):
        return self.id


class rbMesSpecification(db.Model):
    __tablename__ = u'rbMesSpecification'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    done = db.Column(db.Integer, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'done': self.done,
        }

    def __int__(self):
        return self.id


class rbEmergencyTypeAsset(db.Model):
    __tablename__ = u'rbEmergencyTypeAsset'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    codeRegional = db.Column(db.String(8), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.codeRegional,
        }

    def __int__(self):
        return self.id


class rbMedicalAidProfile(db.Model):
    __tablename__ = u'rbMedicalAidProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
        }

    def __int__(self):
        return self.id


class rbDiagnosisType(db.Model):
    __tablename__ = u'rbDiagnosisType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    replaceInDiagnosis = db.Column(db.String(8), nullable=False)
    flatCode = db.Column(db.String(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'flat_code': self.flatCode,
        }

    def __int__(self):
        return self.id


class rbDiseaseCharacter(db.Model):
    __tablename__ = u'rbDiseaseCharacter'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    replaceInDiagnosis = db.Column(db.String(8), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDiseasePhases(db.Model):
    __tablename__ = u'rbDiseasePhases'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    characterRelation = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDiseaseStage(db.Model):
    __tablename__ = u'rbDiseaseStage'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    characterRelation = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDispanser(db.Model):
    __tablename__ = u'rbDispanser'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    observed = db.Column(db.Integer, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'observed': self.observed,
        }

    def __int__(self):
        return self.id


class rbTraumaType(db.Model):
    __tablename__ = u'rbTraumaType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbHealthGroup(db.Model):
    __tablename__ = u'rbHealthGroup'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class MKB(db.Model):
    __tablename__ = u'MKB'
    __table_args__ = (
        db.Index(u'BlockID', u'BlockID', u'DiagID'),
        db.Index(u'ClassID_2', u'ClassID', u'BlockID', u'BlockName'),
        db.Index(u'ClassID', u'ClassID', u'ClassName')
    )

    id = db.Column(db.Integer, primary_key=True)
    ClassID = db.Column(db.String(8), nullable=False)
    ClassName = db.Column(db.String(150), nullable=False)
    BlockID = db.Column(db.String(9), nullable=False)
    BlockName = db.Column(db.String(160), nullable=False)
    DiagID = db.Column(db.String(8), nullable=False, index=True)
    DiagName = db.Column(db.String(160), nullable=False, index=True)
    Prim = db.Column(db.String(1), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(12), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    characters = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, index=True)
    MKBSubclass_id = db.Column(db.Integer)

    def __unicode__(self):
        return self.DiagID

    def __int__(self):
        return self.id


class rbUserProfile(db.Model):
    __tablename__ = u'rbUserProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    withDep = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbUserProfileRight(db.Model):
    __tablename__ = u'rbUserProfile_Right'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, nullable=False, index=True)
    userRight_id = db.Column(db.Integer, nullable=False, index=True)


class rbUserRight(db.Model):
    __tablename__ = u'rbUserRight'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)


class FDField(db.Model):
    __tablename__ = u'FDField'

    id = db.Column(db.Integer, primary_key=True)
    fdFieldType_id = db.Column(db.ForeignKey('FDFieldType.id'), nullable=False, index=True)
    flatDirectory_id = db.Column(db.ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = db.Column(db.ForeignKey('FlatDirectory.code'), index=True)
    name = db.Column(db.String(4096), nullable=False)
    description = db.Column(db.String(4096))
    mask = db.Column(db.String(4096))
    mandatory = db.Column(db.Integer)
    order = db.Column(db.Integer)

    fdFieldType = db.relationship(u'FDFieldType')
    FlatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDField.flatDirectory_code == FlatDirectory.code')
    flatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDField.flatDirectory_id == FlatDirectory.id')


class FDFieldType(db.Model):
    __tablename__ = u'FDFieldType'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096), nullable=False)
    description = db.Column(db.String(4096))


class FDFieldValue(db.Model):
    __tablename__ = u'FDFieldValue'

    id = db.Column(db.Integer, primary_key=True)
    fdRecord_id = db.Column(db.ForeignKey('FDRecord.id'), nullable=False, index=True)
    fdField_id = db.Column(db.ForeignKey('FDField.id'), nullable=False, index=True)
    value = db.Column(db.String)

    fdField = db.relationship(u'FDField')
    fdRecord = db.relationship(u'FDRecord')


class FDRecord(db.Model):
    __tablename__ = u'FDRecord'

    id = db.Column(db.Integer, primary_key=True)
    flatDirectory_id = db.Column(db.ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = db.Column(db.ForeignKey('FlatDirectory.code'), index=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(4096))
    description = db.Column(db.String(4096))
    dateStart = db.Column(db.DateTime)
    dateEnd = db.Column(db.DateTime)

    FlatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDRecord.flatDirectory_code == FlatDirectory.code')
    flatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDRecord.flatDirectory_id == FlatDirectory.id')


class FlatDirectory(db.Model):
    __tablename__ = u'FlatDirectory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096), nullable=False)
    code = db.Column(db.String(128), index=True)
    description = db.Column(db.String(4096))


class UUID(db.Model):
    __tablename__ = u'UUID'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), nullable=False, unique=True)
