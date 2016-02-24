# -*- coding: utf-8 -*-
import datetime

from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.lib.utils import get_action, get_action_list, HIV_diags, syphilis_diags, hepatitis_diags, \
    tuberculosis_diags, scabies_diags, pediculosis_diags, multiple_birth, hypertensia, kidney_diseases, collagenoses, \
    vascular_diseases, diabetes, antiphospholipid_syndrome, pregnancy_pathologies, risk_mkbs
from blueprints.risar.models.risar import RisarRiskGroup
from blueprints.risar.risar_config import checkup_flat_codes, risar_epicrisis
from nemesis.lib.jsonify import EventVisualizer
from nemesis.lib.utils import safe_dict
from nemesis.models.actions import Action, ActionType, ActionPropertyType, ActionProperty
from nemesis.models.enums import PregnancyPathology, PreeclampsiaRisk, PerinatalRiskRate
from nemesis.models.risar import rbPreEclampsiaRate
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


def get_pregnancy_week(event, action, date=None):
    """
    :type event: application.models.event.Event
    :type date: datetime.date | None
    :param event: Карточка пациентки
    :param date: Интересующая дата или None (тогда - дата окончания беременности)
    :return: число недель от начала беременности на дату
    """
    if action is None:
        action = PregnancyCard.get_for_event(event).attrs
    start_date = action['pregnancy_start_date'].value
    if date is None:
        date = action['predicted_delivery_date'].value
    if start_date:  # assume that date is not None
        if isinstance(date, datetime.datetime):
            date = date.date()
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        return (min(date, datetime.date.today()) - start_date).days / 7 + 1


def check_card_attrs_action_integrity(action):
    """
    Проверка, что в action, соответствующего атрибутам карточки, существуют
    все необходимые свойства.
    :param action: действие с атрибутами
    :type action: nemesis.models.actions.Action
    :return: None
    """
    property_type_codes = ['pregnancy_pathology_list', 'preeclampsia_susp', 'preeclampsia_comfirmed']
    for apt_code in property_type_codes:
        if apt_code not in action.propsByCode:
            create_property(action, apt_code)


def create_property(action, apt_code):
    prop_type = action.actionType.property_types.filter(
        ActionPropertyType.deleted == 0, ActionPropertyType.code == apt_code
    ).first()
    prop = ActionProperty()
    prop.type = prop_type
    prop.action = action
    prop.isAssigned = False
    if prop.type.defaultValue:
        prop.set_value(prop.type.defaultValue, True)
    else:
        prop.value = None
    action.properties.append(prop)


def default_AT_Heuristic():
    """
    Получение ActionType, соответствующего атрибутам карточки
    :rtype: ActionType | None
    """
    return ActionType.query.filter(ActionType.flatCode == u'cardAttributes').first()


def get_all_diagnoses(event):
    """
    Получание всех диагнозов по событию
    :param event: Событие
    :type event: nemesis.models.event.Event
    :return: list of DiagIDs
    """
    result = []
    evis = EventVisualizer()
    for action in event.actions:
        for prop in action.properties:
            if prop.type.typeName == u'Diagnosis' and prop.value:
                if prop.type.isVector:
                    for diagnostic in prop.value:
                        diag = evis.make_diagnostic_record(diagnostic)
                        diag['action_property'] = {'name': prop.type.name,
                                                   'code': prop.type.code}
                        result.append(diag)
                else:
                    diag = evis.make_diagnostic_record(prop.value)
                    diag['action_property'] = {'name': prop.type.name,
                                               'code': prop.type.code}
                    result.append(diag)
    result.sort(key=lambda x: x['set_date'])
    return result


def get_diagnoses_from_action(action, open=False):
    """
    Получание всех диагнозов по событию
    :param action: Действие
    :type action: nemesis.model.action.Action
    :return: list of
    """
    result = []
    evis = EventVisualizer()
    if action:
        for prop in action.properties:
            if prop.type.typeName == 'Diagnosis' and prop.value:
                if prop.type.isVector:
                    for diagnostic in prop.value:
                        if not open or not diagnostic.endDate:
                            diag = evis.make_diagnostic_record(diagnostic)
                            diag['action_property_name'] = prop.type.name
                            result.append(diag)
                else:
                    if not open or not prop.value.endDate:
                        diag = evis.make_diagnostic_record(prop.value)
                        diag['action_property_name'] = prop.type.name
                        result.append(diag)
        result.sort(key=lambda x: x['set_date'])
    return result


def reevaluate_risk_rate(card):
    """
    Пересчёт риска невынашивания
    :param card: Карточка беременной
    :type card: PregnancyCard
    """

    risk_rate_mkbs = risk_mkbs()
    high_rates = set(mkb['code'] for mkb in risk_rate_mkbs['high'])
    mid_rates = set(mkb['code'] for mkb in risk_rate_mkbs['medium'])
    low_rates = set(mkb['code'] for mkb in risk_rate_mkbs['low'])

    def diag_to_risk_rate(diag):
        """
        :type diag: nemesis.models.diagnosis.Diagnostic
        :param diag:
        :return:
        """
        diag_id = diag.MKB
        if diag_id in high_rates:
            return PerinatalRiskRate.high[0]
        elif diag_id in mid_rates:
            return PerinatalRiskRate.medium[0]
        elif diag_id in low_rates:
            return PerinatalRiskRate.low[0]
        return PerinatalRiskRate.undefined[0]

    max_rate = max(map(diag_to_risk_rate, card.get_client_diagnostics(card.event.setDate, card.event.execDate)) + [PerinatalRiskRate.undefined[0]])

    card.attrs['prenatal_risk_572'].value = safe_dict(PerinatalRiskRate(max_rate))


def reevaluate_preeclampsia_risk(card):
    """
    Пересчёт риска преэклампсии
    :param card: Карточка беременной
    :type card: PregnancyCard
    """
    delivery_years = []
    all_diagnoses = []
    diseases = multiple_birth + hypertensia + kidney_diseases + collagenoses + vascular_diseases + diabetes + \
        antiphospholipid_syndrome
    mother_action = card.anamnesis.mother
    first_inspection = get_action(card.event, 'risarFirstInspection')
    second_inspections = get_action_list(card.event, 'risarSecondInspection', all=True)
    actions_to_check = [mother_action]+[first_inspection]+second_inspections
    for action in actions_to_check:
        all_diagnoses.extend(get_diagnoses_from_action(action, True))

    prev_pregnancies = card.prev_pregs
    if not mother_action and not first_inspection and not prev_pregnancies:
        risk = PreeclampsiaRisk.undefined[0]
    else:
        risk = PreeclampsiaRisk.no_risk[0]

        if not prev_pregnancies or card.event.client.age_tuple()[-1] > 35 or (first_inspection and first_inspection['BMI'].value >= 25) or \
                (mother_action and mother_action['preeclampsia'].value):
            risk = PreeclampsiaRisk.has_risk[0]
        else:
            for pregnancy in prev_pregnancies:
                if pregnancy['pregnancyResult'].value and pregnancy['pregnancyResult'].value['code'] in ('normal', 'miscarriage37', 'miscarriage27', 'belated_birth'):
                    if pregnancy['preeclampsia'].value:
                        risk = PreeclampsiaRisk.has_risk[0]
                        break
                    delivery_years.append(pregnancy['year'].value)

            delivery_years.sort()
            if delivery_years and datetime.datetime.now().year - delivery_years[-1] >= 10:
                risk = PreeclampsiaRisk.has_risk[0]

        for diag in all_diagnoses:
            diag_id = diag['diagnosis']['mkb'].DiagID
            if filter(lambda x: x in diag_id, diseases):
                risk = PreeclampsiaRisk.has_risk[0]

    if card.attrs.propsByCode.get('preeclampsia_risk'):
        card.attrs['preeclampsia_risk'].value = risk


def reevaluate_dates(card):
    """
    Пересчёт даты начала беременности, предполагаемой даты родов, и даты редактирования карты пациентки
    :param card: Карточка беременной
    :type card: PregnancyCard
    :rtype: datetime.date
    :return:
    """
    now = datetime.datetime.now()

    card.attrs['chart_modify_date'].value = now
    card.attrs['chart_modify_time'].value = now
    prev_start_date, prev_delivery_date = card.attrs['pregnancy_start_date'].value, card.attrs['predicted_delivery_date'].value
    start_date, delivery_date, p_week = None, None, None
    epicrisis = get_action(card.event, risar_epicrisis)

    if epicrisis and epicrisis['pregnancy_duration'].value:
        # Установленная неделя беременности. Может быть как меньше, так и больше 40
        p_week = int(epicrisis['pregnancy_duration'].value)
        # вычисленная дата начала беременности
        start_date = (epicrisis['delivery_date'].value + datetime.timedelta(weeks=-p_week, days=1))
        # Точная дата окончания беременности - дата родоразрешения
        delivery_date = epicrisis['delivery_date'].value

    if not start_date:
        # Сначала смотрим по осмотрам, если таковые есть
        for inspection in get_action_list(card.event, checkup_flat_codes).order_by(Action.begDate.desc()):
            if inspection['pregnancy_week'].value:
                # Установленная неделя беременности. Может быть как меньше, так и больше 40
                p_week = int(inspection['pregnancy_week'].value)
                # вычисленная дата начала беременности
                new_start_date = (inspection.begDate.date() + datetime.timedelta(weeks=-p_week, days=1))
                # Не надо трогать дату начала беременности, если она не слишком отличается от предыдущей вычисленной
                start_date = (
                    new_start_date
                    if (prev_start_date is None or abs((new_start_date - prev_start_date).days) > 3)
                    else prev_start_date
                )
                break

    if not start_date:
        mother_action = card.anamnesis.mother
        if mother_action:
            # если есть анамнез матери, то находим дату начала беременности из него
            start_date = mother_action['menstruation_last_date'].value

    if not start_date:
        card.attrs['pregnancy_start_date'].value = None
        card.attrs['predicted_delivery_date'].value = None
        return

    if not delivery_date:
        # если эпикриза нет, но известна дата начала беременности, можно вычислить дату окончания
        # если в осмотрах фигурировала неделя беременности, то она нам интересна, если была больше 40
        weeks = 40 if p_week is None else max(p_week, 40)
        delivery_date = start_date + datetime.timedelta(weeks=weeks)

    if not prev_start_date or start_date != prev_start_date:
        card.attrs['pregnancy_start_date'].value = start_date
    if not prev_delivery_date or epicrisis or abs((delivery_date - prev_delivery_date).days) > 3:
        # Не надо трогать дату родоразрешения, если она не слишком отличается от предыдущей вычисленной при отсутствии
        # эпикриза
        card.attrs['predicted_delivery_date'].value = delivery_date


def reevaluate_pregnacy_pathology(card):
    """
    Пересчёт групп патологий беременности
    :param card: Карточка беременной
    :type card: PregnancyCard
    """

    event_mkb_codes = set()
    diagnostics = card.get_client_diagnostics(card.event.setDate, card.event.execDate)
    for diagnostic in diagnostics:
        event_mkb_codes.add(diagnostic.MKB)

    event_pathologies = set()
    pathologies = pregnancy_pathologies()
    for pathg_code, mkb_list in pathologies.iteritems():
        for mkb in mkb_list:
            if mkb['code'] in event_mkb_codes:
                event_pathologies.add(PregnancyPathology.getId(pathg_code))
    if len(event_pathologies) > 1:
        event_pathologies.add(PregnancyPathology.getId('combined'))
    elif len(event_pathologies) == 0:
        event_pathologies.add(PregnancyPathology.getId('undefined'))

    card.attrs['pregnancy_pathology_list'].value = list(event_pathologies)


def reevaluate_preeclampsia_rate(card):
    """
    Расчет степени преэклампсии у пациентки
    и отображение преэклампсии установленной врачом
    :type card: PregnancyCard
    """

    def preec_diag(diag):
        DiagID = diag._diagnostic.MKB
        if 'O11' in DiagID:
            return 4, 'ChAH'
        if 'O14.1' in DiagID:
            return 3, 'heavy'
        if 'O14.0' in DiagID:
            return 2, 'mild'
        return 1, 'unknown'

    res = 'unknown'
    has_CAH = False
    heavy_diags = False

    event = card.event
    action = card.attrs

    preg_week = get_pregnancy_week(event, action)

    last_inspection = get_action_list(event, checkup_flat_codes).order_by(Action.begDate.desc()).first()
    if preg_week > 20:
        urinary_24 = get_action(event, '24urinary')
        urinary_protein_24 = urinary_24['24protein'].value if urinary_24 else None
        urinary_protein = get_action(event, 'urinaryProtein')['protein'].value if get_action(event, 'urinaryProtein') else None
        biochemical_analysis = get_action(event, 'biochemical_analysis')
        ALaT = biochemical_analysis['ALaT'].value if biochemical_analysis else None
        ASaT = biochemical_analysis['ASaT'].value if biochemical_analysis else None
        albumin_creatinine = get_action(event, 'albuminCreatinineRelation')['albuminCreatinineRelation'].value if \
            get_action(event, 'albuminCreatinineRelation') else None
        thrombocytes = get_action(event, 'clinical_blood_analysis')['thrombocytes'].value if get_action(event, 'clinical_blood_analysis') else None

        for diag in card.get_client_diagnostics(event.setDate, event.execDate):
            DiagID = diag.MKB
            if 'O10' in DiagID:
                has_CAH = True
            if ('R34' in DiagID) or ('J81' in DiagID) or ('R23.0' in DiagID) or ('O36.5' in DiagID):
                heavy_diags = True

        if has_CAH:  # хроническая артериальная гипертензия
            if urinary_protein_24 >= 0.3 or urinary_protein >= 0.3 or albumin_creatinine >= 0.15 or ALaT > 31 or ASaT > 31 or thrombocytes < 100:
                res = 'ChAH'  # преэклампсия на фоне ХАГ
        elif last_inspection:
            all_complaints = last_inspection['complaints'].value
            complaints = filter(lambda x: x['code'] in ('epigastrii', 'zrenie', 'golovnaabol_'), all_complaints) if all_complaints else None
            ad_left_high = last_inspection['ad_left_high'].value
            ad_left_low = last_inspection['ad_left_low'].value
            ad_right_high = last_inspection['ad_right_high'].value
            ad_right_low = last_inspection['ad_right_low'].value
            hight_blood_pressure = (ad_left_high >= 140 or ad_left_low >= 90) or (ad_right_high >= 140 or ad_right_low >= 90)
            very_hight_blood_pressure = (ad_left_high >= 160 or ad_left_low >= 110) or (ad_right_high >= 160 or ad_right_low >= 110)

            if hight_blood_pressure and (urinary_protein_24 >= 0.3 or albumin_creatinine >= 0.15):
                res = 'mild'
                urinary24 = urinary_24['24urinary'].value if urinary_24 else None  # < 500 Олигурия
                if very_hight_blood_pressure or urinary_protein_24 >= 5 or (urinary24 and urinary24 < 500) or ALaT > 31 or \
                   ASaT > 31 or (thrombocytes and thrombocytes < 100) or heavy_diags or complaints:
                    res = 'heavy'

    last_inspection_diags = get_diagnoses_from_action(last_inspection, open=False)

    action['preeclampsia_susp'].value = rbPreEclampsiaRate.query.filter(rbPreEclampsiaRate.code == res).first().__json__()
    confirmed_rate = max(map(preec_diag, last_inspection_diags), key=lambda x: x[0]) if last_inspection_diags else (1, 'unknown')
    action['preeclampsia_comfirmed'].value = rbPreEclampsiaRate.query.filter(rbPreEclampsiaRate.code == confirmed_rate[1]).first().__json__()


def reevaluate_risk_groups(card):
    """
    :type card: PregnancyCard
    :param card:
    :return:
    """
    from blueprints.risar.lib.risk_groups.calc import calc_risk_groups
    existing_groups = card.event.risk_groups
    found_groups = set(calc_risk_groups(card))
    for rg_record in existing_groups:
        code = rg_record.riskGroup_code
        if code not in found_groups:
            rg_record.deleted = 1
        else:
            found_groups.remove(code)
        rg_record.modifyDatetime = datetime.datetime.now()
        rg_record.modifyPerson_id = safe_current_user_id()
    for code in found_groups:
        risk_group = RisarRiskGroup()
        risk_group.event = card.event
        risk_group.riskGroup_code = code
        db.session.add(risk_group)


def check_disease(diagnostics):
    has_disease = {
        'has_HIV': False,
        'has_syphilis': False,
        'has_hepatitis': False,
        'has_tuberculosis': False,
        'has_scabies': False,
        'has_pediculosis': False
    }
    for diag in diagnostics:
        if diag.endDate is not None:
            continue
        diag_id = diag.MKB
        has_disease['has_HIV'] |= diag_id in HIV_diags
        has_disease['has_syphilis'] |= diag_id in syphilis_diags
        has_disease['has_hepatitis'] |= diag_id in hepatitis_diags
        has_disease['has_tuberculosis'] |= diag_id in tuberculosis_diags
        has_disease['has_scabies'] |= diag_id in scabies_diags
        has_disease['has_pediculosis'] |= diag_id in pediculosis_diags
    return has_disease
