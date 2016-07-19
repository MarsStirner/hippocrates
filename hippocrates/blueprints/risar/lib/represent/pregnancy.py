# -*- coding: utf-8 -*-
import datetime
from collections import defaultdict

from sqlalchemy import func

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import check_disease
from hippocrates.blueprints.risar.lib.card_fill_rate import make_card_fill_timeline
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.represent.common import represent_prop_value, safe_action_property, \
    represent_event, represent_action_diagnoses, represent_diag_shortly, represent_intolerance, represent_fetus, \
    represent_transfusion, represent_pregnancy
from hippocrates.blueprints.risar.lib.risk_groups.calc import calc_risk_groups
from hippocrates.blueprints.risar.lib.utils import get_action_property_value, get_action, get_action_list, week_postfix
from hippocrates.blueprints.risar.models.risar import RisarEpicrisis_Children
from hippocrates.blueprints.risar.risar_config import mother_codes, father_codes, risar_epicrisis, attach_codes
from nemesis.app import app
from nemesis.lib.utils import safe_traverse_attrs, safe_date
from nemesis.lib.vesta import Vesta
from nemesis.models.actions import Action, ActionType
from nemesis.models.client import BloodHistory
from nemesis.models.diagnosis import Diagnostic
from nemesis.models.enums import PregnancyPathology, CardFillRate, Gender
from nemesis.models.exists import rbAttachType
from nemesis.models.risar import rbPerinatalRiskRate, rbPerinatalRiskRateMkbAssoc

__author__ = 'viruzzz-kun'


def represent_pregnancy_event(event):
    """
    :type event: application.models.event.Event
    """
    card = PregnancyCard.get_for_event(event)
    all_diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)
    card_attrs_action = card.get_card_attrs_action(auto=True)
    em_ctrl = EventMeasureController()
    represent = represent_event(event)
    represent.update({
        'em_progress': em_ctrl.calc_event_measure_stats(event),
        'card_attributes': represent_pregnancy_card_attributes(card_attrs_action),
        'anamnesis': represent_pregnancy_anamnesis(card),
        'epicrisis': represent_pregnancy_epicrisis(event),
        'checkups': map(represent_pregnancy_checkup_shortly, card.checkups),
        'checkups_puerpera': map(represent_pregnancy_checkup_shortly, card.checkups_puerpera),
        'risk_rate': card_attrs_action['prenatal_risk_572'].value,
        'preeclampsia_susp_rate': safe_action_property(card_attrs_action, 'preeclampsia_susp'),
        'preeclampsia_confirmed_rate': safe_action_property(card_attrs_action, 'preeclampsia_comfirmed'),
        'pregnancy_pathologies': [
            PregnancyPathology(pathg)
            for pathg in safe_action_property(card_attrs_action, 'pregnancy_pathology_list')
        ],
        'card_fill_rates': represent_event_cfrs(card_attrs_action),
        'pregnancy_week': get_pregnancy_week(event),
        'has_diseases': check_disease(all_diagnostics)
    })
    return represent


def represent_mkbs_for_routing(event):
    """
    :type event: nemesis.models.event.Event
    :param event:
    :return:
    """
    objects = rbPerinatalRiskRate.query.all()

    mapping_mkb = {
        risk_rate.code: set(mkb.DiagID for mkb in risk_rate.mkbs)
        for risk_rate in objects
    }
    mapping_risk_rates = {
        risk_rate.code: risk_rate for risk_rate in objects
    }
    card = PregnancyCard.get_for_event(event)
    diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)

    mkb_ids = [d.mkb.id for d in diagnostics]
    max_risk_mkb_ids = set(x[0] for x in rbPerinatalRiskRateMkbAssoc.query.filter(
        rbPerinatalRiskRateMkbAssoc.mkb_id.in_(mkb_ids)
    ).values(
        rbPerinatalRiskRateMkbAssoc.mkb_id,
        func.Max(rbPerinatalRiskRate.value),
    ))

    def calc_risk(DiagID):
        for code in ['high', 'medium', 'low']:
            if code in mapping_mkb and DiagID in mapping_mkb[code]:
                return mapping_risk_rates[code]
        return mapping_risk_rates['undefined']

    result = []
    for diag in diagnostics:
        if diag.mkb.id in max_risk_mkb_ids:
            result.append({
                'id': diag.mkb.id,
                'code': diag.mkb.DiagID,
                'name': diag.mkb.DiagName,
                'risk_rate': calc_risk(diag.mkb.DiagID),
            })

    result.sort(key=lambda x: x['code'])
    return result


def represent_org_for_routing(org):
    locality = org.kladr_locality
    if locality:
        region = Vesta.get_kladr_locality(locality.get_region_code())
        district = Vesta.get_kladr_locality(locality.get_district_code())
    else:
        region = district = None
    return {
        'id': org.id,
        'full_name': org.fullName,
        'short_name': org.shortName,
        'title': org.title,
        'address': org.Address,
        'phone': org.phone,
        'kladr_locality': locality,
        'region': region,
        'district': district
    }


def group_orgs_for_routing(orgs, client):
    """Разбить список ЛПУ на группы 1) в районе проживания, 2) в регионе
    проживания пациента.

    Район проживания определяется I и II уровнями кода кладр (5 цифр),
    регион - I уровнем (2 цифры). В любом случае ключевую роль играет
    глобальная настройка регионов, которые обсуживает система РИСАР, так,
    что если у пациента нет адреса или адрес не относится к выбранным регионам,
    то ЛПУ будут отбираться в соответствии с регионами системы и попадать
    во 2-ую группу.

    :param orgs: [nemesis.lib.models.exists.Organisation, ]
    :param client: nemesis.lib.models.client.Client
    :return: dict with orgs grouped by district and region
    """
    risar_regions = app.config.get('RISAR_REGIONS', [])
    district_orgs = defaultdict(dict)
    region_orgs = defaultdict(dict)
    if client.loc_address and client.loc_address.is_from_kladr(False):
        client_la_kladr_code = client.loc_address.KLADRCode
        if any(code.startswith(client_la_kladr_code[:2]) for code in risar_regions):
            c_kladr_code = client_la_kladr_code
        else:
            c_kladr_code = None
    else:
        c_kladr_code = None
    c_district_codes = {c_kladr_code[:5]} if c_kladr_code else set()
    c_region_codes = {code[:2] for code in risar_regions}
    # special cases
    # 1) Ленинградская Область 47 000 000 000 (00) и Санкт-Петербург Город 78 000 000 000 (00)
    # 2) Московская Область 50 000 000 000 (00) и Москва Город 77 000 000 000 (00)
    # 3) Крым Республика 91 000 000 000 (00) и Севастополь Город 92 000 000 000 (00)
    for group in [('47', '78'), ('50', '77'), ('91', '92')]:
        if any(code in c_region_codes for code in group):
            c_region_codes.update(group)
    for org in orgs:
        if org.kladr_locality:
            locality_code = org.kladr_locality.code
            if any(locality_code.startswith(code) for code in c_district_codes):
                if 'kladr_locality' not in district_orgs[locality_code]:
                    district_orgs[locality_code]['kladr_locality'] = org.kladr_locality
                district_orgs[locality_code].setdefault('orgs', []).append(represent_org_for_routing(org))
            elif any(locality_code.startswith(code) for code in c_region_codes):
                if 'kladr_locality' not in region_orgs[locality_code]:
                    region_orgs[locality_code]['kladr_locality'] = org.kladr_locality
                region_orgs[locality_code].setdefault('orgs', []).append(represent_org_for_routing(org))
    return {
        'district_orgs': district_orgs,
        'region_orgs': region_orgs
    }


def represent_pregnancy_card_attributes(action):
    """
    @type action: Action
    @param action:
    @return:
    """
    return {
        'pregnancy_start_date': safe_action_property(action, 'pregnancy_start_date'),
        'predicted_delivery_date': safe_action_property(action, 'predicted_delivery_date'),
    }


def represent_pregnancy_anamnesis(card):
    found_groups = list(calc_risk_groups(card))
    return {
        'mother': represent_mother_action(card.anamnesis.mother),
        'father': represent_father_action(card.anamnesis.father),
        'pregnancies': map(represent_pregnancy, card.prev_pregs),
        'transfusions': map(represent_transfusion, card.transfusions),
        'intolerances': map(represent_intolerance, card.intolerances),
        'risk_groups': found_groups,
    }


def represent_mother_action(action):
    if action is None:
        return
    represent_mother = dict((
        (prop.type.code, represent_prop_value(prop))
        for prop in action.properties
        if prop.type.code in mother_codes),

        blood_type=safe_traverse_attrs(
            BloodHistory.query
            .filter(BloodHistory.client_id == action.event.client_id)
            .order_by(BloodHistory.bloodDate.desc())
            .first(),
            'bloodType', default=None)
    )

    if represent_mother is not None:
        mother_blood_type = BloodHistory.query \
            .filter(BloodHistory.client_id == action.event.client_id) \
            .order_by(BloodHistory.bloodDate.desc()) \
            .first()
        if mother_blood_type:
            represent_mother['blood_type'] = mother_blood_type.bloodType
    return represent_mother


def represent_father_action(action):
    if action is None:
        return
    represent_father = dict(
        (prop.type.code, prop.value)
        for prop in action.properties
        if prop.type.code in father_codes
    )
    return represent_father


def represent_checkup(action, with_measures=True, measures_error=None):
    result = dict(
        (code, prop.value)
        for (code, prop) in action.propsByCode.iteritems()
    )
    result['beg_date'] = action.begDate
    result['end_date'] = action.endDate
    result['person'] = action.person
    result['flat_code'] = action.actionType.flatCode
    result['id'] = action.id

    result['diagnoses'] = represent_action_diagnoses(action)
    result['diagnosis_types'] = action.actionType.diagnosis_types
    result['calculated_pregnancy_week'] = get_pregnancy_week(action.event, date=action.begDate)
    result['fetuses'] = map(represent_fetus, PregnancyCard.Fetus(action).states)

    if with_measures:
        em_ctrl = EventMeasureController()
        measures = em_ctrl.get_measures_in_action(action)
        result['measures'] = EventMeasureRepr().represent_listed_event_measures_in_action(measures)
    if measures_error:
        result['em_error'] = measures_error
    return result


def represent_checkup_puerpera(action, with_measures=True):
    result = dict(
        (code, prop.value)
        for (code, prop) in action.propsByCode.iteritems()
    )
    result['beg_date'] = action.begDate
    result['end_date'] = action.endDate
    result['person'] = action.person
    result['flat_code'] = action.actionType.flatCode
    result['id'] = action.id

    result['diagnoses'] = represent_action_diagnoses(action)
    result['diagnosis_types'] = action.actionType.diagnosis_types

    # if with_measures:
    #     em_ctrl = EventMeasureController()
    #     measures = em_ctrl.get_measures_in_action(action)
    #     result['measures'] = EventMeasureRepr().represent_listed_event_measures_in_action(measures)
    return result


def represent_pregnancy_checkup_shortly(action):
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind

    card = PregnancyCard.get_for_event(action.event)
    # Получим диагностики, актуальные на начало действия (Diagnostic JOIN Diagnosis)
    diagnostics = card.get_client_diagnostics(action.begDate, action.endDate)
    diagnosis_ids = [
        diagnostic.diagnosis_id for diagnostic in diagnostics
    ]
    # Ограничим диагностиками, связанными с действием как "Основной диагноз"
    diagnostic = Diagnostic.query.join(
        Action_Diagnosis, Action_Diagnosis.diagnosis_id == Diagnostic.diagnosis_id
    ).join(
        rbDiagnosisKind,
    ).filter(
        Action_Diagnosis.action == action,
        Action_Diagnosis.diagnosis_id.in_(diagnosis_ids),
        rbDiagnosisKind.code == 'main',
    ).first()

    pregnancy_week = get_action_property_value(action.id, 'pregnancy_week')
    result = {
        'id': action.id,
        'beg_date': action.begDate,
        'end_date': action.endDate,
        'person': action.person,
        'flat_code': action.actionType.flatCode,
        'pregnancy_week': pregnancy_week.value if pregnancy_week else None,
        'calculated_pregnancy_week': get_pregnancy_week(action.event, date=action.begDate),
        'diag': represent_diag_shortly(diagnostic) if diagnostic else None
    }
    return result


def represent_checkup_puerpera_shortly(action):
    from nemesis.models.diagnosis import Action_Diagnosis

    card = PregnancyCard.get_for_event(action.event)
    # Получим диагностики, актуальные на начало действия (Diagnostic JOIN Diagnosis)
    diagnostics = card.get_client_diagnostics(action.begDate, action.endDate)
    diagnosis_ids = [
        diagnostic.diagnosis_id for diagnostic in diagnostics
    ]
    diagnostic = Diagnostic.query.join(
        Action_Diagnosis, Action_Diagnosis.diagnosis_id == Diagnostic.diagnosis_id
    ).filter(
        Action_Diagnosis.action == action,
        Action_Diagnosis.diagnosis_id.in_(diagnosis_ids),
    ).first()

    result = {
        'id': action.id,
        'beg_date': action.begDate,
        'end_date': action.endDate,
        'person': action.person,
        'flat_code': action.actionType.flatCode,
        'diag': represent_diag_shortly(diagnostic) if diagnostic else None
    }
    return result


def represent_pregnancy_epicrisis(event, action=None):
    if action is None:
        action = get_action(event, risar_epicrisis)
    if action is None:
        return
    epicrisis = dict(
        (code, prop.value)
        for (code, prop) in action.propsByCode.iteritems()
    )
    # прибавка массы за всю беременность
    first_inspection = get_action(event, 'risarFirstInspection')
    second_inspection = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0).\
        filter(ActionType.flatCode == 'risarSecondInspection').order_by(Action.begDate.desc()).first()

    first_weight = first_inspection.propsByCode['weight'].value if first_inspection else None
    second_weight = second_inspection.propsByCode['weight'].value if second_inspection else None
    if first_weight and second_weight:
        epicrisis['weight_gain'] = second_weight - first_weight

    finish_date = epicrisis['delivery_date']
    epicrisis['registration_pregnancy_week'] = get_pregnancy_week(event, date=event.setDate.date()) if finish_date else None
    epicrisis['newborn_inspections'] = represent_newborn_inspections(action)
    epicrisis['info'] = make_epicrisis_info(epicrisis)
    epicrisis['diagnoses'] = represent_action_diagnoses(action)
    epicrisis['diagnosis_types'] = action.actionType.diagnosis_types
    return epicrisis


def represent_pregnancy_chart_short(event):
    card_attrs_action = PregnancyCard.get_for_event(event).attrs
    return {
        'id': event.id,
        'set_date': event.setDate,
        'modify_date': datetime.datetime.combine(card_attrs_action['chart_modify_date'].value,
                                                 card_attrs_action['chart_modify_time'].value) if
        card_attrs_action['chart_modify_date'].value and card_attrs_action['chart_modify_time'].value else None,
        'client': event.client,
        'risk_rate': card_attrs_action['prenatal_risk_572'].value if event else None,
        'pregnancy_week': get_pregnancy_week(event) if event else None,
    }


def represent_chart_for_routing(event):
    plan_attach = event.client.attachments.join(rbAttachType).filter(rbAttachType.code == attach_codes['plan_lpu']).first()
    extra_attach = event.client.attachments.join(rbAttachType).filter(rbAttachType.code == attach_codes['extra_lpu']).first()
    return {
        'id': event.id,
        'client': {
            'id': event.client_id,
            'live_address': event.client.loc_address
        },
        'diagnoses': represent_mkbs_for_routing(event),
        'plan_lpu': represent_org_for_routing(plan_attach.org) if plan_attach and plan_attach.org else {},
        'extra_lpu': represent_org_for_routing(extra_attach.org) if extra_attach and extra_attach.org else {},
    }


def represent_chart_for_epicrisis(event):
    card_attrs_action = PregnancyCard.get_for_event(event).attrs
    second_inspections = get_action_list(event, 'risarSecondInspection')
    return {
        'id': event.id,
        'set_date': event.setDate,
        'exec_date': event.execDate,
        'pregnancy_start_date': card_attrs_action['pregnancy_start_date'].value,
        'num_of_inspections': second_inspections.count() + 1
    }


def represent_chart_for_card_fill_rate_history(event):
    card = PregnancyCard.get_for_event(event)
    card_attrs_action = card.attrs
    return {
        'id': event.id,
        'card_fill_rates': {
            'card_fill_rate': CardFillRate(card_attrs_action['card_fill_rate'].value),
            'card_fill_rate_anamnesis': CardFillRate(card_attrs_action['card_fill_rate_anamnesis'].value),
            'card_fill_rate_first_inspection': CardFillRate(card_attrs_action['card_fill_rate_first_inspection'].value),
            'card_fill_rate_repeated_inspection': CardFillRate(card_attrs_action['card_fill_rate_repeated_inspection'].value),
            'card_fill_rate_epicrisis': CardFillRate(card_attrs_action['card_fill_rate_epicrisis'].value),
        },
        'start_date': safe_date(event.setDate),
        'timeline': make_card_fill_timeline(card)
    }


def make_epicrisis_info(epicrisis):
    try:
        ended_pregnancy = u'Беременность закончилась '
        info = week = ''
        pregnancy_final = epicrisis['pregnancy_final']['name'] if epicrisis['pregnancy_final'] else ''
        pregnancy_duration = epicrisis.get('pregnancy_duration')
        if pregnancy_duration:
            if 5 <= pregnancy_duration <= 20:
                week = u'недель'
            else:
                week = u'недел' + week_postfix[pregnancy_duration % 10]

        is_dead = bool(epicrisis['death_date'] or epicrisis['reason_of_death'])
        is_complications = bool(epicrisis['delivery_waters'] or epicrisis['weakness'] or epicrisis['perineal_tear'] or
                                epicrisis['eclampsia'] or epicrisis['funiculus'] or epicrisis['afterbirth'])
        is_manipulations = bool(epicrisis['caul'] or epicrisis['calfbed'] or epicrisis['perineotomy'] or
                                epicrisis['secundines'] or epicrisis['other_manipulations'])
        is_operations = bool(epicrisis['caesarean_section'] or epicrisis['obstetrical_forceps'] or
                             epicrisis['vacuum_extraction'] or epicrisis['embryotomy'])

        if is_dead:
            info += u'смертью матери при '
            if pregnancy_final == u'родами':
                info += u'родах'
            elif pregnancy_final == u'абортом':
                info += u'аборте'
        else:
            if pregnancy_final:
                info += u'<b>' + pregnancy_final + u'</b>'

        if is_complications:
            info += u' <b>с осложнениями</b>'
        if pregnancy_duration:
            info += u' при сроке <b>{0} {1}</b>'.format(pregnancy_duration, week)
        delivery_date = epicrisis.get('delivery_date')
        delivery_time = epicrisis.get('delivery_time')
        if delivery_date and delivery_time:
            info += u' - <b>{0} {1}</b>.<br>'.format(delivery_date.strftime("%d.%m.%Y"), delivery_time.strftime("%H:%M"))

        if pregnancy_final == u'родами':
            info += u"Место родоразрешения: <b>{0}</b>.<br>".format(epicrisis['LPU'].shortName)

        if is_manipulations and is_operations:
            info += u'Были осуществлены <b>пособия и манипуляции</b> и проведены <b>операции</b>.<br>'
        elif is_manipulations:
            info += u'Были осуществлены <b>пособия и манипуляции</b>.<br>'
        elif is_operations:
            info += u'Были проведены <b>операции</b>.<br>'

        if epicrisis['newborn_inspections'] and pregnancy_final != u'абортом':
            info += u'<b>Дети</b> ({}): '.format(len(epicrisis['newborn_inspections']))

            children_info = []
            for child in epicrisis['newborn_inspections']:
                if child['sex'].value == 1:
                    children_info.append(u'<b>мальчик - ' + (u'живой</b>' if child['alive'] else u'мертвый</b>'))
                else:
                    children_info.append(u'<b>девочка - ' + (u'живая</b>' if child['alive'] else u'мертвая</b>'))
            info += ', '.join(children_info) + '.'
        if info.strip():
            info = ended_pregnancy + info
        else:
            info = u"Эпикриз ещё не создан"
    except Exception as exc:
        info = u'Произошла ошибка. Свяжитесь с администратором системы'
    return info


def represent_event_cfrs(action):
    if not action:
        return None
    return {
        'card_fill_rate': CardFillRate(action['card_fill_rate'].value),
        'card_fill_rate_anamnesis': CardFillRate(action['card_fill_rate_anamnesis'].value),
        'card_fill_rate_first_inspection': CardFillRate(action['card_fill_rate_first_inspection'].value),
        'card_fill_rate_repeated_inspection': CardFillRate(action['card_fill_rate_repeated_inspection'].value),
        'card_fill_rate_epicrisis': CardFillRate(action['card_fill_rate_epicrisis'].value),
    }


def represent_fetuses(card):
    """
    @type card: PregnancyCard
    @param card:
    @return:
    """
    actions = card.checkups
    if actions:
        action = actions[-1]
        result = dict(
            (code, prop.value)
            for (code, prop) in action.propsByCode.iteritems()
        )
        result['beg_date'] = action.begDate
        result['end_date'] = action.endDate
        result['person'] = action.person
        result['flat_code'] = action.actionType.flatCode
        result['id'] = action.id

        fetus = PregnancyCard.Fetus(action)
        result['fetuses'] = map(represent_fetus, fetus.states)

        return result
    else:
        return {}


def represent_newborn_inspections(action):
    """
    @type action: nemesis.models.actions.Action
    @param action:
    @return:
    """
    return [
        {
            'id': newborn.id,
            'date': newborn.date,
            'time': newborn.time,
            'sex': Gender(newborn.sex) if newborn.sex is not None else None,
            'weight': newborn.weight,
            'length': newborn.length,
            'maturity_rate': newborn.maturity_rate,
            'apgar_score_1': newborn.apgar_score_1,
            'apgar_score_5': newborn.apgar_score_5,
            'apgar_score_10': newborn.apgar_score_10,
            'alive': newborn.alive,
            'death_reasons': newborn.death_reasons,
            'diseases': newborn.diseases,
        }
        for newborn in RisarEpicrisis_Children.query.filter(
            RisarEpicrisis_Children.action == action,
        ).order_by(RisarEpicrisis_Children.id)
    ]