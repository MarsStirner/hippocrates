# -*- coding: utf-8 -*-
import datetime
from application.systemwide import db
from exists import FDRecord
from sqlalchemy.orm.collections import InstrumentedList
from application.models.utils import safe_current_user_id, get_model_by_name

__author__ = 'mmalkov'


class Action(db.Model):
    __tablename__ = u'Action'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    directionDate = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)
    setPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    isUrgent = db.Column(db.Boolean, nullable=False, server_default=u"'0'")
    begDate = db.Column(db.DateTime)
    plannedEndDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime)
    note = db.Column(db.Text, nullable=False, default='')
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    office = db.Column(db.String(16), nullable=False, default='')
    amount = db.Column(db.Float(asdecimal=True), nullable=False)
    uet = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    expose = db.Column(db.Boolean, nullable=False, server_default=u"'1'")
    payStatus = db.Column(db.Integer, nullable=False, default=0)
    account = db.Column(db.Boolean, nullable=False, default=0)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    prescription_id = db.Column(db.Integer, index=True)
    takenTissueJournal_id = db.Column(db.ForeignKey('TakenTissueJournal.id'), index=True)
    contract_id = db.Column(db.Integer, index=True)
    coordDate = db.Column(db.DateTime)
    coordPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    coordAgent = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordInspector = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordText = db.Column(db.String, nullable=False, default='')
    hospitalUidFrom = db.Column(db.String(128), nullable=False, server_default=u"'0'")
    pacientInQueueType = db.Column(db.Integer, server_default=u"'0'")
    AppointmentType = db.Column(
        db.Enum(u'0', u'amb', u'hospital', u'polyclinic', u'diagnostics', u'portal', u'otherLPU'),
        nullable=False, default=u'0')
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    parentAction_id = db.Column(db.Integer, index=True)
    uuid_id = db.Column(db.ForeignKey('UUID.id'), nullable=False, index=True, server_default=u"'0'")
    dcm_study_uid = db.Column(db.String(50))

    actionType = db.relationship(u'ActionType')
    event = db.relationship(u'Event')
    person = db.relationship(u'Person', foreign_keys='Action.person_id')
    setPerson = db.relationship(u'Person', foreign_keys='Action.setPerson_id')
    coordPerson = db.relationship(u'Person', foreign_keys='Action.coordPerson_id')
    takenTissueJournal = db.relationship(u'TakenTissueJournal')
    # tissues = db.relationship(u'Tissue', secondary=u'ActionTissue')
    properties = db.relationship(u'ActionProperty')
    self_finance = db.relationship(u'rbFinance')
    uuid = db.relationship('UUID')


class ActionProperty(db.Model):
    __tablename__ = u'ActionProperty'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), nullable=False, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('ActionPropertyType.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('rbUnit.id'), index=True)
    norm = db.Column(db.String(64), nullable=False, default='')
    isAssigned = db.Column(db.Boolean, nullable=False, server_default=u"'0'")
    evaluation = db.Column(db.Integer, default=None)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    action = db.relationship(u'Action')
    type = db.relationship(u'ActionPropertyType', lazy=False, innerjoin=True)
    unit = db.relationship(u'rbUnit', lazy=False)

    def __get_property_name(self):
        type_name = self.type.typeName
        if type_name in ["Constructor", u"Жалобы", 'Text', 'Html']:
            class_name = 'String'
        elif type_name == u"Запись в др. ЛПУ":
            class_name = 'OtherLPURecord'
        elif type_name == "FlatDirectory":
            class_name = 'FDRecord'
        else:
            class_name = type_name
        return '_value_{0}'.format(class_name)

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
            return None
        if self.type.isVector:
            return [item.value for item in value_object]
        else:
            return value_object[0].value

    @value.setter
    def value(self, value):
        self.set_value(value)

    def set_value(self, value, raw=False):
        value_object = self.value_object
        # Следующая магия вытаскивает класс, ассоциированный с backref-пропертей, созданной этим же классом у нашего
        # ActionProperty. Объекты этого класса мы будем создавать для значений
        value_class = getattr(self.__class__, self.__get_property_name()).property.mapper.class_

        def set_value(val_object, value):
            if raw and hasattr(val_object, 'value_'):
                val_object.value_ = value
            else:
                val_object.value = value

        def make_value(value, index=0):
            val = value_class()
            set_value(val, value)
            val.index = index
            val.property_object = self
            db.session.add(val)
            return val

        if not self.type.isVector:
            if len(value_object) == 0:
                if value is not None:
                    value_object.append(make_value(value))
            else:
                if value is None:
                    db.session.delete(value_object[0])
                else:
                    set_value(value_object[0], value)
        else:
            m = min(len(value_object), len(value))
            for i in xrange(m):
                value_object[i].value = value[i]
            if len(value_object) < len(value):
                for i in xrange(m, len(value)):
                    value_object.append(make_value(value[i], i))
            elif len(value_object) > len(value):
                for i in xrange(len(value_object)-1, m-1, -1):
                    db.session.delete(value_object[i])

    def __json__(self):
        return {
            'id': self.id,
            'idx': self.type.idx,
            'type': self.type,
            'is_assigned': self.isAssigned,
            'value': self.value,
        }


class ActionPropertyTemplate(db.Model):
    __tablename__ = u'ActionPropertyTemplate'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, index=True)
    parentCode = db.Column(db.String(20), nullable=False)
    code = db.Column(db.String(64), nullable=False, index=True)
    federalCode = db.Column(db.String(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(120), nullable=False, index=True)
    abbrev = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    service_id = db.Column(db.Integer, index=True)


class ActionPropertyType(db.Model):

    __tablename__ = u'ActionPropertyType'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    template_id = db.Column(db.ForeignKey('ActionPropertyTemplate.id'), index=True)
    name = db.Column(db.String(128), nullable=False)
    descr = db.Column(db.String(128), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('rbUnit.id'), index=True)
    typeName = db.Column(db.String(64), nullable=False)
    valueDomain = db.Column(db.Text, nullable=False)
    defaultValue = db.Column(db.String(5000), nullable=False)
    isVector = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    norm = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    penalty = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    visibleInJobTicket = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isAssignable = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    test_id = db.Column(db.Integer, index=True)
    defaultEvaluation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    toEpicrisis = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(25), index=True)
    mandatory = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    readOnly = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    createDatetime = db.Column(db.DateTime, nullable=False, index=True)
    createPerson_id = db.Column(db.Integer)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer)

    unit = db.relationship('rbUnit')
    template = db.relationship('ActionPropertyTemplate')

    def __json__(self):
        result = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'domain': self.valueDomain,
            'is_assignable': self.isAssignable,
            'ro': self.readOnly,
            'mandatory': self.mandatory,
            'type_name': self.typeName,
            'unit': self.unit,
            'vector': bool(self.isVector),
        }
        if self.typeName == 'String':
            if self.valueDomain:
                result['values'] = [choice.strip('\' *') for choice in self.valueDomain.split(',')]
        return result


class ActionProperty__ValueType(db.Model):
    __abstract__ = True


class ActionProperty_Action(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Action'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Action.id'), index=True)

    value = db.relationship('Action')
    property_object = db.relationship('ActionProperty', backref='_value_Action')


class ActionProperty_Date(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Date'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Date)

    property_object = db.relationship('ActionProperty', backref='_value_Date')


class ActionProperty_Double(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Double'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Float(asdecimal=True, decimal_return_scale=2), nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_Double')


class ActionProperty_FDRecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_FDRecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('FDRecord.id'), nullable=False, index=True)

    value = db.relationship(u'FDRecord')
    property_object = db.relationship('ActionProperty', backref='_value_FDRecord')

    def get_value(self):
        return FDRecord.query.filter(FDRecord.id == self.value).first().get_value(u'Наименование')


class ActionProperty_HospitalBed(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBed'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('OrgStructure_HospitalBed.id'), index=True)

    value = db.relationship(u'OrgStructure_HospitalBed')
    property_object = db.relationship('ActionProperty', backref='_value_HospitalBed')


class ActionProperty_HospitalBedProfile(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBedProfile'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbHospitalBedProfile.id'), index=True)

    value = db.relationship('rbHospitalBedProfile')
    property_object = db.relationship('ActionProperty', backref='_value_HospitalBedProfile')


class ActionProperty_Image(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Image'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.BLOB)
    property_object = db.relationship('ActionProperty', backref='_value_Image')


class ActionProperty_ImageMap(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_ImageMap'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.String)
    property_object = db.relationship('ActionProperty', backref='_value_ImageMap')


class ActionProperty_Integer_Base(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Integer'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.Integer, nullable=False)


class ActionProperty_Integer(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_Integer')

    @property
    def value(self):
        return self.value_

    @value.setter
    def value(self, val):
        self.value_ = val


class ActionProperty_AnalysisStatus(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_AnalysisStatus')

    @property
    def value(self):
        return rbAnalysisStatus.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None


class ActionProperty_OperationType(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_OperationType')

    @property
    def value(self):
        return rbOperationType.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None




class ActionProperty_RLS(ActionProperty_Integer_Base):

    def get_value(self):
        return v_Nomen.query.get(self.value).first() if self.value else None
    property_object = db.relationship('ActionProperty', backref='_value_RLS')


class ActionProperty_ReferenceRb(ActionProperty_Integer_Base):

    @property
    def value(self):
        if not hasattr(self, 'table_name'):
            domain = ActionProperty.query.get(self.id).type.valueDomain
            self.table_name = domain.split(';')[0]
        model = get_model_by_name(self.table_name)
        return model.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None

    property_object = db.relationship('ActionProperty', backref='_value_ReferenceRb')


class ActionProperty_Table(ActionProperty_Integer_Base):

    def get_value(self):
        return {}

    property_object = db.relationship('ActionProperty', backref='_value_Table')


class ActionProperty_JobTicket(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Job_Ticket'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Job_Ticket.id'), index=True)

    value = db.relationship('JobTicket')
    property_object = db.relationship('ActionProperty', backref='_value_JobTicket')


class ActionProperty_MKB(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_MKB'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('MKB.id'), index=True)

    value = db.relationship('MKB')
    property_object = db.relationship('ActionProperty', backref='_value_MKB')


class ActionProperty_OrgStructure(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OrgStructure'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('OrgStructure.id'), index=True)

    value = db.relationship('OrgStructure')
    property_object = db.relationship('ActionProperty', backref='_value_OrgStructure')


class ActionProperty_Organisation(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Organisation'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Organisation.id'), index=True)

    value = db.relationship('Organisation')
    property_object = db.relationship('ActionProperty', backref='_value_Organisation')


class ActionProperty_OtherLPURecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OtherLPURecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text(collation=u'utf8_unicode_ci'), nullable=False)


class ActionProperty_Person(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Person'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Person.id'), index=True)

    value = db.relationship(u'Person')
    property_object = db.relationship('ActionProperty', backref='_value_Person')


class ActionProperty_String(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_String'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text, nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_String')


class ActionProperty_Time(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Time'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Time, nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_Time')


class ActionProperty_rbBloodComponentType(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbBloodComponentType'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False)
    value_ = db.Column('value', db.ForeignKey('rbTrfuBloodComponentType.id'), nullable=False)

    value = db.relationship('rbBloodComponentType')
    property_object = db.relationship('ActionProperty', backref='_value_rbBloodComponentType')


class ActionProperty_rbFinance(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbFinance'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbFinance.id'), index=True)

    value = db.relationship('rbFinance')
    property_object = db.relationship('ActionProperty', backref='_value_rbFinance')


class ActionProperty_rbReasonOfAbsence(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbReasonOfAbsence'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbReasonOfAbsence.id'), index=True)

    value = db.relationship('rbReasonOfAbsence')
    property_object = db.relationship('ActionProperty', backref='_value_rbReasonOfAbsence')


class ActionTemplate(db.Model):
    __tablename__ = u'ActionTemplate'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, index=True)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    owner_id = db.Column(db.Integer, index=True)
    speciality_id = db.Column(db.Integer, index=True)
    action_id = db.Column(db.Integer, index=True)


# t_ActionTissue = db.Table(
#     u'ActionTissue', db.metadata,
#     db.Column(u'action_id', db.ForeignKey('Action.id'), primary_key=True, nullable=False, index=True),
#     db.Column(u'tissue_id', db.ForeignKey('Tissue.id'), primary_key=True, nullable=False, index=True)
# )


class ActionType(db.Model):
    __tablename__ = u'ActionType'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hidden = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    class_ = db.Column(u'class', db.Integer, nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), index=True)
    code = db.Column(db.String(25), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    title = db.Column(db.Unicode(255), nullable=False)
    flatCode = db.Column(db.String(64), nullable=False, index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    office = db.Column(db.String(32), nullable=False)
    showInForm = db.Column(db.Integer, nullable=False)
    genTimetable = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    quotaType_id = db.Column(db.Integer, index=True)
    context = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'1'")
    amountEvaluation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultStatus = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultDirectionDate = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultPlannedEndDate = db.Column(db.Integer, nullable=False)
    defaultEndDate = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultExecPerson_id = db.Column(db.Integer, index=True)
    defaultPersonInEvent = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultPersonInEditor = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    maxOccursInEvent = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showTime = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isMES = db.Column(db.Integer)
    nomenclativeService_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    isPreferable = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    prescribedType_id = db.Column(db.Integer, index=True)
    shedule_id = db.Column(db.Integer, index=True)
    isRequiredCoordination = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isRequiredTissue = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    testTubeType_id = db.Column(db.Integer, index=True)
    jobType_id = db.Column(db.ForeignKey('rbJobType.id'), index=True)
    mnem = db.Column(db.String(32), server_default=u"''")
    layout = db.Column(db.Text)

    service = db.relationship(u'rbService', foreign_keys='ActionType.service_id')
    nomenclatureService = db.relationship(u'rbService', foreign_keys='ActionType.nomenclativeService_id')
    property_types = db.relationship(u'ActionPropertyType', lazy='dynamic')
    group = db.relationship(u'ActionType', remote_side=[id])
    jobType = db.relationship(u'rbJobType', lazy=False)
    tissue_type = db.relationship(
        'ActionType_TissueType',
        primaryjoin='and_(ActionType_TissueType.master_id == ActionType.id, ActionType_TissueType.idx == 0)',
        uselist=False
    )

    def get_property_type_by_name(self, name):
        return self.property_types.filter(ActionPropertyType.name == name).first()

    def get_property_type_by_code(self, code):
        return self.property_types.filter(ActionPropertyType.code == code).first()

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'class': self.class_,
            'flat_code': self.flatCode,
            'title': self.title,
            'context_name': self.context,
        }


class ActionType_EventType_check(db.Model):
    __tablename__ = u'ActionType_EventType_check'

    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    eventType_id = db.Column(db.ForeignKey('EventType.id'), nullable=False, index=True)
    related_actionType_id = db.Column(db.ForeignKey('ActionType.id'), index=True)
    relationType = db.Column(db.Integer)

    actionType = db.relationship(u'ActionType', primaryjoin='ActionType_EventType_check.actionType_id == ActionType.id')
    eventType = db.relationship(u'EventType')
    related_actionType = db.relationship(u'ActionType', primaryjoin='ActionType_EventType_check.related_actionType_id == ActionType.id')


class ActionType_QuotaType(db.Model):
    __tablename__ = u'ActionType_QuotaType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    quotaClass = db.Column(db.Integer)
    finance_id = db.Column(db.Integer, index=True)
    quotaType_id = db.Column(db.Integer, index=True)


class ActionType_Service(db.Model):
    __tablename__ = u'ActionType_Service'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    finance_id = db.Column(db.Integer, index=True)
    service_id = db.Column(db.Integer, index=True)


class ActionType_TissueType(db.Model):
    __tablename__ = u'ActionType_TissueType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    tissueType_id = db.Column(db.ForeignKey('rbTissueType.id'), index=True)
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)

    master = db.relationship(u'ActionType')
    tissueType = db.relationship(u'rbTissueType')
    unit = db.relationship(u'rbUnit')


class ActionType_User(db.Model):
    __tablename__ = u'ActionType_User'
    __table_args__ = (
        db.Index(u'person_id_profile_id', u'person_id', u'profile_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'))
    profile_id = db.Column(db.ForeignKey('rbUserProfile.id'), index=True)

    actionType = db.relationship(u'ActionType')
    person = db.relationship(u'Person')
    profile = db.relationship(u'rbUserProfile')


class rbUnit(db.Model):
    __tablename__ = u'rbUnit'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(256), index=True)
    name = db.Column(db.Unicode(256), index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbTissueType(db.Model):
    __tablename__ = u'rbTissueType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    group_id = db.Column(db.ForeignKey('rbTissueType.id'), index=True)
    sexCode = db.Column("sex", db.Integer, nullable=False, server_default=u"'0'")

    group = db.relationship(u'rbTissueType', remote_side=[id])

    @property
    def sex(self):
        return {0: u'Любой',
                1: u'М',
                2: u'Ж'}[self.sexCode]

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'sex': self.sex,
        }


class TakenTissueJournal(db.Model):
    __tablename__ = u'TakenTissueJournal'
    __table_args__ = (
        db.Index(u'period_barcode', u'period', u'barcode'),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False, index=True)
    tissueType_id = db.Column(db.ForeignKey('rbTissueType.id'), nullable=False, index=True)
    externalId = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)
    datetimeTaken = db.Column(db.DateTime, nullable=False)
    execPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    note = db.Column(db.String(128), nullable=False, default='')
    barcode = db.Column(db.Integer, nullable=False)  # set with trigger
    period = db.Column(db.Integer, nullable=False)  # set with trigger

    client = db.relationship(u'Client')
    execPerson = db.relationship(u'Person')
    tissueType = db.relationship(u'rbTissueType')
    unit = db.relationship(u'rbUnit')

    @property
    def barcode_s(self):
        return code128C(self.barcode).decode('windows-1252')


class OrgStructure_HospitalBed(db.Model):
    __tablename__ = u'OrgStructure_HospitalBed'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(16), nullable=False, server_default=u"''")
    name = db.Column(db.String(64), nullable=False, server_default=u"''")
    isPermanentCode = db.Column("isPermanent", db.Integer, nullable=False, server_default=u"'0'")
    type_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedType.id'), index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedProfile.id'), index=True)
    relief = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    schedule_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedSchedule.id'), index=True)
    begDate = db.Column(db.Date)
    endDate = db.Column(db.Date)
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    involution = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    begDateInvolute = db.Column(db.Date)
    endDateInvolute = db.Column(db.Date)

    orgStructure = db.relationship(u'OrgStructure')
    type = db.relationship(u'rbHospitalBedType')
    profile = db.relationship(u'rbHospitalBedProfile')
    schedule = db.relationship(u'rbHospitalBedSchedule')

    def __json__(self):
        return {
            'id': self.id,
            'org_structure_id': self.master_id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'profile': self.profile,
            'schedule': self.schedule
        }

    @property
    def isPermanent(self):
        return self.isPermanentCode == 1


class rbHospitalBedSchedule(db.Model):
    __tablename__ = u'rbHospitalBedSchedule'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbHospitalBedType(db.Model):
    __tablename__ = u'rbHospitalBedType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbHospitalBedProfile(db.Model):
    __tablename__ = u'rbHospitalBedProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)

    # service = db.relationship('rbService')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbOperationType(db.Model):
    __tablename__ = u'rbOperationType'

    id = db.Column(db.Integer, primary_key=True)
    cd_r = db.Column(db.Integer, nullable=False)
    cd_subr = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(8), nullable=False, index=True)
    ktso = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAnalysisStatus(db.Model):
    __tablename__ = u'rbAnalysisStatus'

    id = db.Column(db.Integer, primary_key=True)
    statusName = db.Column(db.String(80), nullable=False, unique=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.statusName,
            'name': self.statusName
        }


class Job(db.Model):
    __tablename__ = u'Job'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    jobType_id = db.Column(db.Integer, db.ForeignKey('rbJobType.id'), nullable=False, index=True)
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    begTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    job_type = db.relationship(u'rbJobType')
    org_structure = db.relationship(u'OrgStructure')

    def __json__(self):
        return {
            'id': self.id,
            'jobType_id': self.jobType_id,
            'org_structure': self.org_structure,
        }


class JobTicket(db.Model):
    __tablename__ = u'Job_Ticket'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('Job.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    datetime = db.Column(db.DateTime, nullable=False)
    resTimestamp = db.Column(db.DateTime)
    resConnectionId = db.Column(db.Integer)
    status = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    begDateTime = db.Column(db.DateTime)
    endDateTime = db.Column(db.DateTime)
    label = db.Column(db.String(64), nullable=False, server_default=u"''")
    note = db.Column(db.String(128), nullable=False, server_default=u"''")

    job = db.relationship(u'Job')

    @property
    def jobType(self):
        return self.job.job_type

    @property
    def orgStructure(self):
        return self.job.org_structure

    def __unicode__(self):
        return u'%s, %s, %s' % (unicode(self.jobType),
                                unicode(self.datetime),
                                unicode(self.orgStructure))

    def __json__(self):
        return {
            'id': self.id,
            'job': self.job,
            'datetime': self.datetime,
            'status': self.status,
            'beg_datetime': self.begDateTime,
            'end_datetime': self.endDateTime,
            'label': self.label,
            'note': self.note,
        }


class rbJobType(db.Model):
    __tablename__ = u'rbJobType'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, index=True)
    code = db.Column(db.String(64), nullable=False)
    regionalCode = db.Column(db.String(64), nullable=False)
    name = db.Column(db.Unicode(128), nullable=False)
    laboratory_id = db.Column(db.Integer, index=True)
    isInstant = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class OrgStructure_ActionType(db.Model):
    __tablename__ = u'OrgStructure_ActionType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), index=True)