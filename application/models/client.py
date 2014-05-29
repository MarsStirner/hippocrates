# -*- coding: utf-8 -*-
import datetime
from application.lib.agesex import calcAgeTuple
from application.models.enums import Gender
from application.models.exists import rbDocumentTypeGroup
from application.models.kladr_models import Kladr, Street
from application.systemwide import db
from sqlalchemy import orm


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
    uuid_id = db.Column(db.Integer, db.ForeignKey('UUID.id'), nullable=False, index=True,
                        server_default=u"'0'")

    uuid = db.relationship('UUID')
    documents = db.relationship(u'ClientDocument',
                                primaryjoin='and_(ClientDocument.clientId==Client.id, ClientDocument.deleted == 0)',
                                order_by="desc(ClientDocument.id)",
                                backref=db.backref('client'),
                                lazy='dynamic')
    documents_all = db.relationship('ClientDocument',
                                    primaryjoin='and_(ClientDocument.clientId==Client.id, ClientDocument.deleted != 1)',
                                    order_by="desc(ClientDocument.id)")
    policies = db.relationship(u'ClientPolicy',
                               primaryjoin='and_(ClientPolicy.clientId==Client.id, ClientPolicy.deleted == 0)',
                               order_by="desc(ClientPolicy.id)",
                               backref=db.backref('client'),
                               lazy='dynamic')
    policies_all = db.relationship('ClientPolicy',
                                   primaryjoin='and_(ClientPolicy.clientId==Client.id, ClientPolicy.deleted != 1)',
                                   order_by="desc(ClientPolicy.id)")
    reg_address = db.relationship(u'ClientAddress',
                                  primaryjoin="and_(Client.id==ClientAddress.client_id, ClientAddress.type==0)",
                                  order_by="desc(ClientAddress.id)", uselist=False)
    loc_address = db.relationship(u'ClientAddress',
                                  primaryjoin="and_(Client.id==ClientAddress.client_id, ClientAddress.type==1)",
                                  order_by="desc(ClientAddress.id)", uselist=False)
    socStatuses = db.relationship(u'ClientSocStatus',
                                  primaryjoin='and_(ClientSocStatus.deleted == 0, ClientSocStatus.client_id==Client.id)',
                                  backref=db.backref('client'),
                                  lazy='dynamic') #todo: filter_by_date
    #  primaryjoin='and_(ClientSocStatus.deleted == 0, ClientSocStatus.client_id==Client.id,'
    #                                           'or_(ClientSocStatus.endDate == None, ClientSocStatus.endDate>={0}))'.format(
    #                                   datetime.date.today()))
    intolerances = db.relationship(u'ClientIntoleranceMedicament',
                                   primaryjoin='and_(ClientIntoleranceMedicament.client_id==Client.id,'
                                               'ClientIntoleranceMedicament.deleted == 0)',
                                   backref=db.backref('client'),
                                   lazy='dynamic')
    identifications = db.relationship(u'ClientIdentification',
                                      primaryjoin='and_(ClientIdentification.client_id==Client.id,'
                                                  'ClientIdentification.deleted == 0)',
                                      backref=db.backref('client'),
                                      lazy='dynamic')
    allergies = db.relationship(u'ClientAllergy',
                                primaryjoin='and_(ClientAllergy.client_id==Client.id, ClientAllergy.deleted == 0)',
                                backref=db.backref('client'),
                                lazy='dynamic')
    blood_history = db.relationship(u'BloodHistory',
                                    backref=db.backref('client'),
                                    lazy='dynamic')
    direct_relations = db.relationship(u'DirectClientRelation',
                                       primaryjoin='and_(ClientRelation.client_id==Client.id,'
                                                   'ClientRelation.deleted == 0)',
                                       foreign_keys='ClientRelation.client_id',
                                       backref=db.backref('client'),
                                       lazy='dynamic')
    reversed_relations = db.relationship(u'ReversedClientRelation',
                                         primaryjoin='and_(ClientRelation.relative_id==Client.id,'
                                                     'ClientRelation.deleted == 0)',
                                         foreign_keys='ClientRelation.relative_id',
                                         backref=db.backref('client'),
                                         lazy='dynamic')
    contacts = db.relationship('ClientContact',
                               primaryjoin='and_(ClientContact.client_id==Client.id, ClientContact.deleted == 0)',
                               backref=db.backref('client'),
                               lazy='dynamic')
    works = db.relationship(u'ClientWork', primaryjoin='and_(ClientWork.client_id==Client.id, ClientWork.deleted == 0)',
                            order_by="desc(ClientWork.id)")

    events = db.relationship(
        u'Event', lazy='dynamic', order_by='desc(Event.createDatetime)',
        primaryjoin='and_(Event.deleted == 0, Event.client_id == Client.id)')
    appointments = db.relationship(
        u'ScheduleClientTicket', lazy='dynamic',  #order_by='desc(ScheduleTicket.begDateTime)',
        primaryjoin='and_(ScheduleClientTicket.deleted == 0, ScheduleClientTicket.client_id == Client.id)',
        innerjoin=True
    )

    def __init__(self):
        self.init_on_load()

    @orm.reconstructor
    def init_on_load(self):
        self._id_document = None

    def age_tuple(self, moment=None):
        """
        @type moment: datetime.datetime
        """
        if not moment:
            moment = datetime.datetime.now()
        return calcAgeTuple(self.birthDate, moment)

    @property
    def nameText(self):
        return u' '.join((u'%s %s %s' % (self.lastName or '', self.firstName or '', self.patrName or '')).split())

    @property
    def shortNameText(self):
        words = self.firstName.split() + self.patrName.split()
        initials = ['%s.' % word[0].upper() for word in words if word]
        return u'%s %s' % (self.lastName, u' '.join(initials))

    @property
    def sex(self):
        return unicode(Gender(self.sexCode))

    @property
    def formatted_SNILS(self):
        if self.SNILS:
            s = self.SNILS + ' ' * 14
            return u'%s-%s-%s %s' % (s[0:3], s[3:6], s[6:9], s[9:11])
        else:
            return u''

    @property
    def document(self):
        # TODO: get rid of
        return self.id_document

    @property
    def id_document(self):
        if not self._id_document:
            self._id_document = (self.documents.filter(ClientDocument.deleted == 0).
                filter(rbDocumentTypeGroup.code == '1').order_by(ClientDocument.date.desc()).first())
        return self._id_document

    def get_actual_document_by_code(self, doc_type_code):
        # пока не используется
        return (self.documents.filter(ClientDocument.deleted == 0).
                filter(rbDocumentTypeGroup.code == doc_type_code).
                order_by(ClientDocument.date.desc()).first())

    @property
    def policy(self):
        return self.compulsoryPolicy

    @property
    def policyDMS(self):
        return self.voluntaryPolicy

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
    def phones(self):
        contacts = [(contact.name, contact.contact, contact.notes) for contact in self.contacts]
        return ', '.join([
            (u'%s: %s (%s)' % (phone[0], phone[1], phone[2])) if phone[2]
            else (u'%s: %s' % (phone[0], phone[1]))
            for phone in contacts
        ])

    def __unicode__(self):
        return self.nameText

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'patrName': self.patrName,
            'birthDate': self.birthDate,
            'sex': Gender(self.sexCode),
            'SNILS': self.SNILS,
            'fullName': self.nameText,
            'work_org_id': self.works[0].org_id if self.works else None,
            'comp_policy': self.compulsoryPolicy,
            'vol_policy': self.voluntaryPolicy,
            'direct_relations': self.direct_relations.all(),
            'reversed_relations': self.reversed_relations.all(),  # todo: more
        }


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

    def __json__(self):
        return {
            'id': self.id,
            'deleted': self.deleted,
            'type': self.type,
            'address_id': self.address_id,
            'address': self.address,
            'freeInput': self.freeInput,
            'localityType': self.localityType
        }

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

    id = db.Column("id", db.Integer, primary_key=True)
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

    documentType = db.relationship(u'rbDocumentType', lazy=False)

    @property
    def documentTypeCode(self):
        return self.documentType.regionalCode

    @property
    def serial_left(self):
        try:
            sl = self.serial.split(' ')[0]
        except (AttributeError, IndexError):
            sl = None
        return sl

    @property
    def serial_right(self):
        try:
            sr = self.serial.split(' ')[1]
        except (AttributeError, IndexError):
            sr = None
        return sr

    def __unicode__(self):
        return (' '.join([self.documentType.name, self.serial, self.number])).strip()

    def __json__(self):
        return {
            'id': self.id,
            'documentType': self.documentType,
            'deleted': self.deleted,
            'serial': self.serial,
            'number': self.number,
            'begDate': self.date,
            'endDate': self.endDate,
            'origin': self.origin,
            'documentText': self.__unicode__(),
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

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'deleted': self.deleted,
            'relativeType': self.relativeType,
            'other_id': self.other.id,
            'other_text': self.other.nameText + ' ({})'.format(self.other.id)
        }


class ClientWork(db.Model):
    __tablename__ = u'ClientWork'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    org_id = db.Column(db.ForeignKey('Organisation.id'), index=True)
    shortName = db.Column('freeInput', db.String(200), nullable=False)
    post = db.Column(db.String(200), nullable=False)
    stage = db.Column(db.Integer, nullable=False)
    OKVED = db.Column(db.String(10), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    rank_id = db.Column(db.Integer, nullable=False)
    arm_id = db.Column(db.Integer, nullable=False)

    client = db.relationship(u'Client')
    organisation = db.relationship(u'Organisation')
    # hurts = db.relationship(u'ClientworkHurt')

    def __unicode__(self):
        parts = []
        if self.shortName:
            parts.append(self.shortName)
        if self.post:
            parts.append(self.post)
        if self.OKVED:
            parts.append(u'ОКВЭД: '+self._OKVED)
        return ', '.join(parts)


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

    insurer = db.relationship(u'Organisation', lazy=False)
    policyType = db.relationship(u'rbPolicyType', lazy=False)

    def __unicode__(self):
        return (' '.join([self.policyType.name, unicode(self.insurer), self.serial, self.number])).strip()

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'insurer_id': self.insurer_id,
            'policyType_id': self.policyType_id
        }


class BloodHistory(db.Model):
    __tablename__ = u'BloodHistory'

    id = db.Column(db.Integer, primary_key=True)
    bloodDate = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    bloodType_id = db.Column(db.Integer, db.ForeignKey('rbBloodType.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), nullable=False)

    bloodType = db.relationship("rbBloodType")
    person = db.relationship('Person')

    def __int__(self):
        return self.id


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

    def __json__(self):
        return {
            'id': self.id,
            'deleted': self.deleted,
            'house_id': self.house_id,
            'house': self.house,
            'flat': self.flat
        }

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

    def __json__(self):
        return {
            'id': self.id,
            'deleted': self.deleted,
            'locality_code': self.KLADRCode,
            'street_code': self.KLADRStreetCode,
            'number': self.number,
            'corpus': self.corpus
        }

    def __int__(self):
        return self.id