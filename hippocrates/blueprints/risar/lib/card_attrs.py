# -*- coding: utf-8 -*-
import datetime
import logging

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.time_converter import DateTimeUtil
from hippocrates.blueprints.risar.lib.utils import get_action, get_action_list, HIV_diags, syphilis_diags, \
    hepatitis_diags, tuberculosis_diags, scabies_diags, pediculosis_diags, pregnancy_pathologies, risk_mkbs, \
    belongs_to_mkbgroup, notify_risk_rate_changes
from hippocrates.blueprints.risar.models.risar import RisarRiskGroup
from hippocrates.blueprints.risar.risar_config import checkup_flat_codes, risar_epicrisis, risar_mother_anamnesis, \
    first_inspection_flat_code, rtc_2_atc
from nemesis.lib.jsonify import EventVisualizer
from nemesis.lib.utils import safe_dict, safe_date
from nemesis.models.actions import Action, ActionType
from nemesis.models.enums import PregnancyPathology, PerinatalRiskRate, CardFillRate
from nemesis.models.event import EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.refbooks import rbFinance
from nemesis.models.risar import rbPreEclampsiaRate
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

logger = logging.getLogger('simple')


__author__ = 'viruzzz-kun'


def default_AT_Heuristic(event_type):
    """
    Получение ActionType, соответствующего атрибутам карточки
    @type event_type: EventType
    @rtype: ActionType | None
    """
    rtc = event_type.requestType.code
    atc = rtc_2_atc[rtc]
    return ActionType.query.filter(ActionType.flatCode == atc).first()


def default_ET_Heuristic(request_type_code):
    """
    Получение EventType, соответствующего ситуации
    @type request_type_code: str | unicode
    @rtype: EventType | None
    """
    return EventType.query.join(
        rbRequestType, rbFinance
    ).filter(
        rbRequestType.code == request_type_code,  # Случай беременности
        rbFinance.code == '2',  # ОМС
        EventType.deleted == 0,
    ).order_by(EventType.createDatetime.desc()).first()


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

    max_rate = max(
        map(diag_to_risk_rate, card.get_client_diagnostics(card.event.setDate, card.event.execDate)) +
        [PerinatalRiskRate.undefined[0]]
    )

    new_prr = PerinatalRiskRate(max_rate)
    notify_risk_rate_changes(card, new_prr)

    card.attrs['prenatal_risk_572'].value = safe_dict(new_prr)


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


def reevaluate_card_fill_rate_all(card):
    """Пересчитать показатель заполненности карты полностью.

    Пересчитать показатели для всех разделов карты, а хатем обновить общий показатель
    заполненности.
    """
    anamnesis_fr = reevaluate_card_fill_rate_anamnesis(card, update_general_rate=False)
    first_inspection_fr = reevaluate_card_fill_rate_first_inspection(card, update_general_rate=False)
    repeated_inspection_fr = reevaluate_card_fill_rate_repeated_inspection(card, update_general_rate=False)
    epicrisis_fr = reevaluate_card_fill_rate_epicrisis(card, update_general_rate=False)

    reevaluate_card_fill_rate(
        card,
        anamnesis_fr=anamnesis_fr, first_inspection_fr=first_inspection_fr,
        repeated_inspection_fr=repeated_inspection_fr, epicrisis_fr=epicrisis_fr
    )


def reevaluate_card_fill_rate(card, **kwargs):
    """Пересчитать общий показатель заполненности карты в зависимости от переданных
    данных о показателях различных разделов карты.

    Разделы включают в себя:
      - анамнез :arg anamnesis_fr
      - первичный осмотр :arg first_inspection_fr
      - повторный осмотр :arg repeated_inspection_fr
      - эпикриз :arg epicrisis_fr
    """
    cfr = CardFillRate.filled[0]

    for section in ('anamnesis_fr', 'first_inspection_fr', 'repeated_inspection_fr', 'epicrisis_fr'):
        if section in kwargs:
            if kwargs[section] == CardFillRate.not_filled[0]:
                cfr = CardFillRate.not_filled[0]
                break

    card.attrs['card_fill_rate'].value = cfr


def reevaluate_card_fill_rate_anamnesis(card, update_general_rate=True):
    """Пересчитать показатель заполненности анамнеза в карте пациентки.

    Пересчитывается всегда, при любом состоянии карты пациентки.
    Анамнез считается заполненным, если просто существует запись анамнеза матери,
    без проверки на наличие данных в самом документе.
    """
    event_date = safe_date(card.event.setDate)
    mother_anamnesis = get_action(card.event, risar_mother_anamnesis)
    anamnesis_fr = (
        CardFillRate.filled[0]
        if mother_anamnesis is not None
        else (
            CardFillRate.waiting[0]
            if DateTimeUtil.get_current_date() <= DateTimeUtil.add_to_date(event_date, 7, DateTimeUtil.day)
            else CardFillRate.not_filled[0]
        )
    )
    card.attrs['card_fill_rate_anamnesis'].value = anamnesis_fr

    if update_general_rate:
        reevaluate_card_fill_rate(card, anamnesis_fr=anamnesis_fr)
    return anamnesis_fr


def reevaluate_card_fill_rate_first_inspection(card, update_general_rate=True):
    """Пересчитать показатель заполненности первичного осмотра в карте пациентки.

    Пересчитывается всегда, при любом состоянии карты пациентки.
    Первичный осмотр считается заполненным, если просто существует запись первичного осмотра,
    без проверки на наличие данных в самом документе.
    """
    event_date = safe_date(card.event.setDate)
    first_inspection = get_action(card.event, first_inspection_flat_code)
    fi_fr = (
        CardFillRate.filled[0]
        if first_inspection is not None
        else (
            CardFillRate.waiting[0]
            if DateTimeUtil.get_current_date() <= DateTimeUtil.add_to_date(event_date, 7, DateTimeUtil.day)
            else CardFillRate.not_filled[0]
        )
    )
    card.attrs['card_fill_rate_first_inspection'].value = fi_fr

    if update_general_rate:
        reevaluate_card_fill_rate(card, first_inspection_fr=fi_fr)
    return fi_fr


def reevaluate_card_fill_rate_repeated_inspection(card, update_general_rate=True):
    """Пересчитать показатель заполненности повторного осмотра в карте пациентки.

    Пересчитывается только при наличии первичного осмотра и отсутствии эпикриза в карте пациентки.
    Повторный осмотр считается заполненным, если просто существует запись повторного осмотра,
    без проверки на наличие данных в самом документе.
    """
    first_inspection = None
    last_inspection = get_action_list(card.event, checkup_flat_codes).order_by(Action.begDate.desc()).first()
    if last_inspection is not None and last_inspection.actionType.flatCode == first_inspection_flat_code:
        first_inspection = last_inspection

    ri_fr = CardFillRate.not_required[0]
    # Заполненность повторного осмотра актуальна только при наличии первого осмотра,
    # плюс наличие эпикриза отменяет необходимость повторного осмотра
    if last_inspection is not None:
        inspection_date = safe_date(last_inspection.begDate)
        valid_by_date = DateTimeUtil.get_current_date() <= DateTimeUtil.add_to_date(inspection_date,
                                                                                    30,
                                                                                    DateTimeUtil.day)
        epicrisis = get_action(card.event, risar_epicrisis)
        valid_epicrisis = epicrisis is not None
        valid_by_epicrisis_date = (
            safe_date(epicrisis.begDate) <= DateTimeUtil.add_to_date(inspection_date,
                                                                     30,
                                                                     DateTimeUtil.day)
        ) if epicrisis is not None else False

        if last_inspection == first_inspection:
            ri_fr = (
                CardFillRate.not_required[0]
                if valid_epicrisis and valid_by_epicrisis_date else (
                    CardFillRate.waiting[0]
                    if valid_by_date else CardFillRate.not_filled[0]
                )
            )
        else:
            ri_fr = (
                CardFillRate.filled[0]
                if valid_epicrisis and valid_by_epicrisis_date else (
                    CardFillRate.waiting[0] if valid_by_date else CardFillRate.not_filled[0]
                )
            )

    card.attrs['card_fill_rate_repeated_inspection'].value = ri_fr

    if update_general_rate:
        reevaluate_card_fill_rate(card, repeated_inspection_fr=ri_fr)
    return ri_fr


def reevaluate_card_fill_rate_epicrisis(card, update_general_rate=True):
    """Пересчитать показатель заполненности эпикриза в карте пациентки.

    Пересчитывается всегда, при любом состоянии карты пациентки.
    Эпикриз считается заполненным, если просто существует запись эпикриза,
    без проверки на наличие данных в самом документе.
    """
    preg_start_date = card.attrs['pregnancy_start_date'].value
    epicrisis = get_action(card.event, risar_epicrisis)
    epicrisis_fr = (
        CardFillRate.filled[0]
        if epicrisis is not None
        else (
            CardFillRate.waiting[0]
            if (not preg_start_date or
                DateTimeUtil.get_current_date() <= DateTimeUtil.add_to_date(preg_start_date,
                                                                            # 47 недель
                                                                            329,
                                                                            DateTimeUtil.day))
            else CardFillRate.not_filled[0]
        )
    )
    old_cfr_epicrisis = card.attrs['card_fill_rate_epicrisis'].value
    card.attrs['card_fill_rate_epicrisis'].value = epicrisis_fr

    if update_general_rate:
        if old_cfr_epicrisis != epicrisis_fr:
            reevaluate_card_fill_rate_repeated_inspection(card, update_general_rate)
        reevaluate_card_fill_rate(card, epicrisis_fr=epicrisis_fr)
    return epicrisis_fr


def reevaluate_risk_groups(card):
    """
    :type card: PregnancyCard
    :param card:
    :return:
    """
    from hippocrates.blueprints.risar.lib.risk_groups.calc import calc_risk_groups
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
        has_disease['has_HIV'] |= belongs_to_mkbgroup(diag_id, HIV_diags)
        has_disease['has_syphilis'] |= belongs_to_mkbgroup(diag_id, syphilis_diags)
        has_disease['has_hepatitis'] |= belongs_to_mkbgroup(diag_id, hepatitis_diags)
        has_disease['has_tuberculosis'] |= belongs_to_mkbgroup(diag_id, tuberculosis_diags)
        has_disease['has_scabies'] |= belongs_to_mkbgroup(diag_id, scabies_diags, with_subnodes=False)
        has_disease['has_pediculosis'] |= belongs_to_mkbgroup(diag_id, pediculosis_diags)
    return has_disease
