# -*- coding: utf-8 -*-

import itertools

from .utils import (
    _iter_preg_child, _theone_measure,
    _filter_child_abnormal_weight, _filter_child_cong_prev_preg, _filter_child_death,
    _filter_child_miscarriage, _filter_child_neuro_prev_preg, _filter_misbirth_prev_preg,
    _filter_parity_prev_preg, _filter_premature_prev_preg, _filter_prev_preg_compl,
    _filter_prev_preg_tubal, _filter_misbirth_and_premature_prev_preg, _generator_abortion_first_trimester
)
from hippocrates.blueprints.risar.lib.utils import mkb_match as _mkb_match
from nemesis.lib.utils import safe_bool, safe_decimal


def mother_younger_18(card):
    return card.event.client.age_tuple()[3] < 18


def mother_older_40(card):
    return card.event.client.age_tuple()[3] >= 40


def father_older_40(card):
    anamnesis = card.anamnesis.father
    if anamnesis.id:
        return anamnesis['age'].value is not None and anamnesis['age'].value >= 40
    return False


def mother_professional_properties(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['professional_properties'].value_raw not in (None, 'psychic_tension', 'no')
    return False


def father_professional_properties(card):
    anamnesis = card.anamnesis.father
    if anamnesis.id:
        return anamnesis['professional_properties'].value_raw not in (None, 'no')
    return False


def mother_smoking(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return safe_bool(anamnesis['smoking'].value)
    return False


def mother_alcohol(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def mother_drugs(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return safe_bool(anamnesis.get_prop_value('drugs'))
    return False


def father_alcohol(card):
    anamnesis = card.anamnesis.father
    if anamnesis.id:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def father_drugs(card):
    anamnesis = card.anamnesis.father
    if anamnesis.id:
        return safe_bool(anamnesis.get_prop_value('drugs'))
    return False


def emotional_stress(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['professional_properties'].value_raw == 'psychic_tension'
    return False


def height_less_150(card):
    fi = card.primary_inspection
    if fi:
        return fi.action['height'].value is not None and \
               fi.action['height'].value <= 150
    return False


def height_less_158(card):
    fi = card.primary_inspection
    if fi:
        return fi.action['height'].value is not None and \
               fi.action['height'].value <= 158
    return False


def height_less_155(card):
    fi = card.primary_inspection
    if fi:
        return fi.action['height'].value is not None and \
               fi.action['height'].value <= 155
    return False


def overweight(card):
    fi = card.primary_inspection
    if fi:
        weight = fi.action['weight'].value
        height = fi.action['height'].value
        return weight is not None and height is not None and float(height - 100) * 1.25 < weight
    return False


def Rh_minus(card):
    """
    На форме с регистрационными данными пациентки или на форме "Ввод сведений о матери"
    отмечено значение группы крови = 0(I)Rh- или A(II)Rh- или B(III)Rh- или AB(IV)Rh-
    """
    blood_info = card.anamnesis.mother_blood_type
    return blood_info is not None and blood_info['rh'] == 'Rh(-)'


def not_married(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['marital_status'].value_raw in ('01', '02', '05', '06')
    return False


def parity_under_7(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 4 <= prev_pr_count <= 7


def parity_above_8(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 8 <= prev_pr_count


def parity_above_4(card):
    prev_pr_count = len(filter(_filter_parity_prev_preg, card.prev_pregs))
    return 4 <= prev_pr_count


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


def abortion_first_trimester(card):
    return any(_generator_abortion_first_trimester(card))


def intrauterine_operations(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return safe_bool(anamnesis['intrauterine'].value)
    return False


def premature_birth_1(card):
    premature_count = len(filter(_filter_premature_prev_preg, card.prev_pregs))
    return premature_count == 1


def premature_birth_more_2(card):
    premature_count = len(filter(_filter_premature_prev_preg, card.prev_pregs))
    return premature_count >= 2


def premature_birth_second_trimester(card):
    prematures = filter(_filter_misbirth_and_premature_prev_preg, card.prev_pregs)
    return any(prev_pr for prev_pr in prematures
               if prev_pr.action['pregnancy_week'].value and 14 <= prev_pr.action['pregnancy_week'].value <= 27)


def preeclampsia_anamnesis(card):
    return any(prev_pr for prev_pr in card.prev_pregs
               if prev_pr.action['preeclampsia'].value)


def miscarriage(card):
    return any(
        itertools.ifilter(_filter_child_miscarriage, _iter_preg_child(card.prev_pregs))
    )


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


def child_death(card):
    return any(itertools.ifilter(
        _filter_child_death, _iter_preg_child(card.prev_pregs)
    ))


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


def infertility(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['infertility'].value
    return False


def infertility_less_4(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        if anamnesis['infertility'].value and anamnesis['infertility_period'].value is not None:
            return 2 <= anamnesis['infertility_period'].value <= 4
    return False


def infertility_more_5(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        if anamnesis['infertility'].value and anamnesis['infertility_period'].value is not None:
            return 5 <= anamnesis['infertility_period'].value
    return False


def uterus_oophoron_tumor(card):
    return _mkb_match(card.unclosed_mkbs | card.get_anamnesis_mkbs(), 'O34.1')


def insuficiencia_istmicocervical(card):
    return _mkb_match(card.unclosed_mkbs | card.get_anamnesis_mkbs(),
                      needles=u'O34.3, N88-N88.99, D25-D25.99, D26-D26.99')


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
    if anamnesis.id and '2' in anamnesis['contraception'].value_raw:
        return True

    return any(itertools.ifilter(
        _filter_prev_preg_compl, card.prev_pregs
    ))


def chronic_inflammation_tomsk(card):
    """
    На форме «Диагнозы случая» есть хотя бы один диагноз с кодом МКБ из списка N71 – N77
    """
    return _mkb_match(card.unclosed_mkbs, needles=u'N71-N77.99')


def birth_complications(card):
    """
    На на вкладке "Сведения о предыдущих беременностях" есть хотя бы одна запись со
    значением атрибута "Осложнения после родов/абортов" из узла О85-О92
    """
    return any(itertools.ifilter(
        _filter_prev_preg_compl, card.prev_pregs
    ))


def intrauterine_contraception(card):
    """
    На форме «Ввод сведений о матери» в поле «Сведения по контрацепции» выбрано значение «ВМС»
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id and '2' in anamnesis['contraception'].value_raw:
        return True

    return False


def tubal_pregnancy(card):
    return any(itertools.ifilter(
        _filter_prev_preg_tubal, card.prev_pregs
    ))


def extracorporal_fertilization(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['fertilization_type'].value_raw == '01'
    return False


def intracytoplasmic_sperm_injection(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['fertilization_type'].value_raw == '03'
    return False


def assisted_reproductive_technology(card):
    """
    На форме «Ввод сведений о матери» значением атрибута «Способ оплодотворения»
    выбрано любое значение, кроме "Естественный"
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['fertilization_type'].value_raw and \
               anamnesis['fertilization_type'].value_raw != '05'
    return False


def uterine_scar(card):
    return _mkb_match(card.unclosed_mkbs, 'O34.2')


def uterine_scar_1(card):
    """
    На форме "Ввод сведений о матери" в поле "Рубец на матке" выбрано значение "один"
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['uterine_scar'].value_raw and \
               anamnesis['uterine_scar'].value_raw == '01'
    return False


def uterine_scar_more_2(card):
    """
    На форме "Ввод сведений о матери" в поле "Рубец на матке" выбрано значение "два и более"
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['uterine_scar'].value_raw and \
               anamnesis['uterine_scar'].value_raw == '02'
    return False


def uterine_scar_lower_section(card):
    """
    На форме "Анамнез пациентки" в поле "Рубец на матке после операции" выбрано значение
    с кодом lower_section
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['uterine_scar_location'].value_raw and \
               anamnesis['uterine_scar_location'].value_raw == 'lower_section'
    return False


def uterine_scar_corporeal(card):
    """
    На форме "Анамнез пациентки" в поле "Рубец на матке после операции" выбрано значение
    с кодом corporeal
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['uterine_scar_location'].value_raw and \
               anamnesis['uterine_scar_location'].value_raw == 'corporeal'
    return False


def heart_disease(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'Q20.0-Q26.9, I05.0-I09.9, I34.0-I38, I42.0, O99.4')


def heart_disease_circulatory_embarrassment(card):
    """
    На форме "Анамнез пациентки" поставлен флажок "Пороки сердца с нарушением кровообращения"
    или на форме "Диагнозы случая" есть хотя бы один незакрытый диагноз из узлов I26-I28.
    """
    anamnesis = card.anamnesis.mother
    if anamnesis:
        if safe_bool(anamnesis['heart_disease'].value):
            return True
    return _mkb_match(card.unclosed_mkbs, needles=u'I26-I28.99')


def hypertensive_disease_1(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ из узла:
    I11 или I12 или  I13 или I15 или O10 или O11 и в уточняющем поле
    (справочник rbRisarHypertensiveDiseaseStage) выбрано значение с кодом 01
    """
    mkbs = u'I11-I11.99, I12-I12.99, I13-I13.99, I15-I15.99, O10-O10.99, O11-O11.99'
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=mkbs):
            if diag.mkb_details_code == '01':
                return True
    return False


def hypertensive_disease_2(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ из узла:
    I11 или I12 или  I13 или I15 или O10 или O11 и в уточняющем поле
    (справочник rbRisarHypertensiveDiseaseStage) выбрано значение с кодом 02
    """
    mkbs = u'I11-I11.99, I12-I12.99, I13-I13.99, I15-I15.99, O10-O10.99, O11-O11.99'
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=mkbs):
            if diag.mkb_details_code == '02':
                return True
    return False


def hypertensive_disease_3(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ из узла:
    I11 или I12 или  I13 или I15 или O10 или O11 и в уточняющем поле
    (справочник rbRisarHypertensiveDiseaseStage) выбрано значение с кодом 03
    """
    mkbs = u'I11-I11.99, I12-I12.99, I13-I13.99, I15-I15.99, O10-O10.99, O11-O11.99'
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=mkbs):
            if diag.mkb_details_code == '03':
                return True
    return False


def gestational_hypertension(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O13-O13.99')


def varicose(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'I83-I83.99, O22-O22.99')


def hypotensive_syndrome(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O26.5, I95-I95.99')


def renal_disease(card):
    return _mkb_match(card.get_anamnesis_mkbs(), needles=u'N00-N39.99')


def adrenal_disorders(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'C74.0, C74.1, C74.9, D35.0, E27.0-E27.9, Q89.1, E34.5, E25.0')


def adrenopathy(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'C74.0, C74.1, C74.9, D35.0, E27.0-E27.9, Q89.1, E34.5, E25.0')


def neurometabolic_endocrine_syndrome(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'N91-N91.99, N92.0-N92.3, N92.5, N92.6, N93-N93.99, Q87.4, E28-E28.99')


def diabetes(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'E10.0-E14.9, O24.0-O24.4, O24.9')


def diabetes_tomsk(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'E10.0-E14.9, O24.0, O24.1, O24.2, O24.3, O24.9')


def gestational_diabetes(card):
    return _mkb_match(card.unclosed_mkbs, u'O24.4')


def thyroid_disorders(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'C73, E00.0-E07.9, A18.8, O99.2')


def obesity(card):
    """
    На форме «Первичный осмотр» значение атрибута «Индекс массы тела» >=30
    или на форме "Диагнозы случая" присутствует хоть один диагноз из группы E65-E68
    """
    inspection = card.primary_inspection
    if inspection and inspection.action['BMI'].value is not None and \
            inspection.action['BMI'].value >= 30:
        return True
    return _mkb_match(card.unclosed_mkbs, needles=u'E65-E68.99')


def weight_deficit(card):
    """
    На форме «Первичный осмотр» значение атрибута «Индекс массы тела» < 18,5
    или на форме "Диагнозы случая" присутствует хоть один диагноз из группы E40-E46.
    """
    inspection = card.primary_inspection
    if inspection and inspection.action['BMI'].value is not None and \
            inspection.action['BMI'].value < 18.5:
        return True
    return _mkb_match(card.unclosed_mkbs, needles=u'E40-E46.99')


def anemia_70(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди нескольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение меньше или равно 70 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('hemoglobin'):
        val = theone.result_action['hemoglobin'].value
        return val is not None and val <= 70
    return False


def anemia_90(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди нескольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение меньше или равно 90 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('hemoglobin'):
        val = theone.result_action['hemoglobin'].value
        return val is not None and val <= 90
    return False


def anemia_100(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди нескольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение больше 90 г/л, но меньше или равно 100 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('hemoglobin'):
        val = theone.result_action['hemoglobin'].value
        return val is not None and 90 < val <= 100
    return False


def anemia_110(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди нескольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение больше 100 г/л, но меньше или равно 110 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('hemoglobin'):
        val = theone.result_action['hemoglobin'].value
        return val is not None and 100 < val <= 110
    return False


def coagulopathy(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'D65-D89.9, O46.0, O99.1')


def myopia(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'H44.2, H52.1, H40.0-H40.9, H43.1, H44.5, H46-H47.7, H33.0-H35.9')


def persistent_infection(card):
    return _mkb_match(
        card.unclosed_mkbs,
        needles=(u'B20.0-B24.99, R75-R75.99, A15-A19.9, A23.0-A23.9, B58-B58.99, '
                 u'B18.0-B19.9, Z21-Z21.99, Z22.5, O98.0-O98.9, K73-K73.99')
    )


def lupus_anticoagulant_positive(card):
    """
    В мероприятиях пациентки есть мероприятие, у которого код 0062
    (среди некольких взять самое актуальное) и в данном мероприятии есть свойство
    с кодом lupus_anticoagulant  и его значение = "положительно"
    """
    measure_codes = ['0062']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('lupus_anticoagulant'):
        val = theone.result_action['lupus_anticoagulant'].value
        return val == u'положительно'
    return False


def antiphospholipid_antibodies_IgG(card):
    """
    В мероприятиях пациентки есть мероприятие, у которого код 0062
    (среди нескольких взять самое актуальное) и в данном мероприятии есть свойство
    с кодом anti_phosphotide_G , значение которого больше, либо равно 9,99
    """
    measure_codes = ['0062']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('anti_phosphotide_G'):
        val = theone.result_action['anti_phosphotide_G'].value
        return val is not None and val >= safe_decimal('9.99')
    return False


def antiphospholipid_antibodies_IgM(card):
    """
    В мероприятиях пациентки есть мероприятие, у которого код 0062
    (среди нескольких взять самое актуальное) и в данном мероприятии есть свойство
    с кодом anti_phosphotide_M , значение которого больше, либо равно 9,99
    """
    measure_codes = ['0062']
    theone = _theone_measure(card, measure_codes)
    if theone and theone.result_action.has_property('anti_phosphotide_M'):
        val = theone.result_action['anti_phosphotide_M'].value
        return val is not None and val >= safe_decimal('9.99')
    return False


def early_pregnancy_toxemia(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O21.0, O21.1')


def recurrent_threatened_miscarriage(card):
    """
    Если у пациентки на форме "Диагнозы случая" есть диагноз с кодом МКБ «O20.0»:
     * открытый, повторяющийся в 2 и более осмотрах акушером-гинекологом/специалистом ПЦ подряд
     * либо есть один и более закрытых и один открытый
     * либо 2 и более закрытых
    """
    inspection_diagnoses = card.get_inspection_diagnoses()
    inspections_by_mkb = {}
    for action_id, mkbs in inspection_diagnoses.iteritems():
        for mkb in mkbs:
            inspections_by_mkb.setdefault(mkb, set()).add(action_id)
    return 'O20.0' in inspections_by_mkb and len(inspections_by_mkb['O20.0']) >= 2


def threatened_miscarriage(card):
    """
    Если у пациентки на форме "Диагнозы случая" есть диагноз с кодом МКБ «O20.0»:
     * либо есть один и более закрытых и один открытый
     * либо 2 и более закрытых
    """
    inspection_diagnoses = card.get_inspection_diagnoses()
    inspections_by_mkb = {}
    for action_id, mkbs in inspection_diagnoses.iteritems():
        for mkb in mkbs:
            inspections_by_mkb.setdefault(mkb, set()).add(action_id)
    return 'O20.0' in inspections_by_mkb and len(inspections_by_mkb['O20.0']) >= 2


def edema_disease(card):
    if _mkb_match(card.unclosed_mkbs, needles=u'O12.0'):
        return True
    latest_inspection = card.latest_inspection
    if latest_inspection:
        return latest_inspection.action['complaints'].value_raw is not None and \
            'oteki' in latest_inspection.action['complaints'].value_raw
    return False


def gestosis_mild_case(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O13-O13.99')


def gestosis_moderately_severe(card):
    return _mkb_match(card.unclosed_mkbs, u'O14.0')


def gestosis_severe(card):
    return _mkb_match(card.unclosed_mkbs, u'O14.1')


def preeclampsia(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O14-O14.99')


def preeclampsia_moderate(card):
    return _mkb_match(card.unclosed_mkbs, u'O14.0')


def preeclampsia_hard(card):
    return _mkb_match(card.unclosed_mkbs, u'O14.1')


def eclampsia(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O15.0, O15.9')


def renal_disease_exacerbation(card):
    return _mkb_match(card.unclosed_mkbs, u'O23.0')


def emerging_infection_diseases(card):
    return _mkb_match(
        card.unclosed_mkbs,
        needles=(u'A51.0-A64.99, B00.0-B09.99, B15.0-B17.8, B25.0-B34.9, B50.0-B64.99, '
                 u'J00-J06.9, J10-J11.9, N30.0, N34.0-N34.99, O85-O85.99, O86.0-O86.8, '
                 u'A34-A34.99, O75.3, O98.9, O23.1-O23.9')
    )


def bleeding_1(card):
    return _mkb_match(card.unclosed_mkbs, u'O20.8')


def bleeding_2(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O46-O46.99')


def Rh_hypersusceptibility(card):
    return _mkb_match(card.unclosed_mkbs, u'O36.0')


def ABO_hypersusceptibility(card):
    return _mkb_match(card.unclosed_mkbs, u'O36.1')


def hydramnion(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O40-O40.99')


def hydramnion_saratov(card):
    # can be changed later
    return hydramnion(card)


def hydramnion_moderate(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O40
    и для данного диагноза в уточняющем поле выбрано значение с кодом 01
    (справочник rbRisarHydramnionStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], 'O40'):
            if diag.mkb_details_code == '01':
                return True
    return False


def hydramnion_hard(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O40
    и для данного диагноза в уточняющем поле выбрано значение с кодом 02
    (справочник rbRisarHydramnionStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], 'O40'):
            if diag.mkb_details_code == '02':
                return True
    return False


def oligohydramnios(card):
    return _mkb_match(card.unclosed_mkbs, u'O41.0')


def oligohydramnios_saratov(card):
    # can be changed later
    return oligohydramnios(card)


def oligohydramnios_moderate(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O41.0
    и для данного диагноза в уточняющем поле выбрано значение с кодом 01
    (справочник rbRisarOligohydramnionStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], 'O41.0'):
            if diag.mkb_details_code == '01':
                return True
    return False


def oligohydramnios_hard(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O41.0
    и для данного диагноза в уточняющем поле выбрано значение с кодом 02
    (справочник rbRisarOligohydramnionStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], 'O41.0'):
            if diag.mkb_details_code == '02':
                return True
    return False


def pelvic_station(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O32.1, O33-O33.99')


def pelvic_station_common(card):
    return _mkb_match(card.unclosed_mkbs, u'O32.1')


def multiple_pregnancy(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O30-O30.99')


def multiple_pregnancy_2(card):
    return _mkb_match(card.unclosed_mkbs, u'O30.0')


def multiple_pregnancy_3(card):
    return _mkb_match(card.unclosed_mkbs, u'O30.1')


def prolonged_pregnancy(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O48-O48.99')


def abnormal_fetus_position(card):
    return _mkb_match(card.unclosed_mkbs, u'O32.2')


def maternal_passages_immaturity(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['immaturity'].value)
    return False


def beta_HCG_increase(card):
    # later
    return False


def beta_HCG_decrease(card):
    # later
    return False


def alpha_fetoprotein_increase(card):
    # later
    return False


def alpha_fetoprotein_decrease(card):
    # later
    return False


def PAPP_A_increase(card):
    # later
    return False


def PAPP_A_decrease(card):
    # later
    return False


def small_gestational_age_fetus_1(card):
    """
    В последнем повторном осмотре акушером-гинекологом значение атрибута
    "Задержка роста плода" = до 2 недель
    """
    latest_inspection = card.latest_rep_inspection
    if latest_inspection:
        return any(fetus.delay_code == '01' for fetus in latest_inspection.fetuses)
    return False


def small_gestational_age_fetus_2(card):
    """
    В последнем повторном осмотре акушером-гинекологом значение атрибута
    "Задержка роста плода" = от 2 до 4 недель
    """
    latest_inspection = card.latest_rep_inspection
    if latest_inspection:
        return any(fetus.delay_code == '03' for fetus in latest_inspection.fetuses)
    return False


def small_gestational_age_fetus_2plus(card):
    """
    В последнем повторном осмотре акушером-гинекологом значение атрибута
    "Задержка роста плода" = "от 2 до 4 недель" или "более 4 недель"
    """
    latest_inspection = card.latest_rep_inspection
    if latest_inspection:
        return any(fetus.delay_code in ('03', '02') for fetus in latest_inspection.fetuses)
    return False


def small_gestational_age_fetus_3(card):
    """
    В последнем повторном осмотре акушером-гинекологом значение атрибута
    "Задержка роста плода" = более 4 недель
    """
    latest_inspection = card.latest_rep_inspection
    if latest_inspection:
        return any(fetus.delay_code == '02' for fetus in latest_inspection.fetuses)
    return False


def developmental_defect(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O35-O35.99')


def chronical_placental_insufficiency(card):
    return _mkb_match(card.unclosed_mkbs, u'O36.3')


def central_placental_presentation(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O44.0 или O44.1
    и для данного диагноза в уточняющем поле выбрано значение с кодом 01 или 02 или 03
    (справочник rbRisarPlacentalPresentationStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=u'O44.0, O44.1'):
            if diag.mkb_details_code in ('01', '02', '03'):
                return True
    return False


def placental_maturity_2(card):
    # as intended
    return False


def placental_maturity_3(card):
    # as intended
    return False


def low_insertion_of_placenta(card):
    """
    На форме «Диагнозы случая» есть незакрытый диагноз с кодом МКБ: O44.0 или O44.1
    и для данного диагноза в уточняющем поле выбрано значение с кодом 04
    (справочник rbRisarPlacentalPresentationStage)
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=u'O44.0, O44.1'):
            if diag.mkb_details_code == '04':
                return True
    return False


def placental_perfusion_disorder_1(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ O43.8 или O43.9
    и в уточняющем поле (справочник rbRisarPlacentalPerfusionDisorderStage)
    выбрано значение с кодом 01
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=u'O43.8, O43.9'):
            if diag.mkb_details_code == '01':
                return True
    return False


def placental_perfusion_disorder_2(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ O43.8 или O43.9
    и в уточняющем поле (справочник rbRisarPlacentalPerfusionDisorderStage)
    выбрано значение с кодом 02
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=u'O43.8, O43.9'):
            if diag.mkb_details_code == '02':
                return True
    return False


def placental_perfusion_disorder_3(card):
    """
    На форме «Диагнозы случая» есть хоть один незакрытый диагноз с кодом МКБ O43.8 или O43.9
    и в уточняющем поле (справочник rbRisarPlacentalPerfusionDisorderStage)
    выбрано значение с кодом 03
    """
    for mkb, diag in card.diags_by_mkb.iteritems():
        if _mkb_match([mkb], needles=u'O43.8, O43.9'):
            if diag.mkb_details_code == '03':
                return True
    return False


def placental_perfusion_disorder_1_saratov(card):
    # can be changed later
    return placental_perfusion_disorder_1(card)


def placental_perfusion_disorder_2_saratov(card):
    # can be changed later
    return placental_perfusion_disorder_2(card)


def placental_perfusion_disorder_3_saratov(card):
    # can be changed later
    return placental_perfusion_disorder_3(card)


def placental_presentation(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O44.0, O44.1')


def cardiotocography_more_7(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов >7
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return min(fetuses_ktg_points) > 7
    return False


def cardiotocography_6(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов = 6
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return min(fetuses_ktg_points) == 6
    return False


def cardiotocography_5(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов = 5
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return min(fetuses_ktg_points) == 5
    return False


def cardiotocography_4(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов = 4
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return min(fetuses_ktg_points) == 4
    return False


def cardiotocography_less_4(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов < 4
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return min(fetuses_ktg_points) < 4
    return False


def cardiotocography_between_7_and_8(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов >7, но <= 8
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return 7 < min(fetuses_ktg_points) <= 8
    return False


def cardiotocography_between_7_and_6(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов <=7, но >6
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return 6 < min(fetuses_ktg_points) <= 7
    return False


def cardiotocography_between_6_and_5(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов <=6, но >5
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return 5 < min(fetuses_ktg_points) <= 6
    return False


def cardiotocography_between_5_and_4(card):
    """
    Если в последнем, где были введены данные КТГ, осмотре акушером-гинекологом
    наименьшее значение атрибута "Оценка КТГ по Фишеру" среди всех плодов <=5, но >=4
    """
    latest_inspection = card.latest_inspection_fetus_ktg
    if latest_inspection:
        fetuses_ktg_points = [
            fetus.fisher_ktg_points
            for fetus in latest_inspection.fetuses
            if fetus.fisher_ktg_points is not None
        ]
        if fetuses_ktg_points:
            return 4 <= min(fetuses_ktg_points) <= 5
    return False


def meconium_amniotic_fluid(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['meconium_colouring'].value)
    return False


def predelivery_amniorrhea_before_labour(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['pre_birth_delivery_waters'].value)
    return False


def pathological_preliminary_period(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['patologicsl_preliminal_period'].value)
    return False


def labour_anomaly(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['labor_anomalies'].value)
    return False


def chorioamnionitis(card):
    epicrisis = card.epicrisis
    if epicrisis.action.id:
        return safe_bool(epicrisis.action['chorioamnionit'].value)
    return False


def adnexal_affection(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'N70-N70.99')


def cervix_uteri_length_less_25(card):
    """
    На форме "Первичный осмотр беременной" или "Повторный осмотр беременной" или
    "Осмотр специалистом ПЦ" в поле "Длина шейки матки" выбрано значение "менее 25 мм"
    """
    return any(insp for insp in card.checkups
               if insp['cervix_length'].value_raw and
                  insp['cervix_length'].value_raw == 'cervix_uteri_length_less_25')


def hellp(card):
    return _mkb_match(card.unclosed_mkbs, u'O14.2')


def fetal(card):
    return _mkb_match(card.unclosed_mkbs, u'O43.0')


def pregnancy_after_corrective_surgery(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O34.6, O34.7, O34.8, O34.9')


def pneumology(card):
    return _mkb_match(card.unclosed_mkbs, u'O99.5')


def respiratory_disturbance(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'J96.0, J96.1, J96.9, R09.2')


def vegetovascular_dystonia(card):
    # as intended
    return False


def thrombosis(card):
    """
    На форме «Диагнозы случая» или на форме "Сведения о матери" в поле "Текущие заболевания" или
    "Перенесённые заболевания" есть хоть один незакрытый диагноз с кодом МКБ из списка.
    """
    mkb_list = (
        u'I23.6, I24.0, I26-I26.99, I51.3, I63-I63.99, I67.6, I74-I74.99, I80-I80.99, '
        u'I81-I81.99, I82-I82.99, I87.0, G08-G08.99, K75.1, O03.2, O03.7, O04.2, O04.7, '
        u'O05.2, O05.7, O06.2, O06.7, O07.2, O07.7, O08.2, O08.7, O22.2, O22.3, O22.4, '
        u'K64-K64.99, O22.5, O22.8, O22.9, O87.1, O87.3, O88-O88.99'
    )
    return _mkb_match(card.unclosed_mkbs | card.get_anamnesis_mkbs(), needles=mkb_list)


def glomerulonephritis(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'N00-N00.99, N01-N01.99, N03-N03.99, N18-N18.99')


def solitary_paired(card):
    """
    На форме "Ввод сведений о матери" отмечен флажок "Единственная почка".
    """
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis.get_prop_value('solitary_paired')
    return False


def thrombocytopenia(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'D69-D69.99')


def nervous_disorder(card):
    """
    На форме "Сведения о матери" в полях "Перенесенные заболевания" или "Текущие заболевания"
    есть хотя бы один диагноз из списка: G40, G41, G83.3, F80.3, I60-I67, R56.8
    """
    return _mkb_match(card.get_anamnesis_mkbs(),
                      needles=u'G40-G40.99, G41-G41.99, G83.3, F80.3, I60-I67.99, R56.8')


def malignant_tumor(card):
    """
    На форме "Сведения о матери" в полях "Перенесенные заболевания" или "Текущие заболевания"
    или в открытых диагнозах пациентки есть хотя бы один диагноз из списка кодов МКБ класса С
    """
    mkb_list = u'C00-C99.99'
    return _mkb_match(card.unclosed_mkbs | card.get_anamnesis_mkbs(), needles=mkb_list)


def aneurysm(card):
    return _mkb_match(card.unclosed_mkbs,
                      needles=u'I28.1, I71-I71.99, I72-I72.99, I79.0, Q27.3, I77.0, I67.1, I25.4, I25.3')


def trauma(card):
    """
    На форме "Сведения о матери" в полях "Перенесенные заболевания" или "Текущие заболевания"
    есть хотя бы один диагноз из списка кодов МКБ: S02-S0.4, S06-S09, S32-S34
    """
    return _mkb_match(card.get_anamnesis_mkbs(), needles=u'S02-S04.99, S06-S09.99, S32-S34.99')
