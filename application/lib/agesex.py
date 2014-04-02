# -*- coding: utf-8 -*-
import re
import datetime

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


def recordAcceptableEx(clientSex, clientAge, recordSex, recordAge):
    """
    @type clientSex: str | unicode
    @type clientAge: tuple
    @type recordSex: str | unicode
    @type recordAge: str | unicode
    """
    return not (recordSex and recordSex != clientSex) and \
           not (clientAge and not checkAgeSelector(parseAgeSelector(recordAge), clientAge))


def checkAgeSelector((begUnit, begCount, endUnit, endCount), ageTuple):
    """
    @type begUnit: int
    @type begCount: int
    @type endUnit: int
    @type endCount: int
    @type ageTuple: tuple
    """
    return not (begUnit != 0 and ageTuple[begUnit - 1] < begCount or endUnit != 0 and ageTuple[endUnit - 1] > endCount)


def parseAgeSelector(val):
    """
    @type val: str | unicode
    """
    try:
        return parseAgeSelectorInt(val)
    except:
        return 0, 0, 0, 0


def parseAgeSelectorInt(val):
    u""" selector syntax: "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" -
    с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет;
    пустая нижняя или верхняя граница - нет ограничения снизу или сверху
    @type val: str | unicode
    @rtype: tuple
    """
    parts = val.split('-')
    if len(parts) == 2:
        begUnit, begCount = parseAgeSelectorPart(parts[0].strip())
        endUnit, endCount = parseAgeSelectorPart(parts[1].strip())
        return begUnit, begCount, endUnit, endCount
    elif len(parts) == 1:
        if parts[0]:
            begUnit, begCount = parseAgeSelectorPart(parts[0].strip())
        else:
            begUnit, begCount = 0, 0
        return begUnit, begCount, 0, 0
    raise ValueError(u'Недопустимый синтаксис селектора возраста "%s"' % val)


AgeSelectorUnits = u'днмг'
re_age_selector = re.compile(r'^(\d+)\s*([^\d\s]+)$')


def parseAgeSelectorPart(val):
    if val:
        matchObject = re_age_selector.match(val)
        if matchObject:
            strCount, strUnit = matchObject.groups()
            count = int(strCount) if strCount else 0
            unit = AgeSelectorUnits.find(strUnit.lower()) + 1
            if unit == 0:
                raise ValueError(u'Неизвестная единица измерения "%s"' % strUnit)
            return unit, count
        raise ValueError(u'Недопустимый синтаксис части селектора возраста "%s"' % val)
    return 0, 0


def calcAgeTuple(birthDay, today):
    d = calcAgeInDays(birthDay, today)
    if d >= 0:
        return (
            d,
            d / 7,
            calcAgeInMonths(birthDay, today),
            calcAgeInYears(birthDay, today)
        )
    return None


def calcAgeInMonths(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)

    bYear = birthDay.year
    bMonth = birthDay.month
    bDay = birthDay.day

    tYear = today.year
    tMonth = today.month
    tDay = today.day

    result = (tYear - bYear) * 12 + (tMonth - bMonth)
    if bDay > tDay:
        result -= 1
    return result


def calcAgeInYears(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)

    bYear = birthDay.year
    bMonth = birthDay.month
    bDay = birthDay.day

    tYear = today.year
    tMonth = today.month
    tDay = today.day

    result = tYear - bYear
    if bMonth > tMonth or (bMonth == tMonth and bDay > tDay):
        result -= 1
    return result


def calcAgeInDays(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)
    return (today - birthDay).days