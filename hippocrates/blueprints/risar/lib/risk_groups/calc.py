# -*- coding: utf-8 -*-

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.risk_groups.needles_haystacks import any_thing, mkb_from_mkb, hay_check, explode_needles
from blueprints.risar.lib.utils import get_action_list
from nemesis.models.actions import Action
from nemesis.models.client import BloodHistory

__author__ = 'viruzzz-kun'


def get_mother_bt(event):
    return BloodHistory.query \
        .filter(BloodHistory.client_id == event.client_id) \
        .order_by(BloodHistory.bloodDate.desc()) \
        .first()


def calc_risk_groups(event):
    card = PregnancyCard.get_for_event(event)

    hemoglobin_action = get_action_list(event, 'general_blood_test').order_by(Action.begDate.desc()).first()
    low_hemo = hemoglobin_action['hemoglobin'].value <= 110 if hemoglobin_action is not None else False

    # 01 - Невынашивание беременности

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'О26.2, M95.5, E07.9, E27.9, E28.9, Е30.0, N70.0, N70.1, N70.9, N71.0, N71.1, N71.9, N76.1, N85.8, N96',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O10-O15, O20.0, O30, O33.1, O34.0, O34.1, O34.2, O34.3, O34.8, O35.0-O35.9, O98-O99, Z35.5, Z35.6')
    p2 = True  # TODO: В диагнозах случая (всех)
    p3 = any(preg['pregnancyResult'].value_raw in ('miscarriage27', 'miscarriage37') for preg in card.prev_pregs)
    p4_needles = explode_needles(u'O10-O84, O00-O08')
    p4_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p4_needles)
        for preg in card.prev_pregs
    )
    p4_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p4_needles)
        for preg in card.prev_pregs
    )
    p5 = any(
        preg['maternity_aid'].value_raw == '05'  # Кесарево сечение
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3 or p4_a or p4_b or p5 or low_hemo:
        yield '01'

    # 02 - Развитие позднего токсикоза

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'O20-O26.9, I05-I09.9, I34.0-I38, I42.0, I11.0-I11.9, I10.0-I15.9, N00.0-N07, N10-N15.9, N17.0-N21.9, N25.0-N28.9, D50-D64, E66.8, E66.9, E10.0, E14.9',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O10-O16, Z35.5, Z35.6, O36.0, O30.0-O30.9, O23.0, O26.6, O24.0-O24.4, O24.9, O99.0')
    p2 = True
    p3_needles = explode_needles(u'O10-O92')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or low_hemo:
        yield '02'

    # 03 - Кровотечение в родах и послеродовом периоде

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'D65-D69, D50-D64',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O46.0, O46.8, O46.9, O43.0, O44.0, O44.1, O45.0, O45.8, O45.9, О99.0')
    p2 = True
    p3_needles = explode_needles(u'O72.0-O72.3, O03-O08')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p4 = any(
        preg['pregnancyResult'].value_raw in ('med_abortion12', 'med_abortion', 'misbirth', 'misbirth11', 'misbirth21')
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or p4 or low_hemo:
        yield '03'

    # 04 - Аномалия родовой деятельности

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'E07.9, E28, E30',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O34.1, O34.4, O34.8, O33.0-O33.4, O32.5, O30, O65, O83.1')
    p2 = True
    p3_needles = explode_needles(u'O00-O08, O82')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p4 = any(
        preg['pregnancyResult'].value_raw in ('med_abortion12', 'med_abortion', 'misbirth', 'misbirth11', 'misbirth21')
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or p4:
        yield '04'

    # 05 - Роды крупным плодом

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'E10.0-E14.9',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O24.0-O24.4, O24.9, O33.4, O36.6')
    p3_needles = explode_needles(u'O36.6')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3 = any(
        (preg['pregnancyResult'].value_raw == 'normal' and
         preg['pregnancy_week'] >= 36 and
         (max(child['weight'] for child in preg['newborn_inspections']) >= 4000))
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or p4:
        yield '05'

    # 06 - Развитие резус-конфликта

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'Z51.3',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O36.0')
    p2 = True  # TODO:
    if p1 or p2:
        yield '06'

    # 07 - Развитие групповой несовместимости

    # p1 и p2 идентичны предыдущей группе риска
    father_bt = card.anamnesis.father['blood_type'].value
    mother_bt = get_mother_bt(event)
    p3 = father_bt and mother_bt and mother_bt.bloodType.code in ('1-', '1+') and father_bt.code in ('2+', '2-','3+', '3-', '4+', '4-')
    if p1 or p2 or p3:
        yield '07'

    # 08 - Гипоксия плода

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'I11.0-I13.9, Q20.0-Q28.9, I05-I09, I34.0-I38, I42.0, E10-E14.9, J40-J47',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O10-O16, O23.0-O23.9, O24.0-O24.4, O24.9, O45, O48, O99.4, O99.5, O98.0-O98.9, O99.0')
    p2 = True
    p3_needles = explode_needles(u'O10-O16, O45, O99.0')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or low_hemo:
        yield '08'

    # 09 - Гипотрофия плода

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'E66.9, I11.0-I13.9',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O10-O15.9, O23.0, O36.3, O36.5, O43.8')
    p3 = any(
        (preg['pregnancyResult'].value_raw == 'normal' and
         preg['pregnancy_week'] >= 36 and
         (min(child['weight'] for child in preg['newborn_inspections']) <= 2500))
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3 or low_hemo:
        yield '09'

    # 10 - Несостоятельность рубца на матке

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'О34.2',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'О34.2, О20.0')
    p2 = True
    p3_needles = explode_needles(u'O82.0-O82.9')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b:
        yield '10'

    # 11 - Аномалия прикрепления плаценты

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'N70-N77',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O43.1, O44, O45.9')
    p2 = True
    p3_needles = explode_needles(u'O03-O08, O43, O44, O45')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p4 = any(
        preg['pregnancyResult'].value_raw in ('med_abortion12', 'med_abortion', 'misbirth', 'misbirth11', 'misbirth21')
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b or p4:
        yield '11'

    # 12 - Обострение хр.астматических заболеваний

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'J30-J99',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O98.0, O99.4, O99.5, O99.8, J00-J99')
    p2 = True
    p3_needles = explode_needles(u'J45, J46')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b:
        yield '12'

    # 13 - Септическое состояние в послеродовом периоде

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'N00-N39, N70-N77, N96',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O22, O23, O24, O26.6, O34.3')
    p2 = True
    p3_needles = explode_needles(u'O85, О86, O87, O91, O92')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    if p1 or p2 or p3_a or p3_b:
        yield '13'

    # 14 - Фетоплацентарная недостаточность

    p1 = any_thing(
        card.anamnesis.mother['current_diseases'].value,
        u'Z35.5, Z35.6, I11.0-I13.9, D50-D64, E66, E10.0-E14.9, N96, N97, J00-J99, D25, N80, Q51.1, N70-N77, N85',
        mkb_from_mkb
    )
    p2_needles = explode_needles(u'O10-O15.9, O20-O29, O26.6, O30, O32.1, O34.2, O36.0, O36.1, O41.0, O43, O44, O98')
    p2 = True
    p3_needles = explode_needles(u'О10-О92, O99.0')
    p3_a = any(
        hay_check(preg['pregnancy_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p3_b = any(
        hay_check(preg['delivery_pathology'].value_raw, p3_needles)
        for preg in card.prev_pregs
    )
    p4 = card.anamnesis.mother['alcohol'].value or \
         card.anamnesis.mother['toxic'].value or \
         card.anamnesis.mother['smoking'].value or \
         card.anamnesis.mother['drugs'].value
    p5 = card.anamnesis.mother['professional_properties'].value_raw not in (u'net', u'nervno-psihiceskoenaprajenie')
    p6 = any(
        child['died_at'].value_raw == '01'  # Умер при родах
        for preg in card.prev_pregs
        for child in preg
    )
    if p1 or p2 or p3_a or p3_b or p4 or p5 or p6 or low_hemo:
        yield '14'
