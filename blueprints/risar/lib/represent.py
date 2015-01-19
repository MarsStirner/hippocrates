# -*- coding: utf-8 -*-
import datetime
import itertools
from application.lib.data import create_action

from application.lib.utils import safe_traverse_attrs
from application.models.actions import Action, ActionType
from application.models.client import BloodHistory
from application.models.enums import Gender, AllergyPower, IntoleranceType
from application.models.exists import rbAttachType
from application.systemwide import cache, db
from ..risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, mother_codes, father_codes, risar_father_anamnesis, risar_mother_anamnesis, \
    checkup_flat_codes, risar_epicrisis, risar_newborn_inspection
from ..lib.utils import risk_rates_diagID, risk_rates_blockID, week_postfix

__author__ = 'mmalkov'


def represent_event(event):
    """
    :type event: application.models.event.Event
    """
    client = event.client

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
        'anamnesis': represent_anamnesis(event),
        'epicrisis': represent_epicrisis(event),
        'checkups': represent_checkups(event),
        'risk_rate': get_risk_rate(get_all_diagnoses(event.actions)),
        'pregnancy_week': get_pregnancy_week(event)
    }


def get_lpu_attached(attachments):

    return {
        'plan_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 10).first(),
        'extra_lpu': attachments.join(rbAttachType).filter(rbAttachType.code == 11).first()
    }


def get_all_diagnoses(actions):
    result = []
    if actions:
        for action in actions:
            for property in action.properties:
                if property.type.typeName == 'MKB' and property.value:
                    result.extend(property.value) if isinstance(property.value, list) else result.append(property.value)
    return result


def get_risk_rate(diagnoses):
    risk_rate = {'value': 0, 'note': u"У пациентки риск невынашивания не выявлен"}
    for diag in diagnoses:
        if diag.DiagID in risk_rates_diagID['high'] or diag.BlockID in risk_rates_blockID['high']:
            risk_rate = {'value': 3, 'note': u"Внимание! У пациентки выявлен высокий риск невынашивания "}
            break
        elif diag.DiagID in risk_rates_diagID['middle'] or diag.BlockID in risk_rates_blockID['middle']:
            risk_rate = {'value': 2, 'note':  u"У пациентки выявлен средний риск невынашивания "}
        elif diag.DiagID in risk_rates_diagID['low'] or diag.BlockID in risk_rates_blockID['low']:
            risk_rate = {'value': 1, 'note': u"У пациентки выявлен низкий риск невынашивания "}
    return risk_rate


def get_pregnancy_week(event):
    date = datetime.datetime.today()
    inspection_pregnancy_week, inspection_date = None, None
    inspections = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)).order_by(Action.begDate.desc())
    for inspection in inspections:
        if inspection.propsByCode['pregnancy_week'].value:
            inspection_pregnancy_week, inspection_date = inspection.propsByCode['pregnancy_week'].value, inspection.begDate
            break

    epicrisis = get_action(event, risar_epicrisis)

    if epicrisis:
        ch_b_date = epicrisis.propsByCode['ch_b_date'].value
        if ch_b_date:
            return inspection_pregnancy_week + (ch_b_date - inspection_date.date()).days/7  # на какой неделе произошли роды

    if inspection_pregnancy_week:
        return inspection_pregnancy_week + (date - inspection_date).days/7

    mother_action = get_action(event, risar_mother_anamnesis)
    if mother_action:
        menstruation_last_date = mother_action.propsByCode['menstruation_last_date'].value
        if menstruation_last_date:
            return (date.date() - menstruation_last_date).days/7 + 1  # расчет срока беременности по дате последней менструации
    return None


@cache.memoize()
def get_action_type_id(flat_code):
    selectable = db.select((ActionType.id, ), whereclause=ActionType.flatCode == flat_code, from_obj=ActionType)
    row = db.session.execute(selectable).first()
    if not row:
        return None
    return row[0]


def action_apt_values(action, codes):
    return dict((key, safe_traverse_attrs(action.propsByCode.get(key), 'value')) for key in codes)


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


def get_action(event, flat_code, create=False):
    """
    :type flat_code: list|tuple|basestring|None
    :param event:
    :param flat_code:
    :return:
    """
    query = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0)
    if isinstance(flat_code, (list, tuple)):
        query = query.filter(ActionType.flatCode.in_(flat_code))
    elif isinstance(flat_code, basestring):
        query = query.filter(ActionType.flatCode == flat_code)
    elif flat_code is None:
        return
    else:
        raise TypeError('flat_code must be list|tuple|basestring|None')
    action = query.first()
    if action is None and create:
        action = create_action(get_action_type_id(flat_code), event)
    return action


def get_action_by_id(action_id, event, flat_code, create=False):
    """
    :param action_id:
    :return:
    """
    action = None
    if action_id:
        query = Action.query.filter(Action.id == action_id, Action.deleted == 0)
        action = query.first()
    elif create:
        action = create_action(get_action_type_id(flat_code), event)
    return action


def represent_mother_action(event, action=None):
    if action is None:
        action = get_action(event, risar_mother_anamnesis)
    if action is None:
        return

    represent_mother = dict((
        (prop.type.code, prop.value)
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
    ).order_by(Action.begDate.desc())
    return map(represent_checkup, query)


def represent_checkup(action):
    result = dict(
        (code, prop.value)
        for (code, prop) in action.propsByCode.iteritems()
    )
    result['beg_date'] = action.begDate
    result['person'] = action.person
    result['flatCode'] = action.actionType.flatCode
    result['id'] = action.id
    return result


def represent_ticket(ticket):
    from application.models.actions import Action, ActionType
    from application.models.event import Event
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
        'risk_rate': get_risk_rate(get_all_diagnoses(event.actions)) if event else None,
        'pregnancy_week': get_pregnancy_week(event) if event else None,
    }


def represent_intolerance(obj):
    from application.models.client import ClientAllergy, ClientIntoleranceMedicament
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
        info = u'<b>Беременность закончилась</b> '
        pregnancy_final = epicrisis['pregnancy_final']['name'] if epicrisis['pregnancy_final'] else ''
        week = u'недель' if 5 <= epicrisis['pregnancy_duration'] <= 20 else (u'недел' + week_postfix[epicrisis['pregnancy_duration'] % 10])
        is_dead = bool(epicrisis['death_date'] or ['reason_of_death'])
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
            info += pregnancy_final

        if is_complications:
            info += u' с осложнениями'
        info += u' при сроке {0} {1}'.format(epicrisis['pregnancy_duration'], week)

        if pregnancy_final == u'родами':
            info += u' {0} {1}.<br>'.format(epicrisis['ch_b_date'].strftime("%d.%m.%y"), epicrisis['ch_b_time'])
        elif pregnancy_final == u'абортом':
            info += u' {0} {1}.<br>'.format(epicrisis['abort_date'].strftime("%d.%m.%y"), epicrisis['abort_time'])

        info += u"<b>Место родоразрешения</b>: {0}.<br>".format(epicrisis['LPU'].shortName)

        if is_manipulations and is_operations:
            info += u'Были осуществлены пособия и манипуляции и проведены операции. '
        elif is_manipulations:
            info += u'Были осуществлены пособия и манипуляции. '
        elif is_operations:
            info += u'Были проведены операции. '

        if epicrisis['newborn_inspections'] and pregnancy_final != u'абортом':
            info += u'<b>Дети</b> ({}): '.format(len(epicrisis['newborn_inspections']))

            children_info = []
            for child in epicrisis['newborn_inspections']:
                if child['sexCode'] == 1:
                    children_info.append(u'мальчик ' + (u'живой' if child['alive'] else u'мертвый'))
                else:
                    children_info.append(u'девочка ' + (u'живая' if child['alive'] else u'мертвая'))
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
    finish_date = epicrisis['ch_b_date'] if epicrisis['pregnancy_final']['code'] == 'rodami' else epicrisis['abort_date']
    pregnancy_week = get_pregnancy_week(event)
    epicrisis['registration_pregnancy_week'] = pregnancy_week - (finish_date - event.setDate.date()).days/7
    epicrisis['newborn_inspections'] = represent_newborn_inspections(event)
    epicrisis['info'] = make_epicrisis_info(epicrisis)
    return epicrisis


def represent_newborn_inspections(event):
    newborn_inspections = []
    actions = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0,
                                                   ActionType.flatCode == risar_newborn_inspection).all()

    for action in actions:
        inspection = dict((code, prop.value) for (code, prop) in action.propsByCode.iteritems())
        inspection['id'] = action.id
        if inspection['sexCode'] == 1:
            inspection['sex'] = u'мужской'
        elif inspection['sexCode'] == 2:
            inspection['sex'] = u'женский'
        newborn_inspections.append(inspection)
    return newborn_inspections
