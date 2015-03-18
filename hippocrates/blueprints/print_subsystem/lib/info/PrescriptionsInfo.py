# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from collections import defaultdict
import itertools
from EventEditor.Prescriptions.const import IntersectionType
from EventEditor.Prescriptions.data_models import getPrescriptionModelsFactory
from EventEditor.Prescriptions.data_models.qtsql_models import CPrescriptionSqlModel
from EventEditor.Prescriptions.types import CDateTimeInterval
from EventEditor.Prescriptions.utils import getIntersectionType
from Events.Action import CAction
from ..info.EventInfo import CEventInfo
from ..info.PrintInfo import CInfo, CInfoList, CRBInfo, CDateTimeInfo
from ..info.OrgInfo import CClientInfo
from library.Utils import forceString, forceRef
from library.printing.html import escape
from library.settings import CSettings

__author__ = 'mmalkov'


def intervalIter(interval, step):
    i = QtCore.QDateTime(interval.begDateTime)
    while i < interval.endDateTime:
        yield CDateTimeInterval(i, i.addSecs(step))
        i = i.addSecs(step)


class CDateTimeIntervalInfo(CInfo):
    def __init__(self, context, interval, step):
        super(CDateTimeIntervalInfo, self).__init__(context)
        self._interval = interval
        self._step = step

    def stepCount(self):
        return self._interval.begDateTime.secsTo(self._interval.endDateTime) / self._step

    def captions(self):
        secs = self._interval.begDateTime.secsTo(self._interval.endDateTime)
        for i in xrange(0, secs, self._step):
            dateTime = self._interval.begDateTime.addSecs(i)
            yield dateTime.time().hour() if self._step == 3600 else forceString(dateTime.toString('dd.MM'))

    def hours(self):
        secs = self._interval.begDateTime.secsTo(self._interval.endDateTime)
        for i in xrange(0, secs, 3600):
            yield CDateTimeInfo(self._interval.begDateTime.addSecs(i))

    def dates(self):
        days = self._interval.begDateTime.daysTo(self._interval.endDateTime)
        for i in xrange(days):
            yield CDateTimeInfo(self._interval.begDateTime.addDays(i))

    def __str__(self):
        return u'%s - %s' % (forceString(self._interval.begDateTime), forceString(self._interval.endDateTime))


class CDrugIntervalInfo(CInfo):
    def __init__(self, context, intersectionType, dcInterval, dcStatus):
        super(CDrugIntervalInfo, self).__init__(context)
        self._isType = intersectionType
        self._interval = dcInterval
        self._status = dcStatus

    def __strint(self):
        if self._isType == IntersectionType.left:
            return u'%s>' % self._interval.endDateTime.toString('HH:mm')
        elif self._isType == IntersectionType.over:
            return u''
        elif self._isType == IntersectionType.inner:
            return u'<%s-%s>' % (self._interval.begDateTime.toString('HH:mm'),
                                 self._interval.endDateTime.toString('HH:mm'))
        elif self._isType == IntersectionType.right:
            return u'<%s' % self._interval.begDateTime.toString('HH:mm')
        elif self._isType == IntersectionType.point:
            return unicode(self._interval.begDateTime.toString('HH:mm'))
        else:
            return u''

    def __str__(self):
        return escape(self.__strint())

    def _load(self):
        return True

    intersection = property(lambda self: self._isType)
    interval = property(lambda self: self._interval)
    status = property(lambda self: self._status)


class CDrugCellInfo(CInfoList):
    def __init__(self, context, intervals):
        super(CDrugCellInfo, self).__init__(context)
        self._drugIntervals = intervals
        self._items = [
            CDrugIntervalInfo(context, isType, dc.getDateTimeInterval(), dc.extStatus)
            for (isType, dc) in sorted(intervals, key=lambda (w, x): x.begDateTime)
            if isType > 0
        ]

    def _load(self):
        return True


class CDrugInfo(CInfo):
    def __init__(self, context, drug):
        super(CDrugInfo, self).__init__(context)
        self.__drug = drug

    name = property(lambda self: self.__drug.name)
    dose = property(lambda self: self.__drug.dose)
    unitCode = property(lambda self: self.__drug.rlsRecord.unitCode)
    dosageUnitCode = property(lambda self: self.__drug.rlsRecord.dosageUnitCode)
    dosageValue = property(lambda self: self.__drug.rlsRecord.dosageValue)

    def __str__(self):
        return u'%s (%s %s) %s %s' % (
            self.name,
            self.__drug.rlsRecord.dosageValue,
            self.__drug.rlsRecord.dosageUnitCode,
            self.dose,
            self.__drug.rlsRecord.unitCode,
        )

    def _load(self):
        return True


class CDrugInfoList(CInfoList):
    def __init__(self, context, drugListModel):
        super(CDrugInfoList, self).__init__(context)
        self._items = [CDrugInfo(context, drug) for drug in drugListModel]

    def _load(self):
        return True


class CExecDrugCellInfoList(CInfoList):
    def __init__(self, context, model, interval, step):
        super(CExecDrugCellInfoList, self).__init__(context)
        self.__model = model
        self.__interval = interval
        self.__step = step

    def _load(self):
        self._items = [
            CDrugCellInfo(
                self.context,
                itertools.imap(
                    lambda w: (getIntersectionType(w, i), w),
                    itertools.chain(*[
                        drugInterval.execIntervals
                        for (_, drugInterval) in self.__model.getDrugIntervals(i)
                    ])
                )
            )
            for i in intervalIter(self.__interval, self.__step)
        ]
        return True


class CPrescDrugCellInfoList(CInfoList):
    def __init__(self, context, model, interval, step):
        super(CPrescDrugCellInfoList, self).__init__(context)
        self.__model = model
        self.__interval = interval
        self.__step = step

    def _load(self):
        self._items = [
            CDrugCellInfo(self.context, self.__model.getDrugIntervals(i))
            for i in intervalIter(self.__interval, self.__step)
        ]
        return True


class CPrescriptionInfo(CInfo):
    def __init__(self, context, prescriptionModel, interval, step):
        super(CPrescriptionInfo, self).__init__(context)
        self.__interval = interval
        self.__step = step
        self.__model = prescriptionModel

    def _load(self):
        # TODO: отвязаться от необходимости знать внутреннюю структуру actInfo
        if isinstance(self.__model, CPrescriptionSqlModel):
            cAction = self.__model.actInfo._cAction
        else:
            cAction = CAction.getById(self.__model.id)
        self._action = cAction.toInfo(self.context)
        self._eventInfo = self.context.getInstance(CEventInfo, cAction.event_id)
        self._clientInfo = self.context.getInstance(CClientInfo, cAction.Event.client_id)
        self._prescIntervals = self.context.getInstance(
            CPrescDrugCellInfoList, self.__model, self.__interval, self.__step)
        self._execIntervals = self.context.getInstance(
            CExecDrugCellInfoList, self.__model, self.__interval, self.__step)
        self._drugs = CDrugInfoList(self.context, self.__model.drugComponents)
        self._interval = CDateTimeIntervalInfo(self.context, self.__interval, self.__step)
        return True

    drugs = property(lambda self: self.load()._drugs)
    voa = property(lambda self: self.load()._action['voa',] or u'')
    note = property(lambda self: self.load()._action.note or '')
    event = property(lambda self: self.load()._eventInfo)
    client = property(lambda self: self.load()._clientInfo)
    prescIntervals = property(lambda self: self.load()._prescIntervals)
    execIntervals = property(lambda self: self.load()._execIntervals)
    interval = property(lambda self: self.load()._interval)


class CMOAInfo(CRBInfo):
    tableName = 'rbMethodOfAdministration'


class CPrescriptionSubGroupInfo(CInfoList):
    def __init__(self, context, moa, group):
        super(CPrescriptionSubGroupInfo, self).__init__(context)
        self._moa = self.getInstance(CMOAInfo, moa)
        self._items = group

    def _load(self):
        return True

    moa = property(lambda self: self._moa)


class CPrescriptionInfoList(CInfoList):
    def __init__(self, context, prescriptionListModel, interval, step):
        super(CPrescriptionInfoList, self).__init__(context)
        self.__prescriptionListModel = prescriptionListModel
        self.__interval = interval
        self.__step = step
        remap = defaultdict(set)
        for model in self.__prescriptionListModel:
            if model.getDrugIntervals(interval):
                remap[model.actInfo.moa].add(model)
        self._items = [
            CPrescriptionSubGroupInfo(
                self.context,
                moa,
                [CPrescriptionInfo(self.context, data, self.__interval, self.__step) for data in models]
            ) for moa, models in remap.iteritems()
        ]
        self.interval = CDateTimeIntervalInfo(context, interval, step)

    def _load(self):
        return True


class CPrescriptionInfoListId(CPrescriptionInfo):
    def __init__(self, context, event_id, interval, step):
        db_access_type = CSettings.getInt('Prescription.DataAccessType')
        factory = getPrescriptionModelsFactory(db_access_type)
        prescriptionListModel = factory.getPrescriptionListModel()(event_id)
        super(CPrescriptionInfoListId, self).__init__(context, prescriptionListModel, interval, step)


class CExtendedClientInfo(CInfo):
    def __init__(self, context, event_id):
        super(CExtendedClientInfo, self).__init__(context)
        self.__event_id = event_id

    def _load(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableAT = db.table('ActionType')
        tableATG = db.table('ActionType').alias('ActionTypeGroup')
        queryTable = tableAction.join(tableAT, tableAction['actionType_id'].eq(tableAT['id']))
        queryTable = queryTable.join(tableATG, tableAT['group_id'].eq(tableATG['id']))
        fields = (
            tableAction['id'],
            tableAT['flatCode'],
            tableATG['flatCode']
        )
        cond = (
            tableAction['event_id'].eq(self.__event_id),
        )
        height = None
        weight = None
        regimen = None
        feed = None
        for actionRecord in db.getRecordIter(queryTable, fields, cond, 'Action.createDatetime DESC'):
            actionId = forceRef(actionRecord.value(0))
            flatCode = forceString(actionRecord.value(1))
            groupCode = forceString(actionRecord.value(2))
            if flatCode in ('regimen', 'feed') or groupCode in ('primaryInspection', ):
                action = CAction.getById(actionId)
                if 'height' in action._propertiesByCode:
                    if not height and action['height', ]:
                        height = action['height', ]
                if 'weight' in action._propertiesByCode:
                    if not weight and action['weight', ]:
                        weight = action['weight', ]
                if 'regimen' in action._propertiesByCode:
                    if not regimen and action['regimen', ]:
                        regimen = action['regimen', ]
                if 'feed' in action._propertiesByCode:
                    if not feed and action['feed', ]:
                        feed = action['feed', ]
            if height and weight and regimen and weight:
                break
        self.__height = height or u'Неизвестно'
        self.__weight = weight or u'Неизвестно'
        self.__regimen = regimen or u'Неизвестно'
        self.__feed = feed or u'Неизвестно'
        self.__square = height * weight / 3600.0 if height and weight else u'Неизвестно'

    height = property(lambda self: self.load().__height)
    weight = property(lambda self: self.load().__weight)
    regimen = property(lambda self: self.load().__regimen)
    feed = property(lambda self: self.load().__feed)
    square = property(lambda self: self.load().__square)