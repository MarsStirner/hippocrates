# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2006-2010 Chuk&Gek and Vista Software. All rights reserved.
##
#############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import *
from library.printing.info.HospitalBedInfo import CHospitalBedInfo

from library.Utils     import *

from ..info.PrintInfo import CInfo, CTemplatableInfoMixin, CInfoList, CInfoProxyList, CDateInfo, CDateTimeInfo, CRBInfo
from ..info.ActionInfo import CActionInfo
from Events.ContractTariffCache import CContractTariffCache
from Events.Service    import CServiceInfo
from Events.Utils      import getMKBName, recordAcceptable
from ..info.OrgInfo import COrgInfo, CClientDocumentInfo, CClientInfo
from ..info.PersonInfo import CSpecialityInfo, CPersonInfo

from library.num_to_text_converter import NumToTextConverter


class CPurposeInfo(CRBInfo):
    tableName = 'rbEventTypePurpose'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)


class CServiceInfo(CRBInfo):
    tableName = 'rbService'

    def _initByRecord(self, record):
        self._eisLegacy = forceBool(record.value('eisLegacy'))
        self._license = forceBool(record.value('license'))
        self._infis = forceString(record.value('infis'))
        self._begDate = CDateInfo(record.value('begDate'))
        self._endDate = CDateInfo(record.value('endDate'))


    def _initByNull(self):
        self._eisLegacy = False
        self._license = False
        self._infis = ''
        self._begDate = CDateInfo()
        self._endDate = CDateInfo()

    eisLegacy   = property(lambda self: self.load()._eisLegacy)
    license     = property(lambda self: self.load()._license)
    infis       = property(lambda self: self.load()._infis)
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)

class CFinanceInfo(CRBInfo):
    tableName = 'rbFinance'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)

class CRequestTypeInfo(CRBInfo):
    tableName = 'rbRequestType'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)

class CEventTypeInfo(CRBInfo):
    tableName = 'EventType'

    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)


    def _initByRecord(self, record):
        self._purpose = self.getInstance(CPurposeInfo, forceRef(record.value('purpose_id')))
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._service = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
        self._requestType = self.getInstance(CRequestTypeInfo, forceRef(record.value('requestType_id')))
        a = record.value('context')
        b = a.type()
        c = a.toString()

        self._printContext = forceString(record.value('context'))


    def _initByNull(self):
        self._purpose = self.getInstance(CPurposeInfo, None)
        self._finance = self.getInstance(CFinanceInfo, None)
        self._service = self.getInstance(CServiceInfo, None)
        self._printContext = ''

    purpose = property(lambda self: self.load()._purpose)
    finance = property(lambda self: self.load()._finance)
    service = property(lambda self: self.load()._service)
    requestType = property(lambda self: self.load()._requestType)
    printContext = property(lambda self: self.load()._printContext)


class CResultInfo(CRBInfo):
    tableName = 'rbResult'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)

    def _initByRecord(self, record):
        self._continued = forceBool(record.value('continued'))
        self._regionalCode = forceString(record.value('regionalCode'))


    def _initByNull(self):
        self._continued = False
        self._regionalCode = ''

    continued = property(lambda self: self.load()._continued)
    regionalCode = property(lambda self: self.load()._regionalCode)

class CAcheResultInfo(CRBInfo):
    tableName = 'rbAcheResult'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)

class CContractInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Contract', '*', self.id)
        if record:
            self._number = forceString(record.value('number'))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._begDate = CDateInfo(forceDate(record.value('begDate')))
            self._endDate = CDateInfo(forceDate(record.value('endDate')))
            self._recipient = self.getInstance(COrgInfo, forceRef(record.value('recipient_id')))
            self._recipientAccount = self.getInstance(COrgAccountInfo, forceRef(record.value('recipientAccount_id')))
            self._recipientKBK = forceString(record.value('recipientKBK'))
            self._payer = self.getInstance(COrgInfo, forceRef(record.value('payer_id')))
            self._payerAccount = self.getInstance(COrgAccountInfo, forceRef(record.value('payerAccount_id')))
            self._payerKBK = forceString(record.value('payerKBK'))
            self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
            return True
        else:
            self._number = ''
            self._date = CDateInfo()
            self._begDate = CDateInfo()
            self._endDate = CDateInfo()
            self._recipient = self.getInstance(COrgInfo, None)
            self._recipientAccount = self.getInstance(CBankInfo, None)
            self._recipientKBK = ''
            self._payer = self.getInstance(COrgInfo, None)
            self._payerAccount = self.getInstance(CBankInfo, None)
            self._payerKBK = ''
            self._finance = self.getInstance(CFinanceInfo, None)
            return False
        
    
    def convertToText(self, num):
        converter = NumToTextConverter(num)
        return converter.convert()


    def __str__(self):
        self.load()
        return self._number + ' ' + self._date

    number           = property(lambda self: self.load()._number)
    date             = property(lambda self: self.load()._date)
    begDate          = property(lambda self: self.load()._begDate)
    endDate          = property(lambda self: self.load()._endDate)
    recipient        = property(lambda self: self.load()._recipient)
    recipientAccount = property(lambda self: self.load()._recipientAccount)
    recipientKBK     = property(lambda self: self.load()._recipientKBK)
    payer            = property(lambda self: self.load()._payer)
    payerAccount     = property(lambda self: self.load()._payerAccount)
    payerKBK         = property(lambda self: self.load()._payerKBK)
    finance          = property(lambda self: self.load()._finance)


class COrgAccountInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Organisation_Account', '*', self.id)
        if record:
            self._org = self.getInstance(COrgInfo, forceRef(record.value('organisation_id')))
            self._bankName = forceString(record.value('bankName'))
            self._name = forceString(record.value('name'))
            self._notes = forceString(record.value('notes'))
            self._bank = self.getInstance(CBankInfo, forceRef(record.value('bank_id')))
            self._cash = forceBool(record.value('cash'))
            return True
        else:
            self._org = self.getInstance(COrgInfo, None)
            self._bankName = ''
            self._name = ''
            self._notes = ''
            self._bank = self.getInstance(CBankInfo, None)
            self._cash = False
            return False


    def __str__(self):
        self.load()
        return self._name

    organisation = property(lambda self: self.load()._org)
    org          = property(lambda self: self.load()._org)
    bankName     = property(lambda self: self.load()._bankName)
    name         = property(lambda self: self.load()._name)
    notes        = property(lambda self: self.load()._notes)
    bank         = property(lambda self: self.load()._bank)
    cash         = property(lambda self: self.load()._cash)


class CBankInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Bank', '*', self.id)
        if record:
            self._BIK = forceString(record.value('BIK'))
            self._name = forceString(record.value('name'))
            self._branchName = forceString(record.value('branchName'))
            self._corrAccount = forceString(record.value('corrAccount'))
            self._subAccount = forceString(record.value('subAccount'))
            return True
        else:
            self._BIK = ''
            self._name = ''
            self._branchName = ''
            self._corrAccount = ''
            self._subAccount = ''
            return False


    def __str__(self):
        self.load()
        return self._name

    BIK        = property(lambda self: self.load()._BIK)
    name       = property(lambda self: self.load()._name)
    branchName = property(lambda self: self.load()._branchName)
    corrAccount= property(lambda self: self.load()._corrAccount)
    subAccount = property(lambda self: self.load()._subAccount)



class CMesSpecificationInfo(CRBInfo):
    tableName = 'rbMesSpecification'
    def __init__(self, context, id):
        CRBInfo.__init__(self, context, id)

    def _initByRecord(self, record):
        self._done = forceBool(record.value('done'))
        self._regionalCode = forceString(record.value('regionalCode'))


    def _initByNull(self):
        self._done = False
        self._regionalCode = ''

    done = property(lambda self: self.load()._done)
    regionalCode = property(lambda self: self.load()._done)



class CMesInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('mes.MES', '*', self.id)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._descr = forceString(record.value('descr'))
            return True
        else:
            self._code = ''
            self._name = ''
            self._descr = ''
            return False


    code  = property(lambda self: self.load()._code)
    name  = property(lambda self: self.load()._name)
    descr = property(lambda self: self.load()._descr)


def getCurrentDepartmentInfo(eventId):
    OSInfo = getOrgStructure(eventId)
    if OSInfo:
        return OSInfo[0]


def departmentManagerId(orgStructure_id):
    managerId = None
    if orgStructure_id:
        orgStructureId = orgStructure_id
        db = QtGui.qApp.db
        query = db.query(
            u"SELECT Person.id from Person, rbPost where orgStructure_id = %s and post_id= rbPost.id and rbPost.flatCode = 'departmentManager'" %
            orgStructureId)
        query.first()
        managerId = forceInt(query.record().value('id'))
    return managerId


class CEventInfo(CInfo, CTemplatableInfoMixin):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._localContract = None
        self._tariffDescr = None

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Event', '*', self.id)
        if record:
            self._eventType = self.getInstance(CEventTypeInfo, forceRef(record.value('eventType_id')))
            self._externalId = forceString(record.value('externalId'))
            self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
            self._orgStructure_id = getCurrentDepartmentInfo(self.id)  # id отделения пребывания
            self._departmentManager = self.getInstance(CPersonInfo, departmentManagerId(self._orgStructure_id))
            self._client = self.getInstance(CClientInfo, forceRef(record.value('client_id')))
            self._contract = self.getInstance(CContractInfo, forceRef(record.value('contract_id')))
            self._prevEventDate = CDateInfo(forceDate(record.value('prevEventDate')))
            self._setDate = CDateTimeInfo(forceDate(record.value('setDate')))
            self._setPerson = self.getInstance(CPersonInfo, forceRef(record.value('setPerson_id')))
            self._execDate = CDateTimeInfo(forceDate(record.value('execDate')))
            self._execPerson = self.getInstance(CPersonInfo, forceRef(record.value('execPerson_id')))
            self._isPrimary = forceInt(record.value('isPrimary')) == 1
            self._order = forceInt(record.value('order'))
            self._result = self.getInstance(CResultInfo, forceRef(record.value('result_id')))
            self._acheResult = self.getInstance(CAcheResultInfo, forceRef(record.value('rbAcheResult_id')))
            self._nextEventDate = CDateInfo(forceDate(record.value('nextEventDate')))
            self._payStatus = forceInt(record.value('payStatus'))
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, forceRef(record.value('typeAsset_id')))
            self._note = forceString(record.value('note'))
            self._curator = self.getInstance(CPersonInfo, forceRef(record.value('curator_id')))
            self._assistant = self.getInstance(CPersonInfo, forceRef(record.value('assistant_id')))
            self._actions = self.getInstance(CActionInfoList, self.id)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, self.id)
            self._visits = self.getInstance(CVisitInfoList, self.id)
            self._localContract = self.getInstance(CEventLocalContractInfo, self.id)
            self._mes = self.getInstance(CMesInfo, forceRef(record.value('MES_id')))
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, forceRef(record.value('mesSpecification_id')))
            self._hospitalBed = self.getInstance(CHospitalBedInfo, self._getHospitalBed_id())
            return True
        else:
            self._eventType = self.getInstance(CEventTypeInfo, None)
            self._externalId = ''
            self._org = self.getInstance(COrgInfo, None)
            self._orgStructure_id = None
            self._departmentManager = self.getInstance(CPersonInfo, None)
            self._client = self.getInstance(CClientInfo, None)
            self._contract = self.getInstance(CContractInfo, None)
            self._prevEventDate = CDateInfo()
            self._setDate = CDateTimeInfo()
            self._setPerson = self.getInstance(CPersonInfo, None)
            self._execDate = CDateTimeInfo()
            self._execPerson = self.getInstance(CPersonInfo, None)
            self._isPrimary = False
            self._order = 0
            self._result = self.getInstance(CResultInfo, None)
            self._acheResult = self.getInstance(CAcheResultInfo, None)
            self._nextEventDate = CDateInfo()
            self._payStatus = 0
            self._typeAsset = self.getInstance(CEmergencyTypeAssetInfo, None)
            self._note = ''
            self._curator = self.getInstance(CPersonInfo, None)
            self._assistant = self.getInstance(CPersonInfo, None)
            self._actions = self.getInstance(CActionInfoList, None)
            self._diagnosises = self.getInstance(CDiagnosticInfoList, None)
            self._visits = self.getInstance(CVisitInfoList, None)
            self._localContract = self.getInstance(CEventLocalContractInfo, None)
            self._mes = self.getInstance(CMesInfo, None)
            self._mesSpecification = self.getInstance(CMesSpecificationInfo, None)
            self._hospitalBed = self.getInstance(CHospitalBedInfo, None)
            return False

    # tariff checker interface
    def getEventTypeId(self):
        return self.eventType.id

    def recordAcceptable(self, record):
        client = self.client
        if client:
            return recordAcceptable(client.sexCode, client.ageTuple, record)
        else:
            return True

    def getTariffDescr(self):
        if not self._tariffDescr:
            contractTariffCache = CContractTariffCache()
            self._tariffDescr = contractTariffCache.getTariffDescr(self.contract.id, self)
        return self._tariffDescr

    def getPrintTemplateContext(self):
        return self.eventType.printContext

    def getData(self):
        return { 'event' : self,
                 'client': self.client,
                 'tempInvalid': None
               }

#    def __unicode__(self):
    def __str__(self):
        self.load()
        return unicode(self._eventType)

    def getTempInvalidList(self, begDate=None, endDate=None, types=None):
        if endDate is None:
            endDate = self.execDate
        if isinstance(endDate, CDateInfo):
            endDate = endDate.date
        if begDate is None:
            begDate = endDate.addMonths(-12)
        elif isinstance(begDate, CDateInfo):
            begDate = begDate.date
        if isinstance(types, (set, frozenset, list, tuple)):
            types = tuple(types)
        elif isinstance(types, (int, long, basestring)):
            types = (types, )
        elif types == None:
            # bang!
            types = (0, )
        else:
            raise ValueError('parameter "types" must be list, tuple, set or int')
        return self.getInstance(CTempInvalidInfoList, self.client._id, pyDate(begDate), pyDate(endDate), types)

    def _getHospitalBed_id(self):
        if not self.id:
            return None
        db = QtGui.qApp.db

        tableAction = db.table('Action')
        tableProperty = db.table('ActionProperty')
        tableActionBed = db.table('ActionProperty_HospitalBed')

        table = tableAction
        table = table.join(tableProperty, tableAction['id'].eq(tableProperty['action_id']))
        table = table.join(tableActionBed, tableProperty['id'].eq(tableActionBed['id']))

        cond = (tableAction['event_id'].eq(self.id),
                tableAction['deleted'].eq(0),)
        record = db.getRecordEx(table, tableActionBed['value'], cond, order='Action.begDate DESC')
        if record:
            return forceRef(record.value(0))
        return None


    eventType   = property(lambda self: self.load()._eventType)
    externalId  = property(lambda self: self.load()._externalId)
    org         = property(lambda self: self.load()._org)
    orgStructure_id = property(lambda self: self.load()._orgStructure_id)
    departmentManager = property(lambda self: self.load()._departmentManager)
    client      = property(lambda self: self.load()._client)
    contract    = property(lambda self: self.load()._contract)
    prevEventDate= property(lambda self: self.load()._prevEventDate)
    setDate     = property(lambda self: self.load()._setDate)
    setPerson   = property(lambda self: self.load()._setPerson)
    execDate    = property(lambda self: self.load()._execDate)
    execPerson  = property(lambda self: self.load()._execPerson)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    order       = property(lambda self: self.load()._order)
    result      = property(lambda self: self.load()._result)
    acheResult  = property(lambda self: self.load()._acheResult)
    nextEventDate= property(lambda self: self.load()._nextEventDate)
    payStatus   = property(lambda self: self.load()._payStatus)
    typeAsset   = property(lambda self: self.load()._typeAsset)
    notes       = property(lambda self: self.load()._note)
    curator     = property(lambda self: self.load()._curator)
    assistant   = property(lambda self: self.load()._assistant)
    finance     = property(lambda self: self.contract.finance)
    actions     = property(lambda self: self.load()._actions)
    diagnosises = property(lambda self: self.load()._diagnosises)
    visits      = property(lambda self: self.load()._visits)
    localContract = property(lambda self: self.load()._localContract)
    mes         = property(lambda self: self.load()._mes)
    mesSpecification = property(lambda self: self.load()._mesSpecification)
    hospitalBed = property(lambda self: self.load()._hospitalBed)


class CEmergencyEventInfo(CEventInfo):
    def __init__(self, context, id):
        CEventInfo.__init__(self, context)

    def _load(self):
        db = QtGui.qApp.db
        if CEventInfo._load():
            recordEmergency = db.getRecordEx('EmergencyCall', '*', table['event_id'].eq(self.id))
        else:
            recordEmergency = None
        if recordEmergency:
            self._numberCardCall = forceString(recordEmergency.value('numberCardCall'))
            self._brigade = self.getInstance(CEmergencyBrigadeInfo, forceRef(recordEmergency.value('brigade_id')))
            self._causeCall = self.getInstance(CEmergencyCauseCallInfo, forceRef(recordEmergency.value('causeCall_id')))
            self._whoCallOnPhone = forceString(recordEmergency.value('whoCallOnPhone'))
            self._numberPhone = forceString(recordEmergency.value('numberPhone'))
            if getEventShowTime(self._eventType.id):
                self._begDate = CDateTimeInfo(forceDate(recordEmergency.value('begDate')))
                self._passDate = CDateTimeInfo(forceDate(recordEmergency.value('passDate')))
                self._departureDate = CDateTimeInfo(forceDate(recordEmergency.value('departureDate')))
                self._arrivalDate = CDateTimeInfo(forceDate(recordEmergency.value('arrivalDate')))
                self._finishServiceDate = CDateTimeInfo(forceDate(recordEmergency.value('finishServiceDate')))
                self._endDate = CDateTimeInfo(forceDate(recordEmergency.value('endDate')))
            else:
                self._begDate = CDateInfo(forceDate(recordEmergency.value('begDate')))
                self._passDate = CDateInfo(forceDate(recordEmergency.value('passDate')))
                self._departureDate = CDateInfo(forceDate(recordEmergency.value('departureDate')))
                self._arrivalDate = CDateInfo(forceDate(recordEmergency.value('arrivalDate')))
                self._finishServiceDate = CDateInfo(forceDate(recordEmergency.value('finishServiceDate')))
                self._endDate = CDateInfo(forceDate(recordEmergency.value('endDate')))

            self._placeReceptionCall = self.getInstance(CEmergencyPlaceReceptionCallInfo, forceRef(recordEmergency.value('placeReceptionCall_id')))
            self._receivedCall = self.getInstance(CEmergencyReceivedCallInfo, forceRef(recordEmergency.value('receivedCall_id')))
            self._reasondDelays = self.getInstance(CEmergencyReasondDelaysInfo, forceRef(recordEmergency.value('reasondDelays_id')))
            self._resultCall = self.getInstance(CEmergencyResultInfo, forceRef(recordEmergency.value('resultCall_id')))
            self._accident = self.getInstance(CEmergencyAccidentInfo, forceRef(recordEmergency.value('accident_id')))
            self._death = self.getInstance(CEmergencyDeathInfo, forceRef(recordEmergency.value('death_id')))
            self._ebriety = self.getInstance(CEmergencyEbrietyInfo, forceRef(recordEmergency.value('ebriety_id')))
            self._diseased = self.getInstance(CEmergencyDiseasedInfo, forceRef(recordEmergency.value('diseased_id')))
            self._placeCall = self.getInstance(CEmergencyPlaceCallInfo, forceRef(recordEmergency.value('placeCall_id')))
            self._methodTransport = self.getInstance(CEmergencyMethodTransportInfo, forceRef(recordEmergency.value('methodTransport_id')))
            self._transfTransport = self.getInstance(CEmergencyTransferTransportInfo, forceRef(recordEmergency.value('transfTransport_id')))
            self._renunOfHospital = forceInt(recordEmergency.value('renunOfHospital'))
            self._faceRenunOfHospital = forceString(recordEmergency.value('faceRenunOfHospital'))
            self._disease = forceInt(recordEmergency.value('disease'))
            self._birth = forceInt(recordEmergency.value('birth'))
            self._pregnancyFailure = forceInt(recordEmergency.value('pregnancyFailure'))
            self._noteCall = forceString(recordEmergency.value('noteCall'))
            return True
        else:
            self._numberCardCall = ''
            self._brigade = self.getInstance(CEmergencyBrigadeInfo, None)
            self._causeCall = self.getInstance(CEmergencyCauseCallInfo, None)
            self._whoCallOnPhone = ''
            self._numberPhone = ''
            self._begDate = CDateTimeInfo()
            self._passDate = CDateTimeInfo()
            self._departureDate = CDateTimeInfo()
            self._arrivalDate = CDateTimeInfo()
            self._finishServiceDate = CDateTimeInfo()
            self._endDate = CDateTimeInfo()
            self._placeReceptionCall = self.getInstance(CEmergencyPlaceReceptionCallInfo, None)
            self._receivedCall = self.getInstance(CEmergencyReceivedCallInfo, None)
            self._reasondDelays = self.getInstance(CEmergencyReasondDelaysInfo, None)
            self._resultCall = self.getInstance(CEmergencyResultInfo, None)
            self._accident = self.getInstance(CEmergencyAccidentInfo, None)
            self._death = self.getInstance(CEmergencyDeathInfo, None)
            self._ebriety = self.getInstance(CEmergencyEbrietyInfo, None)
            self._diseased = self.getInstance(CEmergencyDiseasedInfo, None)
            self._placeCall = self.getInstance(CEmergencyPlaceCallInfo, None)
            self._methodTransport = self.getInstance(CEmergencyMethodTransportInfo, None)
            self._transfTransport = self.getInstance(CEmergencyTransferTransportInfo, None)
            self._renunOfHospital = 0
            self._faceRenunOfHospital = ''
            self._disease = 0
            self._birth = 0
            self._pregnancyFailure = 0
            self._noteCall = ''
            return False

    numberCardCall      = property(lambda self: self.load()._numberCardCall)
    brigade             = property(lambda self: self.load()._brigade)
    causeCall           = property(lambda self: self.load()._causeCall)
    whoCallOnPhone      = property(lambda self: self.load()._whoCallOnPhone)
    numberPhone         = property(lambda self: self.load()._numberPhone)
    begDate             = property(lambda self: self.load()._begDate)
    passDate            = property(lambda self: self.load()._passDate)
    departureDate       = property(lambda self: self.load()._departureDate)
    arrivalDate         = property(lambda self: self.load()._arrivalDate)
    finishServiceDate   = property(lambda self: self.load()._finishServiceDate)
    endDate             = property(lambda self: self.load()._endDate)
    placeReceptionCall  = property(lambda self: self.load()._placeReceptionCall)
    receivedCall        = property(lambda self: self.load()._receivedCall)
    reasondDelays       = property(lambda self: self.load()._reasondDelays)
    resultCall          = property(lambda self: self.load()._resultCall)
    accident            = property(lambda self: self.load()._accident)
    death               = property(lambda self: self.load()._death)
    ebriety             = property(lambda self: self.load()._ebriety)
    diseased            = property(lambda self: self.load()._diseased)
    placeCall           = property(lambda self: self.load()._placeCall)
    methodTransport     = property(lambda self: self.load()._methodTransport)
    transfTransport     = property(lambda self: self.load()._transfTransport)
    renunOfHospital     = property(lambda self: self.load()._renunOfHospital)
    faceRenunOfHospital = property(lambda self: self.load()._faceRenunOfHospital)
    disease             = property(lambda self: self.load()._disease)
    birth               = property(lambda self: self.load()._birth)
    pregnancyFailure    = property(lambda self: self.load()._pregnancyFailure)
    noteCall            = property(lambda self: self.load()._noteCall)


class CEventLocalContractInfo(CInfo):
    def __init__(self, context, eventId):
        CInfo.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_LocalContract')
        record = db.getRecordEx(table, '*', [table['master_id'].eq(self.eventId),
                                             table['deleted'].eq(0)
                                            ]) if self.eventId else None
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByNone()
            return False


    def initByRecord(self, record):
        self._coordDate = CDateInfo(forceDate(record.value('coordDate')))
        self._coordAgent = forceString(record.value('coordAgent'))
        self._coordInspector = forceString(record.value('coordInspector'))
        self._coordText = forceString(record.value('coordText'))
        self._date   = CDateInfo(forceDate(record.value('dateContract')))
        self._number = forceString(record.value('numberContract'))
        self._sumLimit = forceDouble(record.value('sumLimit'))
        self._org = self.getInstance(COrgInfo, forceRef(record.value('org_id')))
        self._lastName = forceString(record.value('lastName'))
        self._firstName = forceString(record.value('firstName'))
        self._patrName = forceString(record.value('patrName'))
        self._birthDate = CDateInfo(forceDate(record.value('birthDate')))
        self._document = self.getInstance(CClientDocumentInfo)
        self._document._documentType = forceString(QtGui.qApp.db.translate('rbDocumentType', 'id', record.value('documentType_id'), 'name'))
        self._document._serial = forceStringEx(record.value('serialLeft'))+' '+forceStringEx(record.value('serialRight'))
        self._document._number = forceString(record.value('number'))
        self._document._date = CDateInfo()
        self._document._origin = ''
        self._document._ok = True
        self._document._loaded = True
        self._address = forceString(record.value('regAddress'))
        self._loaded = True
        self._ok = True


    def initByNone(self):
        self._coordDate = CDateInfo()
        self._coordAgent = ''
        self._coordInspector = ''
        self._coordText = ''
        self._date   = CDateInfo()
        self._number = ''
        self._sumLimit = 0
        self._org = self.getInstance(COrgInfo, None)
        self._lastName = ''
        self._firstName = ''
        self._patrName = ''
        self._birthDate = CDateInfo()
        self._sex = ''
        self._document = self.getInstance(CClientDocumentInfo)
        self._address = ''
        self._loaded = True
        self._ok = False

    coordDate   = property(lambda self: self.load()._coordDate)
    coordAgent  = property(lambda self: self.load()._coordAgent)
    coordInspector = property(lambda self: self.load()._coordInspector)
    coordText   = property(lambda self: self.load()._coordText)
    date        = property(lambda self: self.load()._date)
    number      = property(lambda self: self.load()._number)
    sumLimit    = property(lambda self: self.load()._sumLimit)
    lastName    = property(lambda self: self.load()._lastName)
    firstName   = property(lambda self: self.load()._firstName)
    patrName    = property(lambda self: self.load()._patrName)
    birthDate   = property(lambda self: self.load()._birthDate)
    document    = property(lambda self: self.load()._document)
    address     = property(lambda self: self.load()._address)
    org         = property(lambda self: self.load()._org)

    def __str__(self):
        if self.load():
            parts = []
            if self._coordDate:
                parts.append(u'согласовано ' + self._coordDate)
            if self._coordText:
                parts.append(self._coordText)
            if self._number:
                parts.append(u'№ ' + self._number)
            if self._date:
                parts.append(u'от ' + forceString(self._date))
            if self._org:
                parts.append(unicode(self._org))
            else:
                parts.append(self._lastName)
                parts.append(self._firstName)
                parts.append(self._patrName)
            return ' '.join(parts)
        else:
            return ''


class CActionInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Action')
        self._idList = db.getIdList(table, 'id', table['event_id'].eq(self.eventId), 'id')
        self._items = [ self.getInstance(CActionInfo, id) for id in self._idList ]
        return True
        
    def index(self, action):
        return self.load()._idList.index(action.id)


class CDagnosisTypeInfo(CRBInfo):
    tableName = 'rbDiagnosisType'


class CCharacterInfo(CRBInfo):
    tableName = 'rbDiseaseCharacter'


class CStageInfo(CRBInfo):
    tableName = 'rbDiseaseStage'


class CDispanserInfo(CRBInfo):
    tableName = 'rbDispanser'

    def _initByRecord(self, record):
        self._observed = forceBool(record.value('observed'))


    def _initByNull(self):
        self._observed = False


    observed = property(lambda self: self.load()._observed)


class CHospitalInfo(CInfo):
    names = [u'не требуется', u'требуется', u'направлен', u'пролечен']

    def __init__(self, context, code):
        CInfo.__init__(self, context)
        self.code = code
        self.name = self.names[code] if 0<=code<len(self.names) else ('{%s}' % code)
        self._ok = True
        self._loaded = True

    def __str__(self):
        return self.name


class CTraumaTypeInfo(CRBInfo):
    tableName = 'rbTraumaType'


class CHealthGroupInfo(CRBInfo):
    tableName = 'rbHealthGroup'


class CMKBInfo(CInfo):
    def __init__(self, context, code):
        CInfo.__init__(self, context)
        self.code = code
        self._descr = None
        self._ok = bool(self.code)
        self._loaded = True

    def _descr(self):
        if self._descr is None:
            self._descr = getMKBName(self.code) if self.code else ''
        return self._descr

    descr = property(_descr)

    def __str__(self):
        return self.code


class CDiagnosticInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis = db.table('Diagnosis')
        record = db.getRecord(tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id'])),
                              'Diagnostic.*, Diagnosis.MKB, Diagnosis.MKBEx',
                              self.id)
        if record:
            self.initByRecord(record)
            return True
        else:
            self._type = self.getInstance(CDagnosisTypeInfo, None)
            self._MKB = self.getInstance(CMKBInfo, '')
            self._MKBEx = self.getInstance(CMKBInfo, '')
            self._character = self.getInstance(CCharacterInfo, None)
            self._stage = self.getInstance(CStageInfo, None)
            self._dispanser = self.getInstance(CDispanserInfo, None)
            self._sanatorium = self.getInstance(CHospitalInfo, 0)
            self._hospital = self.getInstance(CHospitalInfo, 0)
            self._traumaType = self.getInstance(CTraumaTypeInfo, None)
            self._speciality = self.getInstance(CSpecialityInfo, None)
            self._person = self.getInstance(CPersonInfo, None)
            self._healthGroup = self.getInstance(CHealthGroupInfo, None)
            self._result = self.getInstance(CResultInfo, None)
            self._setDate = CDateInfo()
            self._endDate = CDateInfo()
            self._notes = ''
            return False


    def initByRecord(self, record):
        self._type = self.getInstance(CDagnosisTypeInfo, forceRef(record.value('diagnosisType_id')))
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._MKBEx = self.getInstance(CMKBInfo, forceString(record.value('MKBEx')))
        self._character = self.getInstance(CCharacterInfo, forceRef(record.value('character_id')))
        self._stage = self.getInstance(CStageInfo, forceRef(record.value('stage_id')))
        self._dispanser = self.getInstance(CDispanserInfo, forceRef(record.value('dispanser_id')))
        self._sanatorium = self.getInstance(CHospitalInfo, forceInt(record.value('sanatorium')))
        self._hospital = self.getInstance(CHospitalInfo, forceInt(record.value('hospital')))
        self._traumaType = self.getInstance(CTraumaTypeInfo, forceRef(record.value('traumaType_id')))
        self._speciality = self.getInstance(CSpecialityInfo, forceRef(record.value('speciality_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._healthGroup = self.getInstance(CHealthGroupInfo, forceRef(record.value('healthGroup_id')))
        self._result = self.getInstance(CResultInfo, forceRef(record.value('result_id')))
        self._setDate = CDateInfo(forceDate(record.value('setDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._notes = forceString(record.value('notes'))
        self._loaded = True
        self._ok = True


    type        = property(lambda self: self.load()._type)
    MKB         = property(lambda self: self.load()._MKB)
    MKBEx       = property(lambda self: self.load()._MKBEx)
    character   = property(lambda self: self.load()._character)
    stage       = property(lambda self: self.load()._stage)
    dispanser   = property(lambda self: self.load()._dispanser)
    sanatorium  = property(lambda self: self.load()._sanatorium)
    hospital    = property(lambda self: self.load()._hospital)
    traumaType  = property(lambda self: self.load()._traumaType)
    speciality  = property(lambda self: self.load()._speciality)
    person      = property(lambda self: self.load()._person)
    healthGroup = property(lambda self: self.load()._healthGroup)
    result      = property(lambda self: self.load()._result)
    setDate     = property(lambda self: self.load()._setDate)
    endDate     = property(lambda self: self.load()._endDate)
    notes       = property(lambda self: self.load()._notes)



class CDiagnosticInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        idList = db.getIdList(table, 'id', table['event_id'].eq(self.eventId), 'id')
        self._items = [ self.getInstance(CDiagnosticInfo, id) for id in idList ]
        return True


class CDiagnosisInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnosis')
        record = db.getRecord(table, '*', self.id)
        if record:
            self.initByRecord(record)
            return True
        else:
            self._type = self.getInstance(CDagnosisTypeInfo, None)
            self._MKB = self.getInstance(CMKBInfo, '')
            self._MKBEx = self.getInstance(CMKBInfo, '')
            self._character = self.getInstance(CCharacterInfo, None)
            self._dispanser = self.getInstance(CDispanserInfo, None)
            self._traumaType = self.getInstance(CTraumaTypeInfo, None)
            self._person = self.getInstance(CPersonInfo, None)
            self._setDate = CDateInfo()
            self._endDate = CDateInfo()
            return False


    def initByRecord(self, record):
        self._type = self.getInstance(CDagnosisTypeInfo, forceRef(record.value('diagnosisType_id')))
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._MKBEx = self.getInstance(CMKBInfo, forceString(record.value('MKBEx')))
        self._character = self.getInstance(CCharacterInfo, forceRef(record.value('character_id')))
        self._dispanser = self.getInstance(CDispanserInfo, forceRef(record.value('dispanser_id')))
        self._traumaType = self.getInstance(CTraumaTypeInfo, forceRef(record.value('traumaType_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._setDate = CDateInfo(forceDate(record.value('setDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._loaded = True
        self._ok = True

    type        = property(lambda self: self.load()._type)
    MKB         = property(lambda self: self.load()._MKB)
    MKBEx       = property(lambda self: self.load()._MKBEx)
    character   = property(lambda self: self.load()._character)
    dispanser   = property(lambda self: self.load()._dispanser)
    traumaType  = property(lambda self: self.load()._traumaType)
    person      = property(lambda self: self.load()._person)
#    healthGroup = property(lambda self: self.load()._healthGroup)
    setDate     = property(lambda self: self.load()._setDate)
    endDate     = property(lambda self: self.load()._endDate)


class CDiagnosisInfoList(CInfoList):
    def __init__(self, context, clientId):
        CInfoList.__init__(self, context)
        self.clientId = clientId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Diagnosis')
        idList = db.getIdList(table,
                              'id',
                              [table['client_id'].eq(self.clientId), table['deleted'].eq(0), table['mod_id'].isNull()],
                              'endDate')
        self._items = [ self.getInstance(CDiagnosisInfo, id) for id in idList ]
        return True


class CSceneInfo(CRBInfo):
    tableName = 'rbScene'



class CVisitTypeInfo(CRBInfo):
    tableName = 'rbVisitType'



class CVisitInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('Visit', '*', self.id)
        if record:
            self.initByRecord(record)
            return True
        else:
            self._scene = self.getInstance(CSceneInfo, None)
            self._date = CDateInfo()
            self._type = self.getInstance(CVisitTypeInfo, None)
            self._person = self.getInstance(CPersonInfo, None)
            self._isPrimary = forceBool(record.value('isPrimary'))
            self._finance = self.getInstance(CFinanceInfo, None)
            self._service = self.getInstance(CServiceInfo, None)
            self._payStatus = 0
            return False

    def initByRecord(self, record):
        self._scene = self.getInstance(CSceneInfo, forceRef(record.value('scene_id')))
        self._date = CDateInfo(forceDate(record.value('date')))
        self._type = self.getInstance(CVisitTypeInfo, forceRef(record.value('visitType_id')))
        self._person = self.getInstance(CPersonInfo, forceRef(record.value('person_id')))
        self._isPrimary = forceBool(record.value('isPrimary'))
        self._finance = self.getInstance(CFinanceInfo, forceRef(record.value('finance_id')))
        self._service = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
        self._payStatus = forceInt(record.value('payStatus'))
        self._loaded = True
        self._ok = True

    scene       = property(lambda self: self.load()._scene)
    date        = property(lambda self: self.load()._date)
    type        = property(lambda self: self.load()._type)
    person      = property(lambda self: self.load()._person)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    finance     = property(lambda self: self.load()._finance)
    service     = property(lambda self: self.load()._service)
    payStatus   = property(lambda self: self.load()._payStatus)



class CVisitInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Visit')
        idList = db.getIdList(table, 'id', table['event_id'].eq(self.eventId), 'id')
        self._items = [ self.getInstance(CVisitInfo, id) for id in idList ]
        return True


class CTempInvalidRegimeInfo(CRBInfo):
    tableName = 'rbTempInvalidRegime'


class CTempInvalidBreakInfo(CRBInfo):
    tableName = 'rbTempInvalidBreak'


class CTempInvalidResultInfo(CRBInfo):
    tableName = 'rbTempInvalidResult'


class CTempInvalidPeriodInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._begPerson = None
        self._begDate = CDateInfo()
        self._endPerson = None
        self._endDate = CDateInfo()
        self._isExternal = None
        self._regime = None
        self._break = None
        self._result = None
        self._note = ''
#        self._MKB     = ''
#        self._MKBEx   = ''


    def _load(self):
        if self.id:
            db = QtGui.qApp.db
            table = db.table('TempInvalid_Period')
#            tableDiagnosis = db.table('Diagnosis')
#            tableEx = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(table['diagnosis_id']))
#            record = db.getRecordEx(tableEx, 'TempInvalid.*, Diagnosis.MKB, Diagnosis.MKBEx', table['id'].eq(self.id))
            record = db.getRecordEx(table, '*', table['id'].eq(self.id))
            if record:
                self.initByRecord(record)
                return True
        return False


    def initByRecord(self, record):
        self._begPerson  = self.getInstance(CPersonInfo, forceRef(record.value('begPerson_id')))
        self._begDate    = CDateInfo(forceDate(record.value('begDate')))
        self._endPerson  = self.getInstance(CPersonInfo, forceRef(record.value('endPerson_id')))
        self._endDate    = CDateInfo(forceDate(record.value('endDate')))
        self._isExternal = forceBool(record.value('isExternal'))
        self._regime     = self.getInstance(CTempInvalidRegimeInfo, forceRef(record.value('regime_id')))
        self._break      = self.getInstance(CTempInvalidBreakInfo, forceRef(record.value('break_id')))
        self._result     = self.getInstance(CTempInvalidResultInfo, forceRef(record.value('result_id')))
#        self._MKB        = forceString(record.value('MKB'))
#        self._MKBEx      = forceString(record.value('MKBEx'))


    begPerson   = property(lambda self: self.load()._begPerson)
    begDate     = property(lambda self: self.load()._begDate)
    endPerson   = property(lambda self: self.load()._endPerson)
    endDate     = property(lambda self: self.load()._endDate)
    isExternal  = property(lambda self: self.load()._isExternal)
    regime      = property(lambda self: self.load()._regime)
    break_      = property(lambda self: self.load()._break)
    result      = property(lambda self: self.load()._result)
#    MKB         = property(lambda self: self.load()._MKB)
#    MKBEx       = property(lambda self: self.load()._MKBEx)


class CTempInvalidPeriodInfoList(CInfoList):
    def __init__(self, context, tempInvalidId):
        CInfoList.__init__(self, context)
        self.tempInvalidId = tempInvalidId


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('TempInvalid_Period')
        stmt = db.selectStmt(table, where=table['master_id'].eq(self.tempInvalidId), order='begDate, id')
        result = db.query(stmt)
        while result.next():
            record = result.record()
            id = forceRef(record.value('id'))
            item = self.getInstance(CTempInvalidPeriodInfo, id)
            item.initByRecord(record)
            self._items.append(item)
        return True


class CTempInvalidInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self._type    = None
        self._doctype = context.getInstance(CTempInvalidDocTypeInfo, None)
        self._reason  = context.getInstance(CTempInvalidReasonInfo, None)
        self._serial  = ''
        self._number  = ''
        self._sex     = ''
        self._age     = ''
        self._duration = 0
        self._externalDuration = 0
        self._begDate = CDateInfo()
        self._endDate = CDateInfo()
        self._closed = 0
        self._MKB   = ''
        self._MKBEx = ''
        self._periods = []


    def _load(self):
        if self.id:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            tableDiagnosis = db.table('Diagnosis')
            tableEx = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(table['diagnosis_id']))
            record = db.getRecordEx(tableEx, 'TempInvalid.*, Diagnosis.MKB, Diagnosis.MKBEx', table['id'].eq(self.id))
            if record:
                self.initByRecord(record)
                return True
        return False


    def initByRecord(self, record):
        self._type    = forceInt(record.value('type'))
        self._doctype = self.getInstance(CTempInvalidDocTypeInfo, forceRef(record.value('doctype_id')))
        self._reason  = self.getInstance(CTempInvalidReasonInfo,  forceRef(record.value('tempInvalidReason_id')))
        self._serial  = forceString(record.value('serial'))
        self._number  = forceString(record.value('number'))
        self._sex     = formatSex(forceInt(record.value('sex')))
        self._age     = forceInt(record.value('age'))
        self._duration= forceInt(record.value('duration'))
        self._externalDuration = 0
        self._begDate = CDateInfo(forceDate(record.value('begDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._closed  = forceInt(record.value('closed'))
        self._MKB     = forceString(record.value('MKB'))
        self._MKBEx   = forceString(record.value('MKBEx'))
        self._periods = self.getInstance(CTempInvalidPeriodInfoList, self.id)
    
    @property
    def care(self):
        # Чекбокс "По уходу за больным"
        return self.load().reason.code == '09'


    type        = property(lambda self: self.load()._type)
    doctype     = property(lambda self: self.load()._doctype)
    reason      = property(lambda self: self.load()._reason)
    serial      = property(lambda self: self.load()._serial)
    number      = property(lambda self: self.load()._number)
    sex         = property(lambda self: self.load()._sex)
    age         = property(lambda self: self.load()._age)
    duration    = property(lambda self: self.load()._duration)
    externalDuration = property(lambda self: self.load()._externalDuration)
    begDate     = property(lambda self: self.load()._begDate)
    endDate     = property(lambda self: self.load()._endDate)
    MKB         = property(lambda self: self.load()._MKB)
    MKBEx       = property(lambda self: self.load()._MKBEx)
    periods     = property(lambda self: self.load()._periods)
    closed      = property(lambda self: self.load()._closed)


class CTempInvalidDocTypeInfo(CRBInfo):
    tableName = 'rbTempInvalidDocument'


class CTempInvalidReasonInfo(CRBInfo):
    tableName = 'rbTempInvalidReason'

    def _initByRecord(self, record):
        self._grouping = forceInt(record.value('grouping'))


    def _initByNull(self):
        self._grouping = None

    grouping = property(lambda self: self.load()._grouping)



class CTempInvalidInfoList(CInfoList):
    def __init__(self, context, clientId, begDate, endDate, types=(0)):
        CInfoList.__init__(self, context)
        self.clientId = clientId
        self.begDate  = QDate(begDate) if begDate else None
        self.endDate  = QDate(endDate) if endDate else None
        self.types    = types
        self._idList = []


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('TempInvalid')
        cond = [ table['client_id'].eq(self.clientId),
                 table['deleted'].eq(0),
                 table['type'].inlist(self.types)]
        if self.begDate:
            cond.append(table['endDate'].ge(self.begDate))
        if self.endDate:
            cond.append(table['begDate'].le(self.endDate))
        self._idList = db.getIdList(table, 'id', cond, 'begDate')
        self._items = [ self.getInstance(CTempInvalidInfo, id) for id in self._idList ]
        return True


class CDiagnosticInfoProxyList(CInfoProxyList):
    def __init__(self, context, models):
        CInfoProxyList.__init__(self, context)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        self._items = [ None ] * len(self._rawItems)

    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            record = self._rawItems[key]
            v = self.getInstance(CDiagnosticInfo, 'tmp_%d'%key)
            v.initByRecord(record)
            self._items[key] = v
        return v


class CVisitInfoProxyList(CInfoProxyList):
    def __init__(self, context, modelVisits):
        CInfoProxyList.__init__(self, context)
        self._items = [ None ] * len(modelVisits.items())
        self.model = modelVisits


    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            record = self.model.items()[key]
            v = self.getInstance(CVisitInfo, 'tmp_%d'%key)
            v.initByRecord(record)
            self._items[key] = v
        return v


class CVisitPersonallInfo(CInfo):
    def __init__(self, context, item = []):
        CInfo.__init__(self, context)
        self.item = item


    def _load(self):
        if self.item != []:
            self._scene = self.getInstance(CSceneInfo, self.item[0])
            self._date = CDateTimeInfo(self.item[1])
            self._type = self.getInstance(CVisitTypeInfo, self.item[2])
            self._person = self.getInstance(CPersonInfo, self.item[3])
            self._isPrimary = forceBool(self.item[4])
            self._finance = self.getInstance(CFinanceInfo, self.item[5])
            self._service = self.getInstance(CServiceInfo, self.item[6])
            self._payStatus = self.item[7]


    scene       = property(lambda self: self.load()._scene)
    date        = property(lambda self: self.load()._date)
    type        = property(lambda self: self.load()._type)
    person      = property(lambda self: self.load()._person)
    isPrimary   = property(lambda self: self.load()._isPrimary)
    finance     = property(lambda self: self.load()._finance)
    service     = property(lambda self: self.load()._service)
    payStatus   = property(lambda self: self.load()._payStatus)


class CEmergencyBrigadeInfo(CInfo):
    def __init__(self, context, brigadeId):
        CInfo.__init__(self, context)
        self.brigadeId = brigadeId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('EmergencyBrigade', '*', self.brigadeId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyCauseCallInfo(CInfo):
    def __init__(self, context, causeCallId):
        CInfo.__init__(self, context)
        self.causeCallId = causeCallId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyCauseCall', '*', self.causeCallId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyTransferTransportInfo(CInfo):
    def __init__(self, context, transfTranspId):
        CInfo.__init__(self, context)
        self.transfTranspId = transfTranspId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyTransferredTransportation', '*', self.transfTranspId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyPlaceReceptionCallInfo(CInfo):
    def __init__(self, context, placeReceptionCallId):
        CInfo.__init__(self, context)
        self.placeReceptionCallId = placeReceptionCallId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyPlaceReceptionCall', '*', self.placeReceptionCallId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyReceivedCallInfo(CInfo):
    def __init__(self, context, receivedCallId):
        CInfo.__init__(self, context)
        self.receivedCallId = receivedCallId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyReceivedCall', '*', self.receivedCallId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyReasondDelaysInfo(CInfo):
    def __init__(self, context, emergencyReasondDelaysId):
        CInfo.__init__(self, context)
        self.emergencyReasondDelaysId = emergencyReasondDelaysId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyReasondDelays', '*', self.emergencyReasondDelaysId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyResultInfo(CInfo):
    def __init__(self, context, emergencyResultId):
        CInfo.__init__(self, context)
        self.emergencyResultId = emergencyResultId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyResult', '*', self.emergencyResultId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyAccidentInfo(CInfo):
    def __init__(self, context, accidentId):
        CInfo.__init__(self, context)
        self.accidentId = accidentId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyAccident', '*', self.accidentId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyDeathInfo(CInfo):
    def __init__(self, context, emergencyDeathId):
        CInfo.__init__(self, context)
        self.emergencyDeathId = emergencyDeathId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyDeath', '*', self.emergencyDeathId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyEbrietyInfo(CInfo):
    def __init__(self, context, ebrietyId):
        CInfo.__init__(self, context)
        self.ebrietyId = ebrietyId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyEbriety', '*', self.ebrietyId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyDiseasedInfo(CInfo):
    def __init__(self, context, emergencyDiseasedId):
        CInfo.__init__(self, context)
        self.emergencyDiseasedId = emergencyDiseasedId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyDiseased', '*', self.emergencyDiseasedId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyPlaceCallInfo(CInfo):
    def __init__(self, context, placeCallId):
        CInfo.__init__(self, context)
        self.placeCallId = placeCallId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyPlaceCall', '*', self.placeCallId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyMethodTransportInfo(CInfo):
    def __init__(self, context, methodTransportId):
        CInfo.__init__(self, context)
        self.methodTransportId = methodTransportId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyMethodTransportation', '*', self.methodTransportId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CEmergencyTypeAssetInfo(CInfo):
    def __init__(self, context, typeAssetId):
        CInfo.__init__(self, context)
        self.typeAssetId = typeAssetId
        self._code = ''
        self._name = ''
        self._regionalCode = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord('rbEmergencyTypeAsset', '*', self.typeAssetId)
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._regionalCode = forceString(record.value('regionalCode'))
            return True
        else:
            return False


    def __str__(self):
        return self.load()._name

    code     = property(lambda self: self.load()._code)
    name     = property(lambda self: self.load()._name)
    regionalCode = property(lambda self: self.load()._regionalCode)


class CCashOperationInfo(CRBInfo):
    tableName = 'rbCashOperation'


def getEventInfo(action, context):
    """
    Получение информации об обращении, используется при печати
    """
    from library.printing.info.ActionInfo import CActionInfoProxyListEx
    from EventEditor.DiagnosisModel import CPrelimDiagnosisModel, CFinalDiagnosisModel
    event = action.Event
    result = context.getInstance(CEventInfo, event.id)
    # ручная инициализация свойств
    date = action.endDate.date() if action.endDate else QDate.currentDate()
    db = QtGui.qApp.db
    if event:
        result._eventType = context.getInstance(CEventTypeInfo, event.eventType_id)
        result._externalId = event.externalId
        if event.org_id is not None:
            result._org = context.getInstance(COrgInfo, event.org_id)
        result._client = context.getInstance(CClientInfo, event.client_id, date)
        if event.contract_id is not None:
            result._contract = context.getInstance(CContractInfo, event.contract_id)
            result._localContract = context.getInstance(CEventLocalContractInfo, event.id)
            result._localContract.initByRecord(db.getRecord(db.table('Contract'), '*', event.contract_id))

        result._prevEventDate = CDateInfo(event.prevEventDate)
        result._setDate = CDateInfo(action.begDate)
        result._setPerson = context.getInstance(CPersonInfo, event.execPerson_id)
        result._execDate = CDateInfo(action.endDate)
        result._isPrimary = event.isPrimary
        result._order = event.order
        if event.result_id is not None:
            result._result = context.getInstance(CResultInfo, event.result_id)
        if event.rbAcheResult_id is not None:
            result._acheResult = context.getInstance(CAcheResultInfo, event.rbAcheResult_id)
        result._nextEventDate = None
        result._payStatus = event.payStatus
        result._note = event.note

        result._localContract = context.getInstance(CEventLocalContractInfo, event.id)
        result._mes = context.getInstance(CMesInfo, event.MES_id)
        result._mesSpecification = context.getInstance(CMesSpecificationInfo, event.mesSpecification_id)
        result._actions = CActionInfoProxyListEx(context, result)
        result._orgStructure_id = getCurrentDepartmentInfo(event.id)
        result._departmentManager = context.getInstance(CPersonInfo, departmentManagerId(result._orgStructure_id))

        prelimDiagModel = CPrelimDiagnosisModel(event.client_id, event.id, event.org_id)
        prelimDiagModel.loadDiagnostics(event.id)
        finalDiagModel = CFinalDiagnosisModel(event.client_id, event.id, event.org_id)
        finalDiagModel.loadDiagnostics(event.id)

        result._diagnosises = CDiagnosticInfoProxyList(context, [prelimDiagModel, finalDiagModel])
        result._visits = []
        result._ok = True
        result._loaded = True

    return result
