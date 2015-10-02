# -*- coding: utf-8 -*-
import itertools
import datetime

from nemesis.lib.data import create_action
from nemesis.lib.jsonify import EventVisualizer
from nemesis.lib.utils import safe_dict
from nemesis.models.actions import Action, ActionType, ActionPropertyType, ActionProperty
from nemesis.models.enums import PregnancyPathology, PreeclampsiaRisk, PerinatalRiskRate
from nemesis.models.risar import rbPreEclampsiaRate, rbPerinatalRiskRate
from nemesis.systemwide import db
from blueprints.risar.lib.utils import get_action, get_action_list, HIV_diags, syphilis_diags, hepatitis_diags, \
    tuberculosis_diags, scabies_diags, pediculosis_diags, multiple_birth, hypertensia, kidney_diseases, collagenoses, \
    vascular_diseases, diabetes, antiphospholipid_syndrome, get_event_diag_mkbs, risk_rates_blockID, risk_rates_diagID, \
    pregnancy_pathologies, risk_mkbs
from blueprints.risar.risar_config import checkup_flat_codes, risar_mother_anamnesis, risar_epicrisis, risar_anamnesis_pregnancy

__author__ = 'viruzzz-kun'


def get_card_attrs_action(event, auto=True):
    """
    Получение Action, соответствующего атрибутам карточки
    :param event: карточка беременной, обращение
    :param auto: создавать ли действие автоматически
    :type event: nemesis.models.event.Event
    :type auto: bool
    :return: действие с атрибутами
    :rtype: Action|NoneType
    """
    action = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode == 'cardAttributes',
    ).first()
    if action is None and auto:
        action = create_action(default_AT_Heuristic().id, event)
        reevaluate_card_attrs(event, action)
        db.session.add(action)
        db.session.commit()
    return action


def get_pregnancy_week(event, action, date=None):
    """
    :type event: application.models.event.Event
    :type date: datetime.date | None
    :param event: Карточка пациентки
    :param date: Интересующая дата или None (тогда - дата окончания беременности)
    :return: число недель от начала беременности на дату
    """
    if action is None:
        action = get_card_attrs_action(event)
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
    return ActionType.query.filter(ActionType.flatCode == 'cardAttributes').first()


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
            if prop.type.typeName == 'Diagnosis' and prop.value:
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


def reevaluate_risk_rate(event, action=None):
    """
    Пересчёт риска невынашивания
    :param event: обращение
    :type event: nemesis.models.event.Event
    """
    if action is None:
        action = get_card_attrs_action(event)

    risk_rate_mkbs = risk_mkbs()

    def diag_to_risk_rate(diag):
        if diag['diagnosis']['mkb'].DiagID in [mkb['code'] for mkb in risk_rate_mkbs['high']]:
            return PerinatalRiskRate.high[0]
        elif diag['diagnosis']['mkb'].DiagID in [mkb['code'] for mkb in risk_rate_mkbs['medium']]:
            return PerinatalRiskRate.medium[0]
        elif diag['diagnosis']['mkb'].DiagID in [mkb['code'] for mkb in risk_rate_mkbs['low']]:
            return PerinatalRiskRate.low[0]
        return PerinatalRiskRate.undefined[0]

    all_diagnoses = list(get_all_diagnoses(event))
    action['prenatal_risk_572'].value = safe_dict(PerinatalRiskRate(max(map(diag_to_risk_rate, all_diagnoses)))) if \
        all_diagnoses else safe_dict(PerinatalRiskRate(PerinatalRiskRate.undefined[0]))


def reevaluate_preeclampsia_risk(event, card_attrs_action=None):
    """
    Пересчёт риска преэклампсии
    :param event: обращение
    :type event: nemesis.models.event.Event
    """
    if card_attrs_action is None:
        card_attrs_action = get_card_attrs_action(event)

    delivery_years = []
    all_diagnoses = []
    diseases = multiple_birth + hypertensia + kidney_diseases + collagenoses + vascular_diseases + diabetes + \
        antiphospholipid_syndrome
    mother_action = get_action(event, risar_mother_anamnesis)
    first_inspection = get_action(event, 'risarFirstInspection')
    second_inspections = get_action_list(event, 'risarSecondInspection', all=True)
    actions_to_check = [mother_action]+[first_inspection]+second_inspections
    for action in actions_to_check:
        all_diagnoses.extend(get_diagnoses_from_action(action, True))

    prev_pregnancies = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0,
                                                            ActionType.flatCode == risar_anamnesis_pregnancy).all()
    if not mother_action and not first_inspection and not prev_pregnancies:
        risk = PreeclampsiaRisk.undefined[0]
    else:
        risk = PreeclampsiaRisk.no_risk[0]

        if not prev_pregnancies or event.client.age_tuple()[-1] >= 35 or (first_inspection and first_inspection['BMI'].value >= 25) or \
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

    if card_attrs_action.propsByCode.get('preeclampsia_risk'):
        card_attrs_action['preeclampsia_risk'].value = risk


def reevaluate_dates(event, action=None):
    """
    Пересчёт даты начала беременности, предполагаемой даты родов, и даты редактирования карты пациентки
    :param event: обращение
    :param action: атрибуты карточки пациентки
    :type event: nemesis.models.event.Event
    :type action: Action
    :rtype: datetime.date
    :return:
    """
    now = datetime.datetime.now()
    action['chart_modify_date'].value = now
    action['chart_modify_time'].value = now

    if action is None:
        action = get_card_attrs_action(event)

    prev_start_date, prev_delivery_date = action['pregnancy_start_date'].value, action['predicted_delivery_date'].value
    start_date, delivery_date, p_week = None, None, None
    epicrisis = get_action(event, risar_epicrisis)

    if epicrisis and epicrisis['pregnancy_duration'].value:
        # Установленная неделя беременности. Может быть как меньше, так и больше 40
        p_week = int(epicrisis['pregnancy_duration'].value)
        # вычисленная дата начала беременности
        start_date = (epicrisis['delivery_date'].value + datetime.timedelta(weeks=-p_week, days=1))
        # Точная дата окончания беременности - дата родоразрешения
        delivery_date = epicrisis['delivery_date'].value

    if not start_date:
        # Сначала смотрим по осмотрам, если таковые есть
        for inspection in get_action_list(event, checkup_flat_codes).order_by(Action.begDate.desc()):
            if inspection['pregnancy_week'].value:
                # Установленная неделя беременности. Может быть как меньше, так и больше 40
                p_week = int(inspection['pregnancy_week'].value)
                # вычисленная дата начала беременности
                start_date = (inspection.begDate.date() + datetime.timedelta(weeks=-p_week, days=1))
                break

    if not start_date:
        mother_action = get_action(event, risar_mother_anamnesis)
        if mother_action:
            # если есть анамнез матери, то находим дату начала беременности из него
            start_date = mother_action['menstruation_last_date'].value

    if not start_date:
        action['pregnancy_start_date'].value = None
        action['predicted_delivery_date'].value = None
        return

    if not delivery_date:
        # если эпикриза нет, но известна дата начала беременности, можно вычислить дату окончания
        # если в осмотрах фигурировала неделя беременности, то она нам интересна, если была больше 40
        weeks = 40 if p_week is None else max(p_week, 40)
        delivery_date = start_date + datetime.timedelta(weeks=weeks)

    if not prev_start_date or abs((start_date - prev_start_date).days) > 3:
        # Не надо трогать дату начала беременности, если она не слишком отличается от предыдущей вычисленной
        action['pregnancy_start_date'].value = start_date
    if not prev_delivery_date or epicrisis or abs((delivery_date - prev_delivery_date).days) > 3:
        # Не надо трогать дату родоразрешения, если она не слишком отличается от предыдущей вычисленной при отсутствии
        # эпикриза
        action['predicted_delivery_date'].value = delivery_date


def reevaluate_pregnacy_pathology(event, action=None):
    """
    Пересчёт групп патологий беременности
    :param event: обращение
    :type event: nemesis.models.event.Event
    """
    if action is None:
        action = get_card_attrs_action(event)

    event_mkb_codes = set()
    for mkb in get_event_diag_mkbs(event, at_flatcodes=checkup_flat_codes):
        event_mkb_codes.add(mkb.DiagID)

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

    action['pregnancy_pathology_list'].value = list(event_pathologies)


def reevaluate_preeclampsia_rate(event, action=None):
    """
    Расчет степени преэклампсии у пациентки
    и отображение преэклампсии установленной врачом
    """

    def preec_diag(diag):
        DiagID = diag['diagnosis']['mkb'].DiagID
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
    if action is None:
        action = get_card_attrs_action(event)
    preg_week = get_pregnancy_week(event, action)

    inspections = get_action_list(event, checkup_flat_codes).all()
    last_inspection = inspections[-1] if inspections else None
    if preg_week > 20:
        mother_anamnesis = get_action(event, risar_mother_anamnesis)

        anamnesis_diags = get_diagnoses_from_action(mother_anamnesis, open=False)
        all_diags = get_all_diagnoses(event)
        urinary_protein_24 = get_action(event, '24urinary')['24protein'].value if get_action(event, '24urinary') else None
        urinary_protein = get_action(event, 'urinaryProtein')['protein'].value if get_action(event, 'urinaryProtein') else None
        biochemical_analysis = get_action(event, 'biochemical_analysis')
        ALaT = biochemical_analysis['ALaT'].value if biochemical_analysis else None
        ASaT = biochemical_analysis['ASaT'].value if biochemical_analysis else None
        albumin_creatinine = get_action(event, 'albuminCreatinineRelation')['albuminCreatinineRelation'].value if \
            get_action(event, 'albuminCreatinineRelation') else None
        thrombocytes = get_action(event, 'clinical_blood_analysis')['thrombocytes'] if get_action(event, 'clinical_blood_analysis') else None

        for diag in anamnesis_diags:
            if 'O10' in diag['diagnosis']['mkb'].DiagID:
                has_CAH = True
                break
        for diag in all_diags:
            DiagID = diag['diagnosis']['mkb'].DiagID
            if ('R34' in DiagID) or ('J81' in DiagID) or ('R23.0' in DiagID) or ('O36.5' in DiagID):
                heavy_diags = True
                break

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
                urinary24 = urinary_protein_24['24urinary'].value  # < 500 Олигурия
                if very_hight_blood_pressure or urinary_protein_24 >= 5 or urinary24 < 500 or ALaT > 31 or \
                   ASaT > 31 or thrombocytes < 100 or heavy_diags or complaints:
                    res = 'heavy'

    last_inspection_diags = get_diagnoses_from_action(last_inspection, open=False)

    action['preeclampsia_susp'].value = rbPreEclampsiaRate.query.filter(rbPreEclampsiaRate.code == res).first().__json__()
    confirmed_rate = max(map(preec_diag, last_inspection_diags), key=lambda x: x[0]) if last_inspection_diags else (1, 'unknown')
    action['preeclampsia_comfirmed'].value = rbPreEclampsiaRate.query.filter(rbPreEclampsiaRate.code == confirmed_rate[1]).first().__json__()


def reevaluate_card_attrs(event, action=None):
    """
    Пересчёт атрибутов карточки беременной
    :param event: карточка беременной, обращение
    :type event: application.models.event.Event
    """
    if action is None:
        action = get_card_attrs_action(event)
    check_card_attrs_action_integrity(action)
    reevaluate_risk_rate(event, action)
    reevaluate_preeclampsia_risk(event, action)
    reevaluate_pregnacy_pathology(event, action)
    reevaluate_dates(event, action)
    reevaluate_preeclampsia_rate(event, action)


def check_disease(diagnoses):
    unclosed_diagnosis = filter(lambda x: not x['end_date'], diagnoses)
    has_disease = {'has_HIV': False,
                   'has_syphilis': False,
                   'has_hepatitis': False,
                   'has_tuberculosis': False,
                   'has_scabies': False,
                   'has_pediculosis': False}
    for diag in unclosed_diagnosis:
        diag_id = diag['diagnosis']['mkb'].DiagID
        if filter(lambda x: x in diag_id, HIV_diags):
            has_disease['has_HIV'] = True
        if filter(lambda x: x in diag_id, syphilis_diags):
            has_disease['has_syphilis'] = True
        if filter(lambda x: x in diag_id, hepatitis_diags):
            has_disease['has_hepatitis'] = True
        if filter(lambda x: x in diag_id, tuberculosis_diags):
            has_disease['has_tuberculosis'] = True
        if filter(lambda x: x in diag_id, scabies_diags):
            has_disease['has_scabies'] = True
        if filter(lambda x: x in diag_id, pediculosis_diags):
            has_disease['has_pediculosis'] = True
    return has_disease