# -*- coding: utf-8 -*-

from blueprints.risar.lib.risk_groups.needles_haystacks import any_thing
from nemesis.lib.utils import safe_bool_none


def _filter_parity_prev_preg(prev_preg):
    """
    На форме «Анамнез пациентки» на вкладке «Сведения о преыдущих беременностях»,
    у которых атрибут «Исход беременности» = преждевременные роды 22-27 недель
    или преждевременные роды 28-37 недель или запоздалые роды или роды в срок.
    """
    return prev_preg.action['pregnancyResult'].value_raw in (
        'premature_birth_22-27', 'premature_birth_28-37', 'postmature_birth', 'delivery'
    )


def _filter_misbirth_prev_preg(prev_preg):
    """
    На форме «Анамнез пациентки» на вкладке «Сведения о преыдущих беременностях» записи
    со значением атрибута «Исход беременности» = самопроизвольный выкидыш до 11 недель или
    самопроизвольный выкидыш 12-21 недель или медицинский аборт до 12 недель или
    аборт по мед.показаниям или неуточненный выкидыш
    """
    return prev_preg.action['pregnancyResult'].value_raw in (
        'misbirth_before_11', 'misbirth_before_12-21', 'therapeutic_abortion_before_12',
        'therapeutic_abortion', 'unknown_miscarriage'
    )


def _filter_premature_prev_preg(prev_preg):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением атрибута «Исход беременности» = преждевременные роды 22-27 недель или
    преждевременные роды 28-37 недель
    """
    return prev_preg.action['pregnancyResult'].value_raw in (
        'premature_birth_22-27', 'premature_birth_28-37'
    )


def _iter_preg_child(prev_pregs):
    for prev_preg in prev_pregs:
        for child in prev_preg.newborn_inspections:
            yield child


def _filter_child_miscarriage(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением в сведении о ребенке атрибута «Живой» = нет и в поле Умер в срок указано
    значение «интранатально» или «антенатально»
    """
    alive = safe_bool_none(child.alive)
    return alive is False and child.died_at_code in ('01', '05')


def _filter_child_death(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением в сведении о ребенке атрибута «Живой» = нет и в поле Умер в срок указано
    «7-27 дней»
    """
    alive = safe_bool_none(child.alive)
    return alive is False and child.died_at_code in ('03',)


def _filter_child_cong_prev_preg(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    с установленным флажком в сведении о ребенке атрибута Аномалии развития
    """
    abnormal_development = safe_bool_none(child.abnormal_development)
    return abnormal_development is True


def _filter_child_neuro_prev_preg(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    с установленным флажком в сведении о ребенке атрибута Неврологические нарушения
    """
    neurological_disorders = safe_bool_none(child.neurological_disorders)
    return neurological_disorders is True


def _filter_child_abnormal_weight(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    в сведении о ребенке со значением атрибута Масса,г  <2500 г или >4000 г
    """
    if child.weight is not None:
        return child.weight < 2500 or child.weight > 4000
    return False


def _mkb_match(where, mkb_list=None, needles=None):
    if mkb_list is not None:
        if not isinstance(mkb_list, (list, tuple)):
            mkb_list = (mkb_list, )
        return any(
            mkb in where for mkb in mkb_list
        )
    elif needles is not None:
        return any_thing(where, needles, lambda x: x)
    else:
        raise ValueError('need `mkb_list` or `needles` argument')


def _filter_prev_preg_compl(prev_preg):
    """
    На форме «Анамез пациентки» на вкладке "Сведения о предыдущих беременностях" записи
    со значением атрибута "Осложнения после родов/абортов" из узла О85-О92.
    """
    mkbs = [mkb.DiagID for mkb in prev_preg.action['after_birth_complications'].value]
    if mkbs:
        return _mkb_match(mkbs, needles=u'O85-O92.99')
    return False


def _filter_prev_preg_tubal(prev_preg):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением атрибута «Патологии беременности» = какому-либо коду МКБ из узла O00.
    """
    mkbs = [mkb.DiagID for mkb in prev_preg.action['pregnancy_pathology'].value]
    if mkbs:
        return _mkb_match(mkbs, needles=u'O00-O99.99')
    return False


def _theone_measure(card, measure_codes):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди measure_codes
    (среди некольких взять самое актуальное)
    """
    em_by_code = card.latest_measures_with_result
    theone = None
    for code in measure_codes:
        if code in em_by_code:
            rival = em_by_code[code]
            if theone is None or rival.begDateTime > theone.begDateTime:
                theone = rival
    return theone