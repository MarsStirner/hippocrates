# -*- coding: utf-8 -*-
import collections
import copy

from hippocrates.blueprints.risar.lib.card import PregnancyCard, AbstractCard
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.prev_children import get_previous_children
from hippocrates.blueprints.risar.lib.chart import check_event_controlled
from hippocrates.blueprints.risar.lib.checkups import can_read_checkup, can_edit_checkup, can_copy_checkup
from hippocrates.blueprints.risar.lib.utils import action_as_dict, get_external_id
from hippocrates.blueprints.risar.lib.anamnesis import get_delivery_date_based_on_epicrisis
from hippocrates.blueprints.risar.risar_config import checkup_flat_codes, transfusion_apt_codes, pregnancy_apt_codes, \
    risar_gyn_checkup_flat_codes
from nemesis.app import app
from nemesis.lib.jsonify import DiagnosisVisualizer
from nemesis.lib.utils import safe_int, safe_bool, safe_date, format_date
from nemesis.models.diagnosis import Diagnostic
from nemesis.models.enums import Gender, IntoleranceType, AllergyPower, KtgInput
from nemesis.models.exists import rbAttachType

__author__ = 'viruzzz-kun'


def represent_header(event):
    card = AbstractCard.get_for_event(event)
    client = event.client
    card_req_code = event.eventType.requestType.code
    return {
        'client': {
            'id': client.id,
            'full_name': client.nameText,
            'birth_date': client.birthDate
        },
        'event': {
            'id': event.id,
            'set_date': event.setDate,
            'exec_date': event.execDate,
            'person': event.execPerson,
            'manager': event.manager,
            'external_id': event.externalId,
            'is_controlled': check_event_controlled(event)
        },
        'request_type': card_req_code,
        'latest_gyn_event_id': card.latest_gyn_event.id if card.latest_gyn_event else None,
        'latest_pregnancy_event_id': card.latest_pregnancy_event.id if card.latest_pregnancy_event else None

    }


def represent_event_client(client):
    return {
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
    }


def represent_event(event):
    return {
        'id': event.id,
        'client': represent_event_client(event.client),
        'set_date': event.setDate,
        'exec_date': event.execDate,
        'person': event.execPerson,
        'external_id': event.externalId,
        'type': event.eventType,
        'diagnoses': represent_event_diagnoses(event),
    }


def get_lpu_attached(attachments):
    return {
        'plan_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 10).first(),
        'extra_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 11).first()
    }


def represent_event_diagnoses(event):
    from nemesis.models.diagnosis import Event_Diagnosis

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


def represent_action_diagnoses(action, flat_codes=None):
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind
    from hippocrates.blueprints.risar.lib.diagnosis import get_prev_inspection_query

    card = AbstractCard.get_for_event(action.event)

    # Сперва достаём диагностики на время действия
    diagnostics = card.get_client_diagnostics(action.begDate, action.endDate)
    # Потом достём id всех действовавших на тот момент диагнозов
    diagnosis_ids = [diagnostic.diagnosis_id for diagnostic in diagnostics]

    this_is_new_action = action.id is None
    if this_is_new_action:
        query_action = get_prev_inspection_query(action, flat_codes).first()
    else:
        query_action = action

    query = Action_Diagnosis.query.filter(
        Action_Diagnosis.deleted == 0,
        Action_Diagnosis.action == query_action,
        Action_Diagnosis.diagnosis_id.in_(diagnosis_ids),
    )

    # Расставляем ассоциации Diagnosis.id -> Action_Diagnosis
    associations = collections.defaultdict(set)
    for action_diagnosis in query:
        if this_is_new_action:
            blank_ad = Action_Diagnosis(
                diagnosis_id=action_diagnosis.diagnosis_id,
                diagnosisType_id=action_diagnosis.diagnosisType_id,
                diagnosisKind_id=action_diagnosis.diagnosisKind_id,
                diagnosis=action_diagnosis.diagnosis,
                diagnosisType=action_diagnosis.diagnosisType,
                diagnosisKind=action_diagnosis.diagnosisKind
            )

            associations[action_diagnosis.diagnosis_id].add(blank_ad)
        else:
            associations[action_diagnosis.diagnosis_id].add(action_diagnosis)

    # Начинаем генерацию
    dvis = DiagnosisVisualizer()
    result = []

    # По умолчанию все диагнозы сопутствующие, если не указано иного
    associated_kind = rbDiagnosisKind.query.filter(rbDiagnosisKind.code == 'associated').first()
    types_info = {
        diag_type.code: associated_kind
        for diag_type in action.actionType.diagnosis_types
    }
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
            kind_changed=this_is_new_action,
            diagnostic_changed=this_is_new_action,
        ))
    return result


def represent_diag_shortly(diagnostic):
    return {
        'id': diagnostic.id,
        'mkb': diagnostic.mkb
    }


def _get_ckeckup_count(event, flat_codes):
    from nemesis.models.actions import Action, ActionType

    if event:
        return Action.query.join(
            ActionType
        ).filter(
            Action.event == event,
            Action.deleted == 0,
            ActionType.flatCode.in_(flat_codes)
        ).count()

    return 0


def represent_pregnancy_ticket(ticket, event):
    return {
        'ticket_type': 'pregnancy',
        'schedule_id': ticket.schedule_id,
        'ticket_id': ticket.id,
        'client_ticket_id': ticket.client_ticket.id if ticket.client_ticket else None,
        'client': ticket.client,
        'beg_time': ticket.begDateTime,
        'event_id': event.id,
        'note': ticket.client_ticket.note if ticket.client else None,
        'checkup_n': _get_ckeckup_count(event, checkup_flat_codes),
        'risk_rate': PregnancyCard.get_for_event(event).attrs['prenatal_risk_572'].value if event else None,
        'pregnancy_week': get_pregnancy_week(event) if event else None,
    }


def represent_gynecological_ticket(ticket, event):
    return {
        'ticket_type': 'gynecological',
        'schedule_id': ticket.schedule_id,
        'ticket_id': ticket.id,
        'client_ticket_id': ticket.client_ticket.id if ticket.client_ticket else None,
        'client': ticket.client,
        'beg_time': ticket.begDateTime,
        'event_id': event.id,
        'note': ticket.client_ticket.note if ticket.client else None,
        'checkup_n': _get_ckeckup_count(event, risar_gyn_checkup_flat_codes),
    }


def represent_empty_ticket(ticket):
    return {
        'ticket_type': 'empty',
        'schedule_id': ticket.schedule_id,
        'ticket_id': ticket.id,
        'client_ticket_id': ticket.client_ticket.id if ticket.client_ticket else None,
        'client': ticket.client,
        'beg_time': ticket.begDateTime,
        'event_id': None,
        'note': ticket.client_ticket.note if ticket.client else None,
        'checkup_n': 0,
    }


def represent_ticket(ticket_event_tuple):
    ticket, event = ticket_event_tuple
    if event:
        if event.eventType.requestType.code == 'pregnancy':
            return represent_pregnancy_ticket(ticket, event)
        elif event.eventType.requestType.code == 'gynecological':
            return represent_gynecological_ticket(ticket, event)
    return represent_empty_ticket(ticket)


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


def represent_file_meta(fmeta):
    return {
        'id': fmeta.id,
        'name': fmeta.name,
        'mimetype': fmeta.mimetype,
        'note': fmeta.note,
        'url': make_file_url(fmeta)
    }


def make_file_url(fmeta):
    devourer_url = app.config['DEVOURER_URL'].rstrip('/') + '/'
    if fmeta.uuid:
        return u'{0}{1}'.format(
            devourer_url,
            u'api/0/download/{0}'.format(fmeta.uuid.hex)
        )

def represent_fetus(fetus):
    return {
        'state': {
            'id': fetus.id,
            'position': fetus.position,
            'position_2': fetus.position_2,
            'type': fetus.type,
            'presenting_part': fetus.presenting_part,
            'contigous_part': fetus.contigous_part,
            'heartbeat': fetus.heartbeat,
            'delay': fetus.delay,
            'basal': fetus.basal,
            'variability_range': fetus.variability_range,
            'frequency_per_minute': fetus.frequency_per_minute,
            'acceleration': fetus.acceleration,
            'deceleration': fetus.deceleration,
            'heart_rate': fetus.heart_rate,
            'ktg_input': KtgInput(fetus.ktg_input).code,
            'stv_evaluation': fetus.stv_evaluation,
            'fisher_ktg_points': fetus.fisher_ktg_points,
            'fisher_ktg_rate': fetus.fisher_ktg_rate
        },
    }


def represent_fetus_for_checkup_copy(fetus):
    dc = represent_fetus(fetus)
    dc['state']['id'] = None
    return dc


def represent_age(age):
    age = safe_int(age)
    if age:
        template = ''
        if 11 <= age <= 14:
            template = u"(%s л.)"
        elif age < 110 and int(str(age)[-1]) in (1, 2, 3, 4):
            template = u"(%s г.)"
        else:
            template = u"(%s л.)"
        return template % age
    return ''


def represent_chart_for_close_event(event):
    return {
        'id': event.id,
        'exec_date': event.execDate,
        'manager': event.manager,
    }


def represent_transfusion(action):
    return dict(
        action_as_dict(action, transfusion_apt_codes),
        id=action.id
    )








def represent_pregnancy(pregnancy):
    return dict(
        action_as_dict(pregnancy.action, pregnancy_apt_codes),
        newborn_inspections=map(
            represent_anamnesis_newborn_inspection,
            get_previous_children(pregnancy.action)
        ),
        id=pregnancy.action.id,
        event_id=pregnancy.action.get_prop_value('card_number'),
        external_id=get_external_id(
            pregnancy.action.get_prop_value('card_number')
        ) if pregnancy.action.has_property('card_number') else None,
        epic_delivery_date=format_date(
            safe_date(get_delivery_date_based_on_epicrisis(pregnancy))
        ) if pregnancy.action.has_property('card_number') else None
    )

def represent_anamnesis_newborn_inspection(child):
    return {
        'id': child.id,
        'weight': child.weight,
        'alive': safe_bool(child.alive),
        'sex': Gender(child.sex) if child.sex is not None else None,
        'death_reason': child.death_reason,
        'died_at': child.died_at,
        'abnormal_development': safe_bool(child.abnormal_development),
        'neurological_disorders': safe_bool(child.neurological_disorders),
    }


def represent_checkup(action, che_p_flat_codes=None, codes=None):
    if che_p_flat_codes is None:
        che_p_flat_codes = []
    result = action_as_dict(action, codes)
    result['beg_date'] = action.begDate
    result['end_date'] = action.endDate
    result['person'] = action.person
    result['flat_code'] = action.actionType.flatCode
    result['id'] = action.id

    result['diagnoses'] = represent_action_diagnoses(action, che_p_flat_codes)
    result['diagnosis_types'] = action.actionType.diagnosis_types
    return result


def represent_checkup_shortly(action):
    """
    This is a base for any checkups
    @type action: Action
    @param action:
    @return:
    """
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind

    card = AbstractCard.get_for_event(action.event)
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
    ).order_by(Diagnostic.setDate.desc(), Diagnostic.id.desc()).first()
    result = {
        'id': action.id,
        'beg_date': action.begDate,
        'end_date': action.endDate,
        'person': action.person,
        'flat_code': action.actionType.flatCode,
        'diag': represent_diag_shortly(diagnostic) if diagnostic else None
    }
    return result


def represent_checkup_access(action):
    return {
        'can_read': can_read_checkup(action),
        'can_edit': can_edit_checkup(action),
        'can_copy': can_copy_checkup(action),
    }


def represent_measures(action):
    return EventMeasureRepr().represent_listed_event_measures_in_action(
        EventMeasureController().get_measures_in_action(action, {
            'with_deleted_hand_measures': True
        })
    )


def represent_ticket_25(action):
    if not action:
        return {
            'id': None,
            'beg_date': None,
            'end_date': None,
            'medical_care': {},
            'visit_place': {},
            'visit_reason': {},
            'visit_type': {},
            'finished_treatment': {},
            'initial_treatment': {},
            'treatment_result': {},
            'payment': {},
            'ache_result': {},
            'services': [],
            'operations': [],
            'manipulations': [],
            'temp_disability': [],
        }
    return dict(
        action_as_dict(action),
        id=action.id,
        beg_date=action.begDate,
        end_date=action.endDate,
    )
