# -*- coding: utf-8 -*-
import datetime
from ..models.models_utils import DateInfo
#from base64 import b64encode
#import re
#from urllib import urlencode
# from PyQt4.QtCore import QDateTime, QDate
# from pychart import *
#from info.OrgInfo import COrgInfo, COrgStructureInfo
# from info.PersonInfo import CPersonInfo
# from library.PrintDialog import CDialogsInfo
#from info.PrintInfo import CDateInfo, CTimeInfo
# from library.Utils import forceDate, unformatSNILS, forceDouble, forceString
# from library.chart import areaToQPaintDevice, createTimeChart

__author__ = 'mmalkov'


class CTemplateHelpers(object):
    @staticmethod
    def transpose_table(table):
        return [[row[column_number] for row in table] for column_number in xrange(len(table[0]))] if table else [[]]

    @staticmethod
    def sum_columns(table):
        return [sum(row[column_number] for row in table) for column_number in xrange(len(table[0]))] if table else [[]]

    @staticmethod
    def table_uniform(list_list, null=None):
        max_len = max(len(row) for row in list_list)
        return [(row + [null] * (max_len - len(row))) for row in list_list]

    @staticmethod
    def table_column(table, column=0):
        return [row[column] for row in table] if table and table[0] else []


class CTemplateContext(object):
    def __init__(self, globals, data):
        self.globals = globals
        self.data = data
        # self.locals = {}
        self.now = datetime.datetime.now()
        self.builtin = {'currentDate': DateInfo(self.now.date()),
                        'currentTime': self.now.time().strftime("%H:%M:%S"),
                        'helpers': CTemplateHelpers,
                        }
        # self.builtin = { 'currentDate': CDateInfo(self.now.date()),
        #                  'currentTime': CTimeInfo(self.now.time()),
        #                  'date'       : self.date,
        #                  'present'    : self.present,
        #                  'pdf417'     : self.pdf417,
        #                  'p38code'    : self.p38code,
        #                  'p38test'    : self.p38test,
        #                  'Canvas'     : CCanvas,
        #                  'Plot'       : CChart,
        #                  'helpers'    : CTemplateHelpers,
        #                }

    # def __getitem__(self, key):
    #     if key in self.builtin:
    #         return self.builtin.get(key)
    #     if key in self.locals:
    #         result = self.locals[key]
    #     elif key in self.data:
    #         result = self.data[key]
    #     elif key in self.globals:
    #         result = self.globals[key]
    #     elif key in __builtins__:
    #         result = __builtins__[key]
    #     else:
    #         QtGui.qApp.log(u'Ошибка при печати шаблона',
    #                        u'Переменная или функция "%s" не определена.\nвозвращается строка'%key)
    #         result = '['+key+']'
    #
    #     if type(result) == dict:
    #         return CDictProxy(key, result)
    #     else:
    #         return result
    #
    #
    # def __setitem__(self, key, value):
    #     if type(value) == CDictProxy:
    #         self.locals[key] = value.data
    #     else:
    #         self.locals[key] = value
    #
    #
    # def __delitem__(self, key):
    #     del self.locals[key]
    #
    #
    #
    # def present(self, key):
    #     seq = key.split('.')
    #     key = seq[0]
    #     if self.builtin.has_key(key):
    #         data = self.builtin[key]
    #     elif self.locals.has_key(key):
    #         data = self.locals[key]
    #     elif self.data.has_key(key):
    #         data = self.data[key]
    #     elif self.globals.has_key(key):
    #         data = self.globals[key]
    #     elif __builtins__.has_key(key):
    #         data = __builtins__[key]
    #     else:
    #         return False
    #     for name in seq[1:]:
    #         if hasattr(data, 'has_key') and data.has_key(name):
    #             data = data[name]
    #         else:
    #             return False
    #     return True
    #
    #
    # def getCanvases(self):
    #     result = {}
    #     for key, val in self.locals.iteritems():
    #         if isinstance(val, CCanvas):
    #             result[key] = val
    #     return result
    #
    #
    # def pdf417(self, data, **params):
    #     params['data'] = data
    #     url = 'pdf417://localhost?'+urlencode(params)
    #     return '<IMG SRC="'+url+'">'
    #
    # def date(self, date):
    #     date = forceDate(date)
    #     if type(date) == CDateInfo:
    #         date = date.date
    #     if type(date) != QDate:
    #         date = QDate.fromString(unicode(date), u"dd.MM.yyyy")
    #     return CDateProxy(date)
    #
    # def p38test(self):
    #     return self.p38code('1027802751701', '1357', '41043', '4008', '4104300000002535', 'I67', '1', 100, 1, '3780115', u'4.5+80 мкг+мкг/доза', 1.234, u'008-656-445 65', '083', '1', QDate(2008, 3, 25))
    #
    # def p38code(self, OGRN, doctorCode, orgCode, series, number, MKB, fundingCode, benefitPersent, isIUN, remedyCode, remedyDosage, remedyQuantity, SNILS, personBenefitCategory, periodOfValidity, date):
    #     def intToBits(data, bitsWidth):
    #         if isinstance(data,(int, long)):
    #             n = data
    #         elif not data:
    #             n = 0
    #         else:
    #             try:
    #                 n = int(data, 10)
    #             except:
    #                 n = 0
    #         result = ''
    #         while len(result)<bitsWidth:
    #             result = ('1' if n%2 else '0')+result
    #             n //= 2
    #         return result
    #
    #     def strToBits(data, strWidth):
    #         s = unicode(data)[:strWidth]
    #         s = s.encode('cp1251')
    #         s += ' '*(strWidth-len(s))
    #         result = ''
    #         for c in s:
    #             code = ord(c)
    #             r = ''
    #             for i in xrange(8):
    #                 r = ('1' if (code%2) else '0') + r
    #                 code //= 2
    #             result += r
    #         return result
    #
    #     def bitsToChars(bits):
    #         result = ''
    #         for i in xrange(0, len(bits), 8):
    #             result += chr(int(bits[i:i+8], 2))
    #         return result
    #
    #     bits = intToBits(OGRN, 50) + \
    #            strToBits(doctorCode, 7) + \
    #            intToBits(OGRN, 50) + \
    #            strToBits(orgCode,  7) + \
    #            strToBits(series,  14) + \
    #            intToBits(number, 64) + \
    #            strToBits(MKB, 7) + \
    #            intToBits(fundingCode, 2) + \
    #            ('0' if benefitPersent == 100 else '1') + \
    #            ('0' if isIUN else '0') + \
    #            intToBits(remedyCode, 44) + \
    #            intToBits(unformatSNILS(SNILS), 37) + \
    #            strToBits(remedyDosage, 20) + \
    #            intToBits(int(remedyQuantity*1000), 24) + \
    #            intToBits(personBenefitCategory, 10) + \
    #            ('1' if periodOfValidity else '0') + \
    #            intToBits(date.year()-2000, 7) + \
    #            intToBits(date.month(), 4) + \
    #            intToBits(date.day(), 5)
    #     bits += '0' # признак наличия ВК
    #     bits += '0'*(-len(bits)%8)
    #     bits += intToBits(6, 8) # версия протокола
    #     chars = bitsToChars(bits)
    #     return 'p'+b64encode(chars)

#
# class CCanvas(object):
#     black   = QtGui.QColor(  0,   0,   0)
#     red     = QtGui.QColor(255,   0,   0)
#     green   = QtGui.QColor(  0, 255,   0)
#     yellow  = QtGui.QColor(255, 255,   0)
#     blue    = QtGui.QColor(  0,   0, 255)
#     magenta = QtGui.QColor(255,   0, 255)
#     cyan    = QtGui.QColor(  0, 255, 255)
#     white   = QtGui.QColor(255, 255, 255)
#
#     def __init__(self, width, height):
#         self.image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
#         self.penColor = CCanvas.black
#         self.brushColor = CCanvas.red
#         self.fill(CCanvas.white)
#
#     @staticmethod
#     def rgb(self, r, g, b):
#         return QtGui.QColor(r, g, b)
#
#
#     def setPen(self, color):
#         self.penColor = color
#
#
#     def setBrush(self, color):
#         self.brushColor = color
#
#
#     def fill(self, color):
#         painter = QtGui.QPainter(self.image)
#         painter.fillRect(self.image.rect(), QtGui.QBrush(color))
#
#
#     def line(self, x1, y1, x2, y2):
#         painter = QtGui.QPainter(self.image)
#         painter.setPen(QtGui.QPen(self.penColor))
#         painter.drawLine(x1, y1, x2, y2)
#
#
#     def ellipse(self, x, y, w, h):
#         painter = QtGui.QPainter(self.image)
#         painter.setPen(QtGui.QPen(self.penColor))
#         painter.setBrush(QtGui.QBrush(self.brushColor))
#         painter.drawEllipse(x, y, w, h)


# class CChart(CCanvas):
#     def __init__(self, width, height, pychart):
#         CCanvas.__init__(self, width, height)
#         areaToQPaintDevice(pychart, self.image)
#         if pychart:
#             self.hasData = True
#         else:
#             self.hasData = False
#
#     @classmethod
#     def __singleDoubleChart(cls, clientId, name, step, fromDate, toDate):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения показателя name
#         для клиента clientId, со времени fromDate до времени toDate с шагом отрисовки по x, равным step
#         """
#
#         fromDate = fromDate.date if type(fromDate) == CDateProxy else fromDate
#         fromDate = forceDate(fromDate) if fromDate else None
#         toDate = toDate.date if type(toDate) == CDateProxy else toDate
#         toDate = forceDate(toDate) if toDate else None
#
#         actions = getTimedClientActionsByFlatCode(clientId, '%inspect%', fromDate,  toDate)
#
#         def safeToDouble(v):
#             try:
#                 return forceDouble(v)
#             except:
#                 return None
#
#         ts =  [ (action.date, forceDouble(action[name])) for action in actions
#                                                             if (action.date and action.hasProperty(name) and action[name] and safeToDouble(action[name])) ]
#
#         if not ts or len(ts) == 0:
#             return None
#
#
#         return createTimeChart(ts, name, u'', 2, step)
#
#     @classmethod
#     def t(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения температуры
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#
#         return cls.__singleDoubleChart(clientId, u't', 0.2, fromDate, toDate)
#
#     @classmethod
#     def heartRate(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения ЧСС
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#         return cls.__singleDoubleChart(clientId, u'ЧСС', 5, fromDate, toDate)
#
#     @classmethod
#     def respiratoryRate(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения ЧД
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#         return cls.__singleDoubleChart(clientId, u'ЧДД', 5, fromDate, toDate)
#
#     @classmethod
#     def systolicBloodPressure(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения систолического АД
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#         fromDate = fromDate.date if type(fromDate) == CDateProxy else fromDate
#         fromDate = forceDate(fromDate) if fromDate else None
#         toDate = toDate.date if type(toDate) == CDateProxy else toDate
#         toDate = forceDate(toDate) if toDate else None
#
#         actions = getTimedClientActionsByFlatCode(clientId, '%inspect%', fromDate,  toDate)
#
#         def safeToDouble(v):
#             try:
#                 return forceDouble(v)
#             except:
#                 return None
#
#         def toPair(v):
#             lst = re.split('\W+', forceString(v))
#             if len(lst) < 2:
#                 return None
#             ret0 = safeToDouble(lst[0])
#             ret1 = safeToDouble(lst[1])
#             if ret0 and ret1:
#                 return (ret0, ret1)
#             else:
#                 return None
#
#         def zip2to3(v, t):
#             t0, t1 = t
#             return (v, t0, t1)
#
#         name = u'АД нижн.'
#         ts =  [ (forceDate(action.date), forceDouble(action[name])) for action in actions
#                                                             if (action.date and action.hasProperty(name) and action[name] ) ]
#
#
#         if not ts or len(ts) == 0:
#             return None
#
#         return createTimeChart(ts, u'САД', u'', 2, 5)
#
#     @classmethod
#     def diastolicBloodPressure(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения дистолического АД
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#         fromDate = fromDate.date if type(fromDate) == CDateProxy else fromDate
#         fromDate = forceDate(fromDate) if fromDate else None
#         toDate = toDate.date if type(toDate) == CDateProxy else toDate
#         toDate = forceDate(toDate) if toDate else None
#
#         actions = getTimedClientActionsByFlatCode(clientId, '%inspect%', fromDate,  toDate)
#
#         # Возвращаем None, если полученный объект не конвертится в double
#         def safeToDouble(v):
#             try:
#                 return forceDouble(v)
#             except:
#                 return None
#
#         # Превращает строку вида '90/90' или '90\90' в пару (90,90)
#         # Символ-разделитель не должен быть буквой или числом
#         # В остальном может быть чем угодно
#         # Возвращает None если строка неправильная
#         def toPair(v):
#             lst = re.split('\W+', forceString(v))
#             if len(lst) < 2:
#                 return None
#             ret0 = safeToDouble(lst[0])
#             ret1 = safeToDouble(lst[1])
#             if ret0 and ret1:
#                 return (ret0, ret1)
#             else:
#                 return None
#
#         # zip2to3(a, (b,c)) == (a,b,c)
#         def zip2to3(v, t):
#             t0, t1 = t
#             return (v, t0, t1)
#
#         dbp = u'АД верхн.'
#         ts =  [ (forceDate(action.date), forceDouble(action[dbp])) for action in actions
#                                                             if (action.date and action.hasProperty(dbp ) and action[dbp]) ]
#
#         if not ts or len(ts) == 0:
#             return None
#
#         return createTimeChart(ts, u'ДАД', u'', 2, 5)
#
#     @classmethod
#     def bloodPressure(cls, clientId,  fromDate = None, toDate = None):
#         """
#         Возвращает область (area) с графиком библиотеки pychart, отображающим изменения АД
#         для клиента clientId, со времени fromDate до времени toDate
#         """
#         fromDate = fromDate.date if type(fromDate) == CDateProxy else fromDate
#         fromDate = forceDate(fromDate) if fromDate else None
#         toDate = toDate.date if type(toDate) == CDateProxy else toDate
#         toDate = forceDate(toDate) if toDate else None
#
#         actions = getTimedClientActionsByFlatCode(clientId, '%inspect%', fromDate,  toDate)
#
#         # Возвращаем None, если полученный объект не конвертится в double
#         def safeToDouble(v):
#             try:
#                 return forceDouble(v)
#             except:
#                 return None
#
#         # Превращает строку вида '90/90' или '90\90' в пару (90,90)
#         # Символ-разделитель не должен быть буквой или числом
#         # В остальном может быть чем угодно
#         # Возвращает None если строка неправильная
#         def toPair(v):
#             lst = re.split('\W+', forceString(v))
#             if len(lst) < 2:
#                 return None
#             ret0 = safeToDouble(lst[0])
#             ret1 = safeToDouble(lst[1])
#             if ret0 and ret1:
#                 return (ret0, ret1)
#             else:
#                 return None
#
#         # zip2to3(a, (b,c)) == (a,b,c)
#         def zip2to3(v, t):
#             t0, t1 = t
#             return (v, t0, t1)
#
#
#         dbp = u'АД верхн.'
#         sbp = u'АД нижн.'
#         ts =  [ (forceDate(action.date), forceDouble(action[dbp]), forceDouble(action[sbp])) for action in actions
#                                                             if (action.date and action.hasProperty(dbp) and action[dbp] and action.hasProperty(sbp) and action[sbp] ) ]
#
#         if not ts or len(ts) == 0:
#             return None
#
#         return createTimeChart(ts, (dbp, u'Диастолическое', u'Систолическое'), u'', 2, 5)
#
#     @staticmethod
#     def newChart():
#         # We have 10 sample points total.  The first value in each tuple is
#         # the X value, and subsequent values are Y values for different lines.
#         data = [(10, 20, 30), (20, 65, 33),
#                 (30, 55, 30), (40, 45, 51),
#                 (50, 25, 27), (60, 75, 30),
#                 (70, 80, 42), (80, 62, 32),
#                 (90, 42, 39), (100, 32, 39)]
#
#         # The format attribute specifies the text to be drawn at each tick mark.
#         # Here, texts are rotated -60 degrees ("/a-60"), left-aligned ("/hL"),
#         # and numbers are printed as integers ("%d").
#         xaxis = axis.X(format="/a-60/hL%d", tic_interval = 20, label="Stuff")
#         yaxis = axis.Y(tic_interval = 20, label="Value")
#
#         # Define the drawing area. "y_range=(0,None)" tells that the Y minimum
#         # is 0, but the Y maximum is to be computed automatically. Without
#         # y_ranges, Pychart will pick the minimum Y value among the samples,
#         # i.e., 20, as the base value of Y axis.
#         ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
#
#         # The first plot extracts Y values from the 2nd column
#         # ("ycol=1") of DATA ("data=data"). X values are takes from the first
#         # column, which is the default.
#         plot = line_plot.T(label="foo", data=data, ycol=1, tick_mark=tick_mark.star)
#         plot2 = line_plot.T(label="bar", data=data, ycol=2, tick_mark=tick_mark.square)
#
#         ar.add_plot(plot, plot2)
#
#         # The call to ar.draw() usually comes at the end of a program.  It
#         # draws the axes, the plots, and the legend (if any).
#         return ar
#
#
# class CDateProxy(object):
#     def __init__(self,date):
#         self.date = date
#
#     def __add__(self, days):
#         return CDateProxy(self.date.addDays(days))
#
#     def __sub__(self, days):
#         return CDateProxy(self.date.addDays(-days))
#
#
# class CDictProxy(object):
#     def __init__(self, path, data):
#         object.__setattr__(self, 'path', path)
#         object.__setattr__(self, 'data', data)
#
#
#     def __getattr__(self, name):
#         if self.data.has_key(name):
#             result = self.data[name]
#             if type(result) == dict:
#                 return CDictProxy(self.path+'.'+name, result)
#             else:
#                 return result
#         else:
#             s = self.path+'.'+name
#             # QtGui.qApp.log(u'Ошибка при печати шаблона',
#             #                u'Переменная или функция "%s" не определена.\nвозвращается строка'%s)
#             return '['+s+']'
#
#
#     def __setattr__(self, name, value):
#         self.data[name] = value
#
#
# def getTimedClientActionsByFlatCode(clientId, actionTypeFlatCode, fromDate, toDate):
#     from Events.Action import CActionTypeCache
#
#     db = QtGui.qApp.db
#     tableAction = db.table('Action')
#     tableEvent = db.table('Event')
#     join = tableAction.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
#
#     actionTypes = CActionTypeCache.getTypesByFlatcode(actionTypeFlatCode)
#     actionTypeIds = [ actionType.id for actionType in actionTypes ]
#     cond = [
#         tableEvent['client_id'].eq(clientId),
#         tableAction['actionType_id'].inlist(actionTypeIds),
#     ]
#
#     if(toDate):
#         cond.append(tableAction['begDate'].dateLe(toDate))
#     if(fromDate):
#         cond.append(tableAction['begDate'].dateGe(fromDate))
#
#     records = db.getRecordList(join, '*', cond)
#
#     from Events.Action import CAction as Action
#
#     return [ Action(record=record) for record in records ]