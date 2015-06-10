# -*- coding: utf-8 -*-

import datetime
import itertools

from collections import defaultdict

from nemesis.app import app
from nemesis.systemwide import db
from nemesis.lib.utils import safe_traverse_attrs, safe_traverse, safe_dict
from nemesis.lib.jsonify import EventVisualizer
from nemesis.lib.vesta import Vesta
from nemesis.models.actions import Action, ActionType
from nemesis.models.client import BloodHistory
from nemesis.models.enums import Gender, AllergyPower, IntoleranceType, PrenatalRiskRate, PreeclampsiaRisk
from nemesis.models.event import Diagnosis, Diagnostic
from nemesis.models.exists import rbAttachType, MKB
from blueprints.risar.lib.card_attrs import get_card_attrs_action, get_all_diagnoses, check_disease
from blueprints.risar.lib.utils import get_action, action_apt_values, get_action_type_id, risk_rates_diagID, \
    risk_rates_blockID
from blueprints.risar.lib.expert.protocols import measure_manager_factory
from ..risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, mother_codes, father_codes, risar_father_anamnesis, risar_mother_anamnesis, \
    checkup_flat_codes, risar_epicrisis, risar_newborn_inspection, attach_codes
from ..lib.utils import week_postfix


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
    client = event.client
    all_diagnoses = list(get_all_diagnoses(event))
    card_attrs_action = get_card_attrs_action(event, auto=True)

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
        'progress': {
            'lab': {
                'complete': 5,
                'total': 14,
                'percent': 500 / 14,
            },
            'func': {
                'complete': 3,
                'total': 10,
                'percent': 300 / 10,
            },
            'checkups': {
                'complete': 9,
                'total': 10,
                'percent': 900 / 10,
            }
        },
        'card_attributes': represent_card_attributes(event),
        'anamnesis': represent_anamnesis(event),
        'epicrisis': represent_epicrisis(event),
        'checkups': represent_checkups(event),
        'risk_rate': PrenatalRiskRate(card_attrs_action['prenatal_risk_572'].value),
        'preeclampsia_risk': PreeclampsiaRisk(card_attrs_action['preeclampsia_risk'].value) if
        card_attrs_action.propsByCode.get('preeclampsia_risk') else None,
        'pregnancy_week': get_pregnancy_week(event),
        'diagnoses': all_diagnoses,
        'has_diseases': check_disease(all_diagnoses)
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


def represent_mkbs_for_routing(event):
    mkbs = db.session.query(MKB).select_from(
        Diagnostic
    ).join(Diagnostic.diagnoses).join(Diagnosis.mkb).filter(
        Diagnostic.event_id == event.id,
        Diagnostic.endDate == None,
        Diagnostic.deleted == 0
    ).all()
    mkbs = list(set(mkbs))

    def set_risk(mkb):
        if mkb.DiagID in risk_rates_diagID['high'] or mkb.BlockID in risk_rates_blockID['high']:
            rr = PrenatalRiskRate(PrenatalRiskRate.high[0])
        elif mkb.DiagID in risk_rates_diagID['middle'] or mkb.BlockID in risk_rates_blockID['middle']:
            rr = PrenatalRiskRate(PrenatalRiskRate.medium[0])
        elif mkb.DiagID in risk_rates_diagID['low'] or mkb.BlockID in risk_rates_blockID['low']:
            rr = PrenatalRiskRate(PrenatalRiskRate.low[0])
        else:
            rr = None
        mkb.risk_rate = rr
        return mkb
    mkbs = map(set_risk, mkbs)
    mkbs = sorted(mkbs, key=lambda x: x.DiagID)
    return [{
        'id': mkb.id,
        'code': mkb.DiagID,
        'name': mkb.DiagName,
        'risk_rate': mkb.risk_rate
    } for mkb in mkbs]


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


def get_pregnancy_week(event, date=None):
    """
    :type event: application.models.event.Event
    :type date: datetime.date | None
    :param event: Карточка пациентки
    :param date: Интересующая дата или None (тогда - дата окончания беременности)
    :return: число недель от начала беременности на дату
    """
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


def represent_card_attributes(event):
    action = get_card_attrs_action(event)
    return {
        'pregnancy_start_date': action['pregnancy_start_date'].value,
        'predicted_delivery_date': action['predicted_delivery_date'].value
    }


def represent_anamnesis(event):
    return {
        'mother': represent_mother_action(event),
        'father': represent_father_action(event),
        'pregnancies': [
            dict(action_apt_values(action, pregnancy_apt_codes), id=action.id)
            for action in event.actions
            if action.actionType_id == get_action_type_id(risar_anamnesis_pregnancy)
        ],
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
        evis = EventVisualizer()
        mother_blood_type = BloodHistory.query \
            .filter(BloodHistory.client_id == event.client_id) \
            .order_by(BloodHistory.bloodDate.desc()) \
            .first()
        if mother_blood_type:
            represent_mother['blood_type'] = mother_blood_type.bloodType
        represent_mother['finished_diseases'] = [evis.make_diagnostic_record(diag) for diag in
                                                 represent_mother['finished_diseases']] if represent_mother['finished_diseases'] else []
        represent_mother['current_diseases'] = [evis.make_diagnostic_record(diag) for diag in
                                                represent_mother['current_diseases']] if represent_mother['current_diseases'] else []
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

    if represent_father is not None:
        evis = EventVisualizer()
        represent_father['finished_diseases'] = [evis.make_diagnostic_record(diag) for diag in
                                                 represent_father['finished_diseases']] if represent_father['finished_diseases'] else []
        represent_father['current_diseases'] = [evis.make_diagnostic_record(diag) for diag in
                                                represent_father['current_diseases']] if represent_father['current_diseases'] else []
    return represent_father


def represent_checkups(event):
    query = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)
    ).order_by(Action.begDate)
    return map(represent_checkup, query)


def represent_checkup(action, with_measures=True):
    evis = EventVisualizer()
    result = dict(
        (code, prop.value)
        for (code, prop) in action.propsByCode.iteritems()
    )
    result['beg_date'] = action.begDate
    result['person'] = action.person
    result['flatCode'] = action.actionType.flatCode
    result['id'] = action.id
    if result:
        result['diag'] = evis.make_diagnostic_record(result['diag'])
        for code in ('diag2', 'diag3'):
            result[code] = [evis.make_diagnostic_record(diag) for diag in result[code]] if result[code] else []
    result['calculated_pregnancy_week'] = get_pregnancy_week(action.event, action.begDate)

    if with_measures:
        measure_mng = measure_manager_factory('represent', action) if action.id else None
        result['measures'] = measure_mng.represent_measures() if measure_mng else []
    return result


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
        'risk_rate': PrenatalRiskRate(get_card_attrs_action(event)['prenatal_risk_572'].value) if event else None,
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
    finish_date = epicrisis['delivery_date']
    epicrisis['registration_pregnancy_week'] = get_pregnancy_week(event, event.setDate.date()) if finish_date else None
    epicrisis['newborn_inspections'] = represent_newborn_inspections(event)
    epicrisis['info'] = make_epicrisis_info(epicrisis)
    if epicrisis:
        evis = EventVisualizer()
        epicrisis['main_diagnosis'] = evis.make_diagnostic_record(epicrisis['main_diagnosis'])
        epicrisis['pat_diagnosis'] = evis.make_diagnostic_record(epicrisis['pat_diagnosis'])
        for code in ('attend_diagnosis', 'complicating_diagnosis', 'operation_complication'):
            epicrisis[code] = [evis.make_diagnostic_record(diag) for diag in epicrisis[code]] if epicrisis[code] else []
    return epicrisis


def represent_newborn_inspections(event):
    newborn_inspections = []
    actions = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0,
                                                   ActionType.flatCode == risar_newborn_inspection).all()

    for action in actions:
        inspection = dict((code, prop.value) for (code, prop) in action.propsByCode.iteritems())
        inspection['id'] = action.id
        inspection['sex'] = Gender(inspection['sex']) if inspection['sex'] is not None else None
        newborn_inspections.append(inspection)
    return newborn_inspections
