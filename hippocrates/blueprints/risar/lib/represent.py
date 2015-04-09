# -*- coding: utf-8 -*-
import datetime
import itertools

from nemesis.lib.utils import safe_traverse_attrs, safe_traverse
from nemesis.lib.jsonify import EventVisualizer
from nemesis.models.actions import Action, ActionType
from nemesis.models.client import BloodHistory
from nemesis.models.enums import Gender, AllergyPower, IntoleranceType, PrenatalRiskRate
from nemesis.models.exists import rbAttachType
from blueprints.risar.lib.card_attrs import get_card_attrs_action, get_all_diagnoses, check_disease
from blueprints.risar.lib.utils import get_action, action_apt_values, get_action_type_id
from ..risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, mother_codes, father_codes, risar_father_anamnesis, risar_mother_anamnesis, \
    checkup_flat_codes, risar_epicrisis, risar_newborn_inspection
from ..lib.utils import week_postfix


__author__ = 'mmalkov'


def represent_prop_value(prop):
    if prop.value is None:
        return [] if prop.type.isVector else None
    else:
        return prop.value


def represent_event(event):
    """
    :type event: application.models.event.Event
    """
    client = event.client
    all_diagnoses = list(get_all_diagnoses(event))

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
        'risk_rate': PrenatalRiskRate(get_card_attrs_action(event, auto=True)['prenatal_risk_572'].value),
        'pregnancy_week': get_pregnancy_week(event),
        'diagnoses': all_diagnoses,
        'has_diseases': check_disease(all_diagnoses)
    }


def represent_chart_for_routing(event):
    mkbs = [
        diagnose.mkb
        for diagnose in itertools.chain.from_iterable(
            diagnostic.diagnoses
            for diagnostic in itertools.chain.from_iterable(
                prop.value if isinstance(prop.value, list) else [prop.value]
                for prop in itertools.chain.from_iterable(
                    action.properties
                    for action in event.actions
                )
                if prop.type.typeName == 'Diagnosis' and prop.value
            )
            if not diagnostic.endDate
        )
    ]
    mkbs.sort(key=lambda x: x.DiagID)
    plan_attach = event.client.attachments.join(rbAttachType).filter(rbAttachType.code == 10).first()
    extra_attach = event.client.attachments.join(rbAttachType).filter(rbAttachType.code == 11).first()
    return {
        'id': event.id,
        'client_id': event.client_id,
        'diagnoses': mkbs,
        'plan_lpu': plan_attach.org if plan_attach else {},
        'extra_lpu': extra_attach.org if extra_attach else {},
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
    ).order_by(Action.begDate.desc())
    return map(represent_checkup, query)


def represent_checkup(action):
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
