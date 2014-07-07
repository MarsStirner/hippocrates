# -*- coding: utf-8 -*-
from application.systemwide import db
from exists import FDRecord

__author__ = 'mmalkov'


class Action(db.Model):
    __tablename__ = u'Action'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
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
    note = db.Column(db.Text, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    office = db.Column(db.String(16), nullable=False)
    amount = db.Column(db.Float(asdecimal=True), nullable=False)
    uet = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    expose = db.Column(db.Boolean, nullable=False, server_default=u"'1'")
    payStatus = db.Column(db.Integer, nullable=False)
    account = db.Column(db.Boolean, nullable=False)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    prescription_id = db.Column(db.Integer, index=True)
    takenTissueJournal_id = db.Column(db.ForeignKey('TakenTissueJournal.id'), index=True)
    contract_id = db.Column(db.Integer, index=True)
    coordDate = db.Column(db.DateTime)
    coordPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    coordAgent = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordInspector = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordText = db.Column(db.String, nullable=False)
    hospitalUidFrom = db.Column(db.String(128), nullable=False, server_default=u"'0'")
    pacientInQueueType = db.Column(db.Integer, server_default=u"'0'")
    AppointmentType = db.Column(
        db.Enum(u'0', u'amb', u'hospital', u'polyclinic', u'diagnostics', u'portal', u'otherLPU'), nullable=False)
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
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), nullable=False, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('ActionPropertyType.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('rbUnit.id'), index=True)
    norm = db.Column(db.String(64), nullable=False)
    isAssigned = db.Column(db.Boolean, nullable=False, server_default=u"'0'")
    evaluation = db.Column(db.Integer)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    action = db.relationship(u'Action')
    type = db.relationship(u'ActionPropertyType', lazy=False, innerjoin=True)
    unit = db.relationship(u'rbUnit', lazy=False)

    @property
    def valueTypeClass(self):
        if self.type.typeName in ["Constructor", u"Жалобы   "]:
            class_name = u'ActionProperty_Text'
        elif self.type.typeName == "AnalysisStatus":
            class_name = u'ActionProperty_Integer'
        elif self.type.typeName == u"Запись в др. ЛПУ":
            class_name = u'ActionProperty_OtherLPURecord'
        elif self.type.typeName == "FlatDirectory":
            class_name = u'ActionProperty_FDRecord'
        else:
            class_name = u'ActionProperty_{}'.format(self.type.typeName)
        return globals().get(class_name)

    @property
    def raw_values_query(self):
        return self.valueTypeClass.query.filter(self.id == self.valueTypeClass.id)


    @property
    def value(self):
        if self.type.isVector:
            return [item.get_value() for item in self.raw_values_query.all()]
        else:
            item = self.raw_values_query.first()
            return item.get_value() if item else None


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

class ActionProperty_Action(db.Model):
    __tablename__ = u'ActionProperty_Action'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        return Action.query.get(self.value) if self.value else None

    property_object = db.relationship('ActionProperty')


class ActionProperty_Date(db.Model):
    __tablename__ = u'ActionProperty_Date'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Date)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_Double(db.Model):
    __tablename__ = u'ActionProperty_Double'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Float(asdecimal=True, decimal_return_scale=2), nullable=False)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_FDRecord(db.Model):
    __tablename__ = u'ActionProperty_FDRecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value = db.Column(db.ForeignKey('FDRecord.id'), nullable=False, index=True)

    FDRecord = db.relationship(u'FDRecord')

    def get_value(self):
        return FDRecord.query.filter(FDRecord.id == self.value).first().get_value(u'Наименование')

    property_object = db.relationship('ActionProperty')


class ActionProperty_HospitalBed(db.Model):
    __tablename__ = u'ActionProperty_HospitalBed'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.ForeignKey('OrgStructure_HospitalBed.id'), index=True)

    ActionProperty = db.relationship(u'ActionProperty')
    hospitalBed = db.relationship(u'OrgStructure_HospitalBed')

    def get_value(self):
        return OrgStructure_HospitalBed.query.filter(OrgStructure_HospitalBed.id == self.value).first()

    property_object = db.relationship('ActionProperty')


class ActionProperty_HospitalBedProfile(db.Model):
    __tablename__ = u'ActionProperty_HospitalBedProfile'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        return rbHospitalBedProfile.query.get(self.value) if self.value else None

    property_object = db.relationship('ActionProperty')


class ActionProperty_Image(db.Model):
    __tablename__ = u'ActionProperty_Image'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.BLOB)

    def get_value(self):
        return None


class ActionProperty_ImageMap(db.Model):
    __tablename__ = u'ActionProperty_ImageMap'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.String)

    def get_value(self):
        return None

    property_object = db.relationship('ActionProperty')


class ActionProperty_Integer(db.Model):
    __tablename__ = u'ActionProperty_Integer'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, nullable=False)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_RLS(ActionProperty_Integer):

    def get_value(self):
        return v_Nomen.query.get(self.value).first() if self.value else None


class ActionProperty_OperationType(ActionProperty_Integer):

    def get_value(self):
        return rbOperationType.query.get(self.value)


class ActionProperty_JobTicket(db.Model):
    __tablename__ = u'ActionProperty_Job_Ticket'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        return JobTicket.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_MKB(db.Model):
    __tablename__ = u'ActionProperty_MKB'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        from exists import MKB
        return MKB.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_OrgStructure(db.Model):
    __tablename__ = u'ActionProperty_OrgStructure'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        from exists import OrgStructure
        return OrgStructure.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_Organisation(db.Model):
    __tablename__ = u'ActionProperty_Organisation'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        from exists import Organisation
        return Organisation.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_OtherLPURecord(db.Model):
    __tablename__ = u'ActionProperty_OtherLPURecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text(collation=u'utf8_unicode_ci'), nullable=False)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_Person(db.Model):
    __tablename__ = u'ActionProperty_Person'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value = db.Column(db.ForeignKey('Person.id'), index=True)

    ActionProperty = db.relationship(u'ActionProperty')
    Person = db.relationship(u'Person')

    def get_value(self):
        from exists import Person
        return Person.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_String(db.Model):
    __tablename__ = u'ActionProperty_String'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text, nullable=False)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_Text(ActionProperty_String):

    def get_value(self):
        # return replace_first_paragraph(convenience_HtmlRip(self.value)) if self.value else ''
        return self.value


class ActionProperty_Html(ActionProperty_String):

    def get_value(self):
        # return convenience_HtmlRip(self.value) if self.value else ''
        return self.value

class ActionProperty_Table(ActionProperty_Integer):

    def get_value(self):
        return {}


class ActionProperty_Time(db.Model):
    __tablename__ = u'ActionProperty_Time'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Time, nullable=False)

    def get_value(self):
        return self.value

    property_object = db.relationship('ActionProperty')


class ActionProperty_ReferenceRb(ActionProperty_Integer):

    def get_value(self):
        domain = ActionProperty.query.get(self.id).type.valueDomain
        table_name = domain.split(';')[0]
        return db.session.query(table_name).get(self.value)


class ActionProperty_rbBloodComponentType(db.Model):
    __tablename__ = u'ActionProperty_rbBloodComponentType'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False)
    value = db.Column(db.Integer, nullable=False)

    def get_value(self):
        return None

    property_object = db.relationship('ActionProperty')


class ActionProperty_rbFinance(db.Model):
    __tablename__ = u'ActionProperty_rbFinance'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        from exists import rbFinance
        return rbFinance.query.get(self.value)

    property_object = db.relationship('ActionProperty')


class ActionProperty_rbReasonOfAbsence(db.Model):
    __tablename__ = u'ActionProperty_rbReasonOfAbsence'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Integer, index=True)

    def get_value(self):
        from exists import rbReasonOfAbsence
        return rbReasonOfAbsence.query.get(self.value)

    property_object = db.relationship('ActionProperty')


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
    jobType_id = db.Column(db.Integer, index=True)
    mnem = db.Column(db.String(32), server_default=u"''")

    service = db.relationship(u'rbService', foreign_keys='ActionType.service_id')
    nomenclatureService = db.relationship(u'rbService', foreign_keys='ActionType.nomenclativeService_id')
    property_types = db.relationship(u'ActionPropertyType', lazy='dynamic')
    group = db.relationship(u'ActionType', remote_side=[id])

    def get_property_type_by_name(self, name):
        return self.property_types.filter(ActionPropertyType.name == name).first()

    def get_property_type_by_code(self, code):
        return self.property_types.filter(ActionPropertyType.code == code).first()

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
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
    note = db.Column(db.String(128), nullable=False)
    barcode = db.Column(db.Integer, nullable=False)
    period = db.Column(db.Integer, nullable=False)

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


class Job(db.Model):
    __tablename__ = u'Job'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
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


class ActionPropertyTypeLayout(db.Model):
    __tablename__ = u'ActionPropertyTypeLayout'

    id = db.Column(db.Integer, primary_key=True)
    actionPropertyType_id = db.Column(db.Integer, db.ForeignKey('ActionPropertyType.id'), nullable=False, index=True)
    template = db.Column(db.UnicodeText, nullable=False)

    type = db.relationship(u'ActionPropertyType', lazy=True, innerjoin=True, backref=db.backref('layout'))