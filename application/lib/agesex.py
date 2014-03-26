# -*- coding: utf-8 -*-

__author__ = 'mmalkov'


class AgeSex(object):
    # TODO: Здесь надо парсить age и прочую ерунду. Пока так.
    def __init__(self, obj):
        self.obj = obj

    def __json__(self):
        result = {}
        if hasattr(self.obj, 'age'):
            result['age'] = self.obj.age
        if hasattr(self.obj, 'sex'):
            result['sex'] = self.obj.sex
        return result