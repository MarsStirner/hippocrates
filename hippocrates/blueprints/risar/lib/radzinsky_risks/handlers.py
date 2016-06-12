# -*- coding: utf-8 -*-

import itertools

from .utils import (
    _iter_preg_child, _mkb_match, _theone_measure,
    _filter_child_abnormal_weight, _filter_child_cong_prev_preg, _filter_child_death,
    _filter_child_miscarriage, _filter_child_neuro_prev_preg, _filter_misbirth_prev_preg,
    _filter_parity_prev_preg, _filter_premature_prev_preg, _filter_prev_preg_compl,
    _filter_prev_preg_tubal
)
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


def father_alcohol(card):
    anamnesis = card.anamnesis.father
    if anamnesis.id:
        return safe_bool(anamnesis['alcohol'].value)
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


def overweight(card):
    fi = card.primary_inspection
    if fi:
        weight = fi.action['weight'].value
        height = fi.action['height'].value
        return weight is not None and height is not None and float(height - 100) * 1.25 < weight
    return False


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
    if anamnesis.id:
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
    if anamnesis.id and '2' in anamnesis['contraception'].value_raw:
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
    if anamnesis.id:
        return anamnesis['fertilization_type'].value_raw == '01'
    return False


def intracytoplasmic_sperm_injection(card):
    anamnesis = card.anamnesis.mother
    if anamnesis.id:
        return anamnesis['fertilization_type'].value_raw == '03'
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
        return safe_bool(anamnesis['heart_disease'].value)
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
    return _mkb_match(card.unclosed_mkbs, needles=u'E10.0-E14.9, O24.0-O24.4, O24.9')


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


def anemia_90(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди некольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение меньше или равно 90 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and 'hemoglobin' in theone.result_action.propsByCode:
        val = theone.result_action['hemoglobin'].value
        return val is not None and val <= 90
    return False


def anemia_100(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди некольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение больше 90 г/л, но меньше или равно 100 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and 'hemoglobin' in theone.result_action.propsByCode:
        val = theone.result_action['hemoglobin'].value
        return val is not None and 90 < val <= 100
    return False


def anemia_110(card):
    """
    В мероприятиях пациентки есть любое мероприятие, у которого код среди следующих:
    0010, 0035, 0284, 0128 (среди некольких взять самое актуальное) и в данном мероприятии
    есть свойство с кодом hemoglobin и его значение больше 100 г/л, но меньше или равно 110 г/л
    """
    measure_codes = ['0010', '0035', '0284', '0128']
    theone = _theone_measure(card, measure_codes)
    if theone and 'hemoglobin' in theone.result_action.propsByCode:
        val = theone.result_action['hemoglobin'].value
        return val is not None and 100 < val <= 110
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
    """
    В мероприятиях пациентки есть мероприятие, у которого код 0062
    (среди некольких взять самое актуальное) и в данном мероприятии есть свойство
    с кодом lupus_anticoagulant  и его значение = "положительно"
    """
    measure_codes = ['0062']
    theone = _theone_measure(card, measure_codes)
    if theone and 'lupus_anticoagulant' in theone.result_action.propsByCode:
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
    if theone and 'anti_phosphotide_G' in theone.result_action.propsByCode:
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
    if theone and 'anti_phosphotide_M' in theone.result_action.propsByCode:
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
    return _mkb_match(card.unclosed_mkbs, u'O14.9')


def eclampsia(card):
    return _mkb_match(card.unclosed_mkbs, u'O15.0')


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


def oligohydramnios(card):
    return _mkb_match(card.unclosed_mkbs, u'O41.0')


def pelvic_station(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O32.1, O33-O33.99')


def multiple_pregnancy(card):
    return _mkb_match(card.unclosed_mkbs, needles=u'O30-O30.99')


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


def small_gestational_age_fetus_3(card):
    """
    В последнем повторном осмотре акушером-гинекологом значение атрибута
    "Задержка роста плода" = более 4 недель
    """
    latest_inspection = card.latest_rep_inspection
    if latest_inspection:
        return any(fetus.delay_code == '02' for fetus in latest_inspection.fetuses)
    return False


def chronical_placental_insufficiency(card):
    return _mkb_match(card.unclosed_mkbs, u'O36.3')


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
