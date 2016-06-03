# -*- coding: utf-8 -*-

import itertools

from .utils import (
    _iter_preg_child, _mkb_match,
    _filter_child_abnormal_weight, _filter_child_cong_prev_preg, _filter_child_death,
    _filter_child_miscarriage, _filter_child_neuro_prev_preg, _filter_misbirth_prev_preg,
    _filter_parity_prev_preg, _filter_premature_prev_preg, _filter_prev_preg_compl,
    _filter_prev_preg_tubal
)
from nemesis.lib.utils import safe_bool


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


def parity_under_7(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 4 <= prev_pr_count <= 7


def parity_above_8(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 8 <= prev_pr_count


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


def premature_birth_1(card):
    premature_count = len(filter(_filter_premature_prev_preg, card.prev_pregs))
    return premature_count == 1


def premature_birth_more_2(card):
    premature_count = len(filter(_filter_premature_prev_preg, card.prev_pregs))
    return premature_count >= 2


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


def congenital_disorders(card):
    cong_gt_zero = any(itertools.ifilter(
        _filter_child_cong_prev_preg, _iter_preg_child(card.prev_pregs)
    ))
    return cong_gt_zero


def neurological_disorders(card):
    neuro_gt_zero = any(itertools.ifilter(
        _filter_child_neuro_prev_preg, _iter_preg_child(card.prev_pregs)
    ))
    return neuro_gt_zero


def abnormal_child_weight(card):
    abn_weight_gt_zero = any(itertools.ifilter(
        _filter_child_abnormal_weight, _iter_preg_child(
            prev_preg
            for prev_preg in card.prev_pregs
            if prev_preg.action['pregnancyResult'].value_raw == 'delivery'
        )
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
    return _mkb_match(card.unclosed_mkbs, 'O34.2')


def uterus_oophoron_tumor(card):
    return _mkb_match(card.unclosed_mkbs, 'O34.1')


def insuficiencia_istmicocervical(card):
    return _mkb_match(card.unclosed_mkbs, 'O34.3')


def uterine_malformations(card):
    return _mkb_match(card.unclosed_mkbs, ('O34.0', 'O34.4'))


def chronic_inflammation(card):
    """
    На форме «Диагнозы случая» есть хотя бы один диагноз с кодом МКБ из списка
    N70 – N77 или на форме «Ввод сведений о матери» в поле «Сведения по контрацепции»
    выбрано значение «ВМС» или на на вкладке "Сведения о предыдущих беременностях"
    есть хотя бы одна запись со значением атрибута "Осложнения после родов/абортов"
    из узла О85-О92.
    """
    if _mkb_match(card.unclosed_mkbs, needles=u'N70-N77.99'):
        return True

    anamnesis = card.anamnesis.mother
    if anamnesis and '2' in anamnesis['contraception'].value_raw:
        return True

    return any(itertools.ifilter(
        _filter_prev_preg_compl, card.prev_pregs
    ))


def tubal_pregnancy(card):
    return any(itertools.ifilter(
        _filter_prev_preg_tubal, card.prev_pregs
    ))


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


def heart_disease(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'Q20.0-Q26.9, I05.0-I09.9, I34.0-I38, I42.0, O99.4')


def heart_disease_circulatory_embarrassment(card):
    """
    На форме "Анамнез пациентки" поставлен флажок "Пороки сердца с нарушением кровообращения"
    или на форме "Диагнозы случая" есть хотя бы один незакрытый диагноз из узлов I26-I28.
    """
    # TODO: after anamnesis ticket
    # anamnesis = card.anamnesis.mother
    # if anamnesis:
    #     return safe_bool(anamnesis[<code>].value)
    return _mkb_match(card.unclosed_mkbs, needles=u'I26-I28.99')


def hypertensive_disease_1(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'I11-I11.99')


def hypertensive_disease_2(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'I12-I12.99')


def hypertensive_disease_3(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'I13-I13.99')


def varicose(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'I83-I83.99, O22-O22.99')


def hypotensive_syndrome(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O26.5, I95-I95.99')


def renal_disease(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'N00-N39.99')


def adrenal_disorders(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'C74.0, C74.1, C74.9, D35.0, E27.0-E27.9, Q89.1, E34.5, E25.0')


def neurometabolic_endocrine_syndrome(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'N91-N91.99, N92.0-N92.3, N92.5, N92.6, N93-N93.99, Q87.4, E28-E28.99')


def diabetes(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'E10.0-E14.9, O24.0-O24.4, О24.9')


def thyroid_disorders(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'C73, E00.0-E07.9, A18.8, O99.2')


def obesity(card):
    """
    На форме «Первичный осмотр» значение атрибута «Индекс массы тела» >=30
    или на форме "Диагнозы случая" присутствует хоть один диагноз из группы E65-E68
    """
    # TODO: first_inspection
    return _mkb_match(card.unclosed_mkbs, needles=u'E65.99-E68.99')


def anemia_90(card):
    # TODO: measures
    return False


def anemia_100(card):
    # TODO: measures
    return False


def anemia_110(card):
    # TODO: measures
    return False


def coagulopathy(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'D65-D89.9, O46.0, O99.1')


def myopia(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'H44.2, H52.1, H40.0-H40.9, H43.1, H44.5, H46-H47.7, H33.0-H35.9, O99.8')


def persistent_infection(card):
    return _mkb_match(
        card.unclosed_mkbs,
        needles=(u'B20.0-B24, R75-R75.99, A15-A19.9, A23.0-A23.9, B58-B58.99, '
                 u'B18.0-B19.9, Z21-Z21.99, Z22.5, O98.0-O98.9')
    )


def lupus_anticoagulant_positive(card):
    # TODO: measures
    return False


def antiphospholipid_antibodies_IgG(card):
    # TODO: measures
    return False


def antiphospholipid_antibodies_IgM(card):
    # TODO: measures
    return False
