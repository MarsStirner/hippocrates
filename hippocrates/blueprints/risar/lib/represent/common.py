# -*- coding: utf-8 -*-
import collections
import copy

from hippocrates.blueprints.risar.lib.card import PregnancyCard, AbstractCard
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.em_repr import EventMeasureRepr
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.prev_children import get_previous_children
from hippocrates.blueprints.risar.lib.utils import action_as_dict
from hippocrates.blueprints.risar.risar_config import checkup_flat_codes, transfusion_apt_codes, pregnancy_apt_codes
from nemesis.app import app
from nemesis.lib.jsonify import DiagnosisVisualizer
from nemesis.lib.utils import safe_int, safe_bool
from nemesis.models.diagnosis import Diagnostic
from nemesis.models.enums import Gender, IntoleranceType, AllergyPower
from nemesis.models.event import Event
from nemesis.models.exists import rbAttachType
from nemesis.models.schedule import ScheduleTicket

__author__ = 'viruzzz-kun'


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
            'manager': event.manager,
            'external_id': event.externalId,
        }
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


def represent_action_diagnoses(action):
    from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind

    card = AbstractCard.get_for_event(action.event)

    # Сперва достаём диагностики на время действия
    diagnostics = card.get_client_diagnostics(action.begDate, action.endDate)
    # Потом достём id всех действовавших на тот момент диагнозов
    diagnosis_ids = [diagnostic.diagnosis_id for diagnostic in diagnostics]

    # По умолчанию все диагнозы сопутствующие, если не указано иного
    associated_kind = rbDiagnosisKind.query.filter(rbDiagnosisKind.code == 'associated').first()
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


def represent_diag_shortly(diagnostic):
    return {
        'id': diagnostic.id,
        'mkb': diagnostic.mkb
    }


def represent_ticket(ticket_event_ids):
    from nemesis.models.actions import Action, ActionType
    event = Event.query.filter(Event.id == ticket_event_ids[1]).first()
    ticket = ScheduleTicket.query.get(ticket_event_ids[0])
    checkup_n = 0
    if event:
        checkup_n = Action.query\
            .join(ActionType)\
            .filter(
                Action.event_id == event.id,
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
            'heartbeat': fetus.heartbeat,
            'delay': fetus.delay,
            'basal': fetus.basal,
            'variability_range': fetus.variability_range,
            'frequency_per_minute': fetus.frequency_per_minute,
            'acceleration': fetus.acceleration,
            'deceleration': fetus.deceleration,
            'heart_rate': fetus.heart_rate,
            'ktg_input': fetus.ktg_input,
        },
    }


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
        id=pregnancy.action.id
    )


def represent_anamnesis_newborn_inspection(child):
    return {
        'id': child.id,
        'weight': child.weight,
        'alive': safe_bool(child.alive),
        'death_reason': child.death_reason,
        'died_at': child.died_at,
        'abnormal_development': safe_bool(child.abnormal_development),
        'neurological_disorders': safe_bool(child.neurological_disorders),
    }


def represent_checkup(action, codes=None):
    result = action_as_dict(action, codes)
    result['beg_date'] = action.begDate
    result['end_date'] = action.endDate
    result['person'] = action.person
    result['flat_code'] = action.actionType.flatCode
    result['id'] = action.id

    result['diagnoses'] = represent_action_diagnoses(action)
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


def represent_measures(action):
    return EventMeasureRepr().represent_listed_event_measures_in_action(
        EventMeasureController().get_measures_in_action(action)
    )