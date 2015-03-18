# -*- coding: utf-8 -*-
from library.FlatDirectory import CFDRecord
from ..info.PrintInfo import CInfo, CInfoList

__author__ = 'mmalkov'


class CFDValueInfo(CInfo):
    def __init__(self, context, FDValue):
        super(CFDValueInfo, self).__init__(context)
        self.__value = FDValue

    def __str__(self):
        return self.__value.value


class CFDFieldInfo(CInfo):
    def __init__(self, context, FDField):
        super(CFDFieldInfo, self).__init__(context)
        self.__field = FDField

    def __str__(self):
        return self.__field.name


class CFDValueInfoList(CInfoList):
    def __init__(self, context, FDRecord):
        super(CFDValueInfoList, self).__init__(context)
        self.__FDRecord = FDRecord

    def _load(self):
        self._items = [self.context.getInstance(CFDValueInfo, value) for value in self.__FDRecord.values]
        return True


class CFDFieldInfoList(CInfoList):
    def __init__(self, context, FDRecord):
        super(CFDFieldInfoList, self).__init__(context)
        self.__FDRecord = FDRecord

    def _load(self):
        self._items = [self.context.getInstance(CFDValueInfo, value) for value in self.__FDRecord.fields]
        return True


class CFDRecordInfo(CInfo):
    def __init__(self, context, _id):
        super(CFDRecordInfo, self).__init__(context)
        self.__id = _id
        self.__record = None
        self.__fields = None
        self.__values = None

    def _load(self):
        if not self.__id:
            self.__record = None
            self.__fields = []
            self.__values = []
            return False
        self.__record = CFDRecord.getById(self.__id)
        self.__fields = self.context.getInstance(CFDFieldInfoList, self.__record)
        self.__values = self.context.getInstance(CFDValueInfoList, self.__record)
        return True

    @property
    def fields(self):
        return self.load().__fields

    @property
    def values(self):
        return self.load().__values

    def __str__(self):
        return " / ".join(map(lambda v: v.__str__(), self.values))

    def __getitem__(self, item):
        return self.values[item]

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()
