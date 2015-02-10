# -*- coding: utf-8 -*-

#from PyQt4 import QtCore, QtGui
# from library.Utils import *
from flask import g


class CInfoContext(object):
    u"""Отображение (класс объекта, параметры объекта) -> Экземпляр класса"""

    def __init__(self):
        self._mapClassesToInstances = {}

    def getInstance(self, infoClass, *args, **kwargs):
        mapArgsToInstance = self._mapClassesToInstances.setdefault(infoClass, {})
        key = (args, tuple(kwargs.iteritems()))
        if key in mapArgsToInstance:
            return mapArgsToInstance[key]
        else:
            result = infoClass(self, *args, **kwargs)
            mapArgsToInstance[key] = result
            return result


class CInfo(object):
    u"""Базовый класс для представления объектов при передаче в шаблоны печати"""
    def __init__(self, context):
        self._loaded = False
        self._ok = False
        self.context = context

    def _load(self):
        """Pure virtual"""
        raise NotImplementedError

    def load(self):
        if not self._loaded:
            self._ok = self._load()
            self._loaded = True
        return self

    def getInstance(self, infoClass, *args, **kwargs):
        return self.context.getInstance(infoClass, *args, **kwargs)


    def __nonzero__(self):
        self.load()
        return self._ok

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

    def getProperties(self):
        result = []
        # class properties
        class_ = type(self)
        for name, value in class_.__dict__.iteritems():
            if not name.startswith('_') and isinstance(value, property):
                propvalue = self.__getattribute__(name)
                type_ = type(propvalue)
                result.append((name, str(type_), value.__doc__))
        return result


class CTemplatableInfoMixin:
    u"""Примесевый класс для представления возможности печати СInfo через собственный шаблон"""

    def getPrintTemplateContext(self):
        # "абстрактный" метод для получения контекста печати
        return None

    def getPrintTemplateList(self, printContext=None):
        from ..utils import getPrintTemplates
        # список пар (имяШаблона, idШаблона) подходящих для печати этого объекта
        return getPrintTemplates(printContext if printContext else self.getPrintTemplateContext())

    def getData(self):
        # "абстрактный" метод для получения данных для шаблона печати
        return {}

    def formatByTemplateId(self, templateId):
        # формирование html по id шаблона
        from ..internals import renderTemplate
        from ...models.models_all import Rbprinttemplate
        template_data = g.printing_session.query(Rbprinttemplate).get(templateId)
        if not template_data:
            return ''
        data = self.getData()
        html, canvases = renderTemplate(template_data.templateText, data, render=template_data.render)
        return html

    def formatByTemplate(self, name, printContext=None):
        # формирование html по имени шаблона
        for templateName, templateId in self.getPrintTemplateList(printContext):
            if templateName == name:
                return self.formatByTemplateId(templateId)
        return u'Шаблон "%s" не найден в контексте печати "%s"' % (name, printContext if printContext else self.getPrintTemplateContext())


class CInfoList(CInfo):
    u"""Базовый класс для представления списков (массивов) объектов при передаче в шаблоны печати"""
    def __init__(self, context):
        CInfo.__init__(self, context)
        self._items = []

    def __len__(self):
        self.load()
        return len(self._items)

    def __getitem__(self, key):
        self.load()
        return self._items[key]

    def __iter__(self):
        self.load()
        return iter(self._items)

    def __str__(self):
        self.load()
        return u', '.join([unicode(x) for x in self._items])

    def __nonzero__(self):
        self.load()
        return bool(self._items)

    def filter(self, **kw):
        self.load()

        result = CInfoList(self.context)
        result._loaded = True
        result._ok = True

        for item in self._items:
            if all([item.__getattribute__(key) == value for key, value in kw.iteritems()]):
                result._items.append(item)
        return result

    def __add__(self, right):
        if isinstance(right, CInfoList):
            right.load()
            rightItems = right._items
        elif isinstance(right, list):
            rightItems = right
        else:
            raise TypeError(u'can only concatenate CInfoList or list (not "%s") to CInfoList' % type(right).__name__)
        self.load()

        result = CInfoList(self.context)
        result._loaded = True
        result._ok = True

        result._items = self._items + rightItems
        return result


class CInfoProxyList(CInfo):
    def __init__(self, context):
        CInfo.__init__(self, context)
#        self._loaded = True
#        self._ok = True
        self._items = []

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key):  # чисто-виртуальный
        return None

    def __iter__(self):
        for i in xrange(len(self._items)):  # цикл по self._items исп. нельзя т.к. у нас хитрый __getitem__
            yield self.__getitem__(i)

    def __str__(self):
        return u', '.join([unicode(x) for x in self.__iter__()])

    def __nonzero__(self):
        return bool(self._items)


class CDateInfo(object):
    def __init__(self, date=None):
        if date is None:
            self.date = QtCore.QDate()
        else:
            self.date = forceDate(date)

    def __str__(self):
        return forceString(self.date)

    def __nonzero__(self):
        return bool(self.date.isValid())

    def __add__(self, x):
        return forceString(self.date) + str(x)

    def __radd__(self, x):
        return str(x)+forceString(self.date)


class CTimeInfo(object):
    def __init__(self, time=None):
        if time is None:
            self.time = QtCore.QTime()
        else:
            self.time = time

    def toString(self):
        return formatTime(self.time)

    def __str__(self):
        return self.toString()

    def __nonzero__(self):
        return bool(self.time.isValid())

    def __add__(self, x):
        return self.toString() + str(x)

    def __radd__(self, x):
        return str(x) + self.toString()


class CDateTimeInfo(object):
    def __init__(self, date=None):
        if date is None:
            self.datetime = QtCore.QDateTime()
        else:
            self.datetime = forceDateTime(date)

    def __str__(self):
        if self.datetime:
            date = self.datetime.date()
            time = self.datetime.time()
            return forceString(date)+' '+formatTime(time)
        else:
            return ''

    def __nonzero__(self):
        return bool(self.datetime.isValid())

    def __add__(self, x):
        return forceString(self.datetime) + str(x)

    def __radd__(self, x):
        return str(x)+forceString(self.datetime)

    date = property(lambda self: self.datetime.date())
    time = property(lambda self: self.datetime.time())


class CRBInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        assert self.tableName, 'tableName must be defined in derivative'

    def _load(self):
        query = '''SELECT *
                   FROM {0}
                   WHERE id = {1};'''.format(self.tableName, self.id)
        record = db_session.execute(query).first() if self.id else None
        db_session.close()
        #record = db.getRecord(, '*', ) if self.id else None
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._initByRecord(record)
            return True
        else:
            self._code = ''
            self._name = ''
            self._initByNull()
            return False

    def _initByRecord(self, record):
        pass

    def _initByNull(self):
        pass

    def __str__(self):
        return self.load()._name

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
