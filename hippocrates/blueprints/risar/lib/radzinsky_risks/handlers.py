# -*- coding: utf-8 -*-

import itertools

from nemesis.lib.utils import safe_bool, safe_bool_none


def mother_younger_18(card):
    return card.event.client.age_tuple()[3] < 18


def mother_older_40(card):
    return card.event.client.age_tuple()[3] >= 18


def father_older_40(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return anamnesis['age'].value is not None and anamnesis['age'].value >= 40
    return False


def mother_professional_properties(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['professional_properties'].value is not None and \
               anamnesis['professional_properties'].value_raw != 'psychic_tension'
    return False


def father_professional_properties(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return anamnesis['professional_properties'].value is not None
    return False


def mother_smoking(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return safe_bool(anamnesis['smoking'].value)
    return False


def mother_alcohol(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def father_alcohol(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def emotional_stress(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['professional_properties'].value_raw == 'psychic_tension'
    return False


def height_less_150(card):
    fi = card.first_inspection
    if fi:
        return fi['height'].value is not None and \
               fi['height'].value <= 150
    return False


def overweight(card):
    fi = card.first_inspection
    if fi:
        weight = fi['weight'].value
        height = fi['height'].value
        return weight is not None and height is not None and float(height - 100) * 1.25 < weight
    return False


def not_married(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['marital_status'].value_raw in ('01', '02', '05', '06')
    return False


def _filter_parity_prev_preg(prev_preg):
    """
    На форме «Анамнез пациентки» на вкладке «Сведения о преыдущих беременностях»,
    у которых атрибут «Исход беременности» = преждевременные роды 22-27 недель
    или преждевременные роды 28-37 недель или запоздалые роды или роды в срок.
    """
    return prev_preg.action['pregnancyResult'].value_raw in (
        'premature_birth_22-27', 'premature_birth_28-37', 'postmature_birth', 'delivery'
    )


def parity_under_7(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 4 <= prev_pr_count <= 7


def parity_above_8(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 8 <= prev_pr_count


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

def abortion_1(card):
    parity_count_gt_zero = any(itertools.ifilter(_filter_parity_prev_preg, card.prev_pregs))
    misbirth_count = len(filter(_filter_misbirth_prev_preg, card.prev_pregs))
    return not parity_count_gt_zero and misbirth_count == 1


def abortions_2(card):
    parity_count_gt_zero = any(itertools.ifilter(_filter_parity_prev_preg, card.prev_pregs))
    misbirth_count = len(filter(_filter_misbirth_prev_preg, card.prev_pregs))
    return not parity_count_gt_zero and misbirth_count == 2


def abortions_more_3(card):
    parity_count_gt_zero = any(itertools.ifilter(_filter_parity_prev_preg, card.prev_pregs))
    misbirth_count = len(filter(_filter_misbirth_prev_preg, card.prev_pregs))
    return not parity_count_gt_zero and misbirth_count >= 3


def abortion_after_last_delivery_more_3(card):
    parity_count_gt_zero = any(itertools.ifilter(_filter_parity_prev_preg, card.prev_pregs))
    misbirth_count = len(filter(_filter_misbirth_prev_preg, card.prev_pregs))
    return parity_count_gt_zero and misbirth_count >= 3


def intrauterine_operations(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return safe_bool(anamnesis['intrauterine'].value)
    return False


def _filter_premature_prev_preg(prev_preg):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением атрибута «Исход беременности» = преждевременные роды 22-27 недель или
    преждевременные роды 28-37 недель
    """
    return prev_preg.action['pregnancyResult'].value_raw in (
        'premature_birth_22-27', 'premature_birth_28-37'
    )


def premature_birth_1(card):
    premature_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return premature_count == 1


def premature_birth_more_2(card):
    premature_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return premature_count >= 2


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


def miscarriage_1(card):
    miscarriage_count = len(list(
        itertools.ifilter(_filter_child_miscarriage, _iter_preg_child(card.prev_pregs))
    ))
    return miscarriage_count == 1


def miscarriage_more_2(card):
    miscarriage_count = len(list(
        itertools.ifilter(_filter_child_miscarriage, _iter_preg_child(card.prev_pregs))
    ))
    return miscarriage_count >= 2


def _filter_child_death(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    со значением в сведении о ребенке атрибута «Живой» = нет и в поле Умер в срок указано
    «7-27 дней»
    """
    alive = safe_bool_none(child.alive)
    return alive is False and child.died_at_code in ('03',)


def child_death_1(card):
    ch_d_count = len(list(itertools.ifilter(
        _filter_child_death, _iter_preg_child(card.prev_pregs)
    )))
    return ch_d_count == 1


def child_death_more_2(card):
    ch_d_count = len(list(itertools.ifilter(
        _filter_child_death, _iter_preg_child(card.prev_pregs)
    )))
    return ch_d_count >= 2


def _filter_child_cong_prev_preg(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    с установленным флажком в сведении о ребенке атрибута Аномалии развития
    """
    abnormal_development = safe_bool_none(child.abnormal_development)
    return abnormal_development is True


def congenital_disorders(card):
    cong_gt_zero = any(itertools.ifilter(
        _filter_child_cong_prev_preg, _iter_preg_child(card.prev_pregs)
    ))
    return cong_gt_zero


def _filter_child_neuro_prev_preg(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    с установленным флажком в сведении о ребенке атрибута Неврологические нарушения
    """
    neurological_disorders = safe_bool_none(child.neurological_disorders)
    return neurological_disorders is True


def neurological_disorders(card):
    neuro_gt_zero = any(itertools.ifilter(
        _filter_child_neuro_prev_preg, _iter_preg_child(card.prev_pregs)
    ))
    return neuro_gt_zero


def _filter_child_abnormal_weight(child):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях» записи
    в сведении о ребенке со значением атрибута Масса,г  <2500 г или >4000 г
    """
    if child.weight is not None:
        return child.weight < 2500 or child.weight > 4000
    return False


def abnormal_child_weight(card):
    abn_weight_gt_zero = any(itertools.ifilter(
        _filter_child_abnormal_weight, _iter_preg_child(card.prev_pregs)
    ))
    return abn_weight_gt_zero


def infertility_less_4(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        if anamnesis['infertility'].value and anamnesis['infertility_period'].value is not None:
            return 2 <= anamnesis['infertility_period'].value <= 4
    return False


def infertility_more_5(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        if anamnesis['infertility'].value and anamnesis['infertility_period'].value is not None:
            return 5 <= anamnesis['infertility_period'].value
    return False


def uterine_scar(card):
    return 'O34.2' in card.unclosed_mkbs


def uterus_oophoron_tumor(card):
    return 'O34.1' in card.unclosed_mkbs


def insuficiencia_istmicocervical(card):
    return 'O34.3' in card.unclosed_mkbs


def uterine_malformations(card):
    return any(mkb in card.unclosed_mkbs for mkb in ('O34.0', 'O34.4'))


def chronic_inflammation(card):
    """
    На форме «Диагнозы случая» есть хотя бы один диагноз с кодом МКБ из списка
    N70 – N77 или на форме «Ввод сведений о матери» в поле «Сведения по контрацепции»
    выбрано значение «ВМС» или на на вкладке "Сведения о предыдущих беременностях"
    есть хотя бы одна запись со значением атрибута "Осложнения после родов/абортов"
    из узла О85-О92.
    """
    # TODO
    return False


def tubal_pregnancy(card):
    """
    На форме «Анамез пациентки» на вкладке «Сведения о предыдущих беременностях»
    есть хотя бы одна запись со значением атрибута
    «Патологии беременности» = какому-либо коду МКБ из узла O00.
    """
    return False


def extracorporal_fertilization(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['fertilization_type'].value_raw == '01'
    return False


def intracytoplasmic_sperm_injection(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['fertilization_type'].value_raw == '03'
    return False
