# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


def explode_needles(needles):
    """
    Транслирует описание иголок (которые мы ищем) из строки/списка/словаря в словарь
    :param needles: Иголки
    :return: Описание
    """
    if isinstance(needles, basestring):
        if len(needles) in (3, 5):
            return {'=': decompose(needles)}
        if ',' in needles:
            return explode_needles(map(unicode.strip, needles.split(',')))
        if '-' in needles:
            return {'..': tuple(map(decompose, needles.split('-', 1)))}
    elif isinstance(needles, (list, tuple)):
        return {'|': map(explode_needles, needles)}
    elif isinstance(needles, dict):
        return needles


def decompose(value):
    """
    Разбирает значение кода МКБ на составные части
    :param value: код МКБ
    :return:
    """
    if '.' in value:
        return value[0], int(value[1:3]), int(value[4:])
    return value[0], int(value[1:3]), None


def hay_check(value, needles):
    """
    Проверяет значение на соответвие описанию искомых иголок
    :param value:
    :param needles:
    :return:
    """
    if not isinstance(value, tuple):
        value = decompose(value)
    needles = explode_needles(needles)
    if '|' in needles:
        return any(hay_check(value, needle) for needle in needles['|'])
    elif '=' in needles:
        return value == needles['=']
    elif '..' in needles:
        left, right = needles['..']
        return left <= value <= right
    return True


def any_thing(haystack, needles, extract):
    """
    Ищет иголку в стоге сена
    :param haystack: Стог
    :param needles: Описание иголок
    :param extract: Функция, возвращающая сено-иголку из куска сена
    :return: соответствует ли стог сена описанию иголкок
    """
    if not haystack:
        return False
    needles = explode_needles(needles)
    for hay in haystack:
        value = extract(hay)
        if not value:
            continue
        tmp = hay_check(value, needles)
        if tmp:
            return True
    return False


def mkb_from_mkb(mkb):
    return mkb.DiagID


if __name__ == "__main__":
    from pprint import pprint
    e = explode_needles(u'O20-O26.9, I05-I09.9, I34.0-I38, I42.0, I11.0-I11.9, I10.0-I15.9, N00.0-N07, N10-N15.9, N17.0-N21.9, N25.0-N28.9, D50-D64, E66.8, E66.9, E10.0, E14.9')
    pprint(e)
    print hay_check('O21', e)
    print hay_check('O26.10', e)