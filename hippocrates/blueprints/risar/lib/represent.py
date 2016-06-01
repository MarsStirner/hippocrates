# -*- coding: utf-8 -*-
import collections
import copy
import datetime
import itertools
from collections import defaultdict

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import get_all_diagnoses, check_disease
from hippocrates.blueprints.risar.lib.card_fill_rate import make_card_fill_timeline
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.utils import get_action, action_apt_values, get_action_type_id, risk_rates_diagID, \
    risk_rates_blockID, get_action_list
from hippocrates.blueprints.risar.lib.utils import week_postfix, get_action_property_value
from hippocrates.blueprints.risar.risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, mother_codes, father_codes, risar_father_anamnesis, risar_mother_anamnesis, \
    checkup_flat_codes, risar_epicrisis, attach_codes
from nemesis.app import app
from nemesis.lib.jsonify import EventVisualizer, DiagnosisVisualizer
from nemesis.lib.utils import safe_traverse_attrs, safe_date
from nemesis.lib.vesta import Vesta
from nemesis.models.actions import Action, ActionType
from nemesis.models.client import BloodHistory
from nemesis.models.diagnosis import Diagnosis, Diagnostic
from nemesis.models.enums import (Gender, AllergyPower, IntoleranceType, PerinatalRiskRate, PreeclampsiaRisk,
                                  PregnancyPathology, ErrandStatus, CardFillRate)
from nemesis.models.exists import rbAttachType, MKB
from nemesis.systemwide import db

__author__ = 'mmalkov'


def represent_prop_value(prop):
    if prop.value is None:
        return [] if prop.type.isVector else None
    else:
        return prop.value


def represent_header(event):
    client = event.client
    return {
        'client': {
            'id': client.id,
            'full_name': client.nameText,
        },
        'event': {
            'id': event.id,
            'set_date': event.setDate,
            'exec_date': event.execDate,
            'person': event.execPerson,
            'external_id': event.externalId,
        }
    }


def represent_event(event):
    """
    :type event: application.models.event.Event
    """
    card = PregnancyCard.get_for_event(event)
    client = event.client
    all_diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)
    card_attrs_action = card.get_card_attrs_action(auto=True)
    em_ctrl = EventMeasureController()
    return {
        'id': event.id,
        'client': {
            'id': client.id,
            'first_name': client.firstName,
            'last_name': client.lastName,
            'patr_name': client.patrName,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode) if client.sexCode is not None else None,
            'snils': client.formatted_SNILS,
            'full_name': client.nameText,
            'notes': client.notes,
            'age_tuple': client.age_tuple(),
            'age': client.age,
            'sex_raw': client.sexCode,
            'cmi_policy': client.policy,
            'attach_lpu': get_lpu_attached(client.attachments),
            'phone': client.contacts.first()
        },
        'set_date': event.setDate,
        'exec_date': event.execDate,
        'person': event.execPerson,
        'external_id': event.externalId,
        'type': event.eventType,
        'em_progress': em_ctrl.calc_event_measure_stats(event),
        'card_attributes': represent_card_attributes(event),
        'anamnesis': represent_anamnesis(event),
        'epicrisis': represent_epicrisis(event),
        'checkups': represent_checkups_shortly(event),
        'risk_rate': card_attrs_action['prenatal_risk_572'].value,
        'preeclampsia_susp_rate': card_attrs_action['preeclampsia_susp'].value if
            card_attrs_action.propsByCode.get('preeclampsia_susp') else None,
        'preeclampsia_confirmed_rate': card_attrs_action['preeclampsia_comfirmed'].value if
            card_attrs_action.propsByCode.get('preeclampsia_comfirmed') else None,
        'pregnancy_pathologies': [
            PregnancyPathology(pathg)
            for pathg in card_attrs_action['pregnancy_pathology_list'].value
        ] if card_attrs_action['pregnancy_pathology_list'].value else [],
        'card_fill_rates': represent_event_cfrs(card_attrs_action),
        'pregnancy_week': get_pregnancy_week(event),
        'diagnoses': represent_event_diagnoses(event),
        'has_diseases': check_disease(all_diagnostics)
    }


def represent_chart_short(event):
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
    second_inspections = get_action_list(event, 'risarSecondInspection', all=True)
    return {
        'id': event.id,
        'set_date': event.setDate,
        'exec_date': event.execDate,
        'pregnancy_start_date': card_attrs_action['pregnancy_start_date'].value,
        'num_of_inspections': len(second_inspections) + 1
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


def represent_mkbs_for_routing(event):
    """
    :type event: nemesis.models.event.Event
    :param event:
    :return:
    """
    card = PregnancyCard.get_for_event(event)
    diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)

    hi_diag_rates = set(risk_rates_diagID['high'])
    hi_block_rates = set(risk_rates_blockID['high'])

    mid_diag_rates = set(risk_rates_diagID['middle'])
    mid_block_rates = set(risk_rates_blockID['middle'])

    low_diag_rates = set(risk_rates_diagID['low'])
    low_block_rates = set(risk_rates_blockID['low'])

    def calc_risk(DiagID, BlockID):
        if DiagID in hi_diag_rates or BlockID in hi_block_rates:
            return PerinatalRiskRate(PerinatalRiskRate.high[0])
        elif DiagID in mid_diag_rates or BlockID in mid_block_rates:
            return PerinatalRiskRate(PerinatalRiskRate.medium[0])
        elif DiagID in low_diag_rates or BlockID in low_block_rates:
            return PerinatalRiskRate(PerinatalRiskRate.low[0])

    result = []
    for diag in diagnostics:
        result.append({
            'id': diag.mkb.id,
            'code': diag.mkb.DiagID,
            'name': diag.mkb.DiagName,
            'risk_rate': calc_risk(diag.mkb.DiagID, diag.mkb.BlockID),
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
    c_district_codes = set([c_kladr_code[:5]]) if c_kladr_code else set()
    c_region_codes = set([code[:2] for code in risar_regions])
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


def get_lpu_attached(attachments):
    return {
        'plan_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 10).first(),
        'extra_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 11).first()
    }


def represent_card_attributes(event):
    action = PregnancyCard.get_for_event(event).attrs
    return {
        'pregnancy_start_date': action['pregnancy_start_date'].value,
        'predicted_delivery_date': action['predicted_delivery_date'].value,
    }


def represent_pregnancies(event):
    prev_pregnancies = [represent_pregnancy(action) for action in event.actions
                        if action.actionType_id == get_action_type_id(risar_anamnesis_pregnancy)]
    return prev_pregnancies


def represent_pregnancy(action):
    pregnancy = dict(action_apt_values(action, pregnancy_apt_codes), id=action.id)
    pregnancy['newborn_inspections'] = represent_newborn_inspections(pregnancy['newborn_inspections']) if \
        pregnancy.get('newborn_inspections') else []
    return pregnancy


def represent_anamnesis(event):
    return {
        'mother': represent_mother_action(event),
        'father': represent_father_action(event),
        'pregnancies': represent_pregnancies(event),
        'transfusions': [
            dict(action_apt_values(action, transfusion_apt_codes), id=action.id)
            for action in event.actions
            if action.actionType_id == get_action_type_id(risar_anamnesis_transfusion)
        ],
        'intolerances': [
            represent_intolerance(obj)
            for obj in itertools.chain(event.client.allergies, event.client.intolerances)
        ]
    }


def represent_mother_action(event, action=None):
    if action is None:
        action = get_action(event, risar_mother_anamnesis)
    if action is None:
        return

    represent_mother = dict((
        (prop.type.code, represent_prop_value(prop))
        for prop in action.properties
        if prop.type.code in mother_codes),

        blood_type=safe_traverse_attrs(
            BloodHistory.query
            .filter(BloodHistory.client_id == event.client_id)
            .order_by(BloodHistory.bloodDate.desc())
            .first(),
            'bloodType', default=None)
    )

    if represent_mother is not None:
        mother_blood_type = BloodHistory.query \
            .filter(BloodHistory.client_id == event.client_id) \
            .order_by(BloodHistory.bloodDate.desc()) \
            .first()
        if mother_blood_type:
            represent_mother['blood_type'] = mother_blood_type.bloodType
    return represent_mother


def represent_father_action(event, action=None):
    if action is None:
        action = get_action(event, risar_father_anamnesis)
    if action is None:
        return
    represent_father = dict(
        (prop.type.code, prop.value)
        for prop in action.properties
        if prop.type.code in father_codes
    )
    return represent_father


def represent_checkups(event):
    query = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)
    ).order_by(Action.begDate)
    return map(represent_checkup, query)


def represent_event_diagnoses(event):
    from nemesis.models.diagnosis import Event_Diagnosis, rbDiagnosisKind

    card = PregnancyCard.get_for_event(event)

    # Сперва достаём диагностики на время действия
    diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)
    # Потом достём id всех действовавших на тот момент диагнозов
    diagnosis_ids = [diagnostic.diagnosis_id for diagnostic in diagnostics]

    # Расставляем ассоциации Diagnosis.id -> Action_Diagnosis
    associations = collections.defaultdict(set)
    for action_diagnosis in Event_Diagnosis.query.filter(
        Event_Diagnosis.deleted == 0,
        Event_Diagnosis.event == event,
        Event_Diagnosis.diagnosis_id.in_(diagnosis_ids),
    ):
        associations[action_diagnosis.diagnosis_id].add(action_diagnosis)

    # Начинаем генерацию
    dvis = DiagnosisVisualizer()
    result = [
        dvis.make_diagnosis_record(diagnostic.diagnosis, diagnostic)
        for diagnostic in diagnostics
    ]
    return result


def represent_action_diagnoses(action):
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind

    card = PregnancyCard.get_for_event(action.event)

    # Сперва достаём диагностики на время действия
    diagnostics = card.get_client_diagnostics(action.begDate, action.endDate)
    # Потом достём id всех действовавших на тот момент диагнозов
    diagnosis_ids = [diagnostic.diagnosis_id for diagnostic in diagnostics]

    # По умолчанию все диагнозы сопутствующие, если не указано иного
    associated_kind = rbDiagnosisKind.cache().by_code().get('associated').first()
    types_info = {
        diag_type.code: associated_kind
        for diag_type in action.actionType.diagnosis_types
    }

    # Расставляем ассоциации Diagnosis.id -> Action_Diagnosis
    associations = collections.defaultdict(set)
    for action_diagnosis in Action_Diagnosis.query.filter(
        Action_Diagnosis.deleted == 0,
        Action_Diagnosis.action == action,
        Action_Diagnosis.diagnosis_id.in_(diagnosis_ids),
    ):
        associations[action_diagnosis.diagnosis_id].add(action_diagnosis)

    # Начинаем генерацию
    dvis = DiagnosisVisualizer()
    result = []
    for diagnostic in diagnostics:
        # Основа типов
        types = copy.copy(types_info)
        # Перегружаем перегруженные (основной/осложнения)
        types.update({
            action_diagnosis.diagnosisType.code: action_diagnosis.diagnosisKind
            for action_diagnosis in associations.get(diagnostic.diagnosis_id, ())
        })
        # Собираем описание диагноза
        result.append(dict(
            dvis.make_diagnosis_record(diagnostic.diagnosis, diagnostic),
            diagnosis_types=types,
        ))
    return result


def represent_checkup(action, with_measures=True):
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
    result['calculated_pregnancy_week'] = get_pregnancy_week(action.event, action.begDate)

    if with_measures:
        em_ctrl = EventMeasureController()
        measures = em_ctrl.get_measures_in_action(action)
        result['measures'] = EventMeasureRepr().represent_listed_event_measures_in_action(measures)
    return result


def represent_checkups_shortly(event):
    query = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)
    ).order_by(Action.begDate)
    return map(represent_checkup_shortly, query)


def represent_checkup_shortly(action):
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisTypeN

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
        rbDiagnosisTypeN,
    ).filter(
        Action_Diagnosis.action == action,
        Action_Diagnosis.diagnosis_id.in_(diagnosis_ids),
        rbDiagnosisTypeN.code == 'main',
    ).first()

    pregnancy_week = get_action_property_value(action.id, 'pregnancy_week')
    result = {
        'id': action.id,
        'beg_date': action.begDate,
        'end_date': action.endDate,
        'person': action.person,
        'pregnancy_week': pregnancy_week.value if pregnancy_week else None,
        'calculated_pregnancy_week': get_pregnancy_week(action.event, action.begDate),
        'diag': represent_diag_shortly(diagnostic) if diagnostic else None
    }
    return result


def represent_diag_shortly(diagnostic):
    return {
        'id': diagnostic.id,
        'mkb': diagnostic.mkb
    }


def represent_ticket(ticket):
    from nemesis.models.actions import Action, ActionType
    from nemesis.models.event import Event
    checkup_n = 0
    event_id = ticket.client_ticket.event_id if ticket.client_ticket else None
    event = Event.query.get(event_id) if event_id else None
    if event_id is not None:
        checkup_n = Action.query\
            .join(ActionType)\
            .filter(
                Action.event_id == event_id,
                Action.deleted == 0,
                ActionType.flatCode.in_(checkup_flat_codes))\
            .count()
    return {
        'schedule_id': ticket.schedule_id,
        'ticket_id': ticket.id,
        'client_ticket_id': ticket.client_ticket.id if ticket.client_ticket else None,
        'client': ticket.client,
        'beg_time': ticket.begDateTime,
        'event_id': ticket.client_ticket.event_id if ticket.client_ticket else None,
        'note': ticket.client_ticket.note if ticket.client else None,
        'checkup_n': checkup_n,
        'risk_rate': PregnancyCard.get_for_event(event).attrs['prenatal_risk_572'].value if event else None,
        'pregnancy_week': get_pregnancy_week(event) if event else None,
    }


def represent_intolerance(obj):
    from nemesis.models.client import ClientAllergy, ClientIntoleranceMedicament
    code = 0 if isinstance(obj, ClientAllergy) else 1 if isinstance(obj, ClientIntoleranceMedicament) else None
    return {
        'type': IntoleranceType(code),
        'id': obj.id,
        'date': obj.createDate,
        'name': obj.name,
        'power': AllergyPower(obj.power),
        'note': obj.notes,
    }


def make_epicrisis_info(epicrisis):
    try:
        info = u'Беременность закончилась '
        pregnancy_final = epicrisis['pregnancy_final']['name'] if epicrisis['pregnancy_final'] else ''
        week = u'недель' if 5 <= epicrisis['pregnancy_duration'] <= 20 else (u'недел' + week_postfix[epicrisis['pregnancy_duration'] % 10])
        is_dead = bool(epicrisis['death_date'] or epicrisis['reason_of_death'])
        is_complications = bool(epicrisis['delivery_waters'] or epicrisis['weakness'] or epicrisis['perineal_tear'] or
                                epicrisis['eclampsia'] or epicrisis['funiculus'] or epicrisis['afterbirth'] or
                                epicrisis['other_complications'])
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
            info += u'<b>' + pregnancy_final + u'</b>'

        if is_complications:
            info += u' <b>с осложнениями</b>'
        info += u' при сроке <b>{0} {1}</b>'.format(epicrisis['pregnancy_duration'], week)

        info += u' - <b>{0} {1}</b>.<br>'.format(epicrisis['delivery_date'].strftime("%d.%m.%Y"), epicrisis['delivery_time'].strftime("%H:%M"))

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
    except:
        info = ''
    return info


def represent_epicrisis(event, action=None):
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
    epicrisis['newborn_inspections'] = represent_newborn_inspections(epicrisis['newborn_inspections']) if \
        epicrisis.get('newborn_inspections') else []
    epicrisis['info'] = make_epicrisis_info(epicrisis)
    epicrisis['diagnoses'] = represent_action_diagnoses(action)
    epicrisis['diagnosis_types'] = action.actionType.diagnosis_types
    return epicrisis


def represent_newborn_inspections(children_info):
    newborn_inspections = []

    for action in children_info:
        inspection = dict((code, prop.value) for (code, prop) in action.propsByCode.iteritems())
        inspection['id'] = action.id
        inspection['sex'] = Gender(inspection['sex']) if inspection['sex'] is not None else None
        newborn_inspections.append(inspection)
    return newborn_inspections


def represent_errand(errand_info):
    today = datetime.date.today()
    planned = errand_info.plannedExecDate.date()
    create_date = errand_info.createDatetime.date()

    days_to_complete = (planned-create_date).days
    progress = (today - create_date).days*100/days_to_complete if (today < planned and days_to_complete) else 100
    card_attrs_action = PregnancyCard.get_for_event(errand_info.event).attrs
    return {
        'id': errand_info.id,
        'create_datetime': errand_info.createDatetime,
        'number': errand_info.number,
        'set_person': errand_info.setPerson,
        'exec_person': errand_info.execPerson,
        'text': errand_info.text,
        'planned_exec_date': errand_info.plannedExecDate,
        'exec_date': errand_info.execDate,
        'event': {'id': errand_info.event.id,
                  'external_id':  errand_info.event.externalId,
                  'client': errand_info.event.client.shortNameText,
                  'risk_rate': card_attrs_action['prenatal_risk_572'].value
                  },
        'result': errand_info.result,
        'reading_date': errand_info.readingDate,
        'status': ErrandStatus(errand_info.status_id),
        'progress': progress
    }


def represent_event_cfrs(card_attrs_action):
    if not card_attrs_action:
        return None
    return {
        'card_fill_rate': CardFillRate(card_attrs_action['card_fill_rate'].value),
        'card_fill_rate_anamnesis': CardFillRate(card_attrs_action['card_fill_rate_anamnesis'].value),
        'card_fill_rate_first_inspection': CardFillRate(card_attrs_action['card_fill_rate_first_inspection'].value),
        'card_fill_rate_repeated_inspection': CardFillRate(card_attrs_action['card_fill_rate_repeated_inspection'].value),
        'card_fill_rate_epicrisis': CardFillRate(card_attrs_action['card_fill_rate_epicrisis'].value),
    }