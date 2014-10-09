# -*- coding: utf-8 -*-
import datetime
import itertools

from application.lib.utils import safe_traverse_attrs
from application.models.actions import Action, ActionType
from application.models.client import BloodHistory
from application.models.enums import Gender, AllergyPower, IntoleranceType
from application.systemwide import cache, db
from ..risar_config import pregnancy_apt_codes, risar_anamnesis_pregnancy, transfusion_apt_codes, \
    risar_anamnesis_transfusion, mother_codes, father_codes


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
        'epicrisis': None,
        'checkups': [
            {
                'beg_date': datetime.date(2014, 7, 15),
                'person_name': u'Занкоков Тенши Ноёнивич',
                'diag': {
                    'code': 'O.10',
                    'name': u'Существовавшая ранее гипертензия, осложняющая беременность, роды и послеродовой период',
                }
            },
            {
                'beg_date': datetime.date(2014, 8, 6),
                'person_name': u'Занкоков Тенши Ноёнивич',
                'diag': {
                    'code': 'O.15',
                    'name': u'Эклампсия',
                }
            },
            {
                'beg_date': datetime.date(2014, 8, 14),
                'person_name': u'Занкоков Тенши Ноёнивич',
                'diag': {
                    'code': 'O.10',
                    'name': u'Существовавшая ранее гипертензия, осложняющая беременность, роды и послеродовой период',
                }
            },
            {
                'beg_date': datetime.date(2014, 8, 19),
                'person_name': u'Занкоков Тенши Ноёнивич',
                'diag': {
                    'code': 'O.15',
                    'name': u'Эклампсия',
                }
            },
            {
                'beg_date': datetime.date(2014, 8, 24),
                'person_name': u'Шоненова Шинвани Наровна',
                'diag': {
                    'code': 'O.10',
                    'name': u'Существовавшая ранее гипертензия, осложняющая беременность, роды и послеродовой период',
                }
            },
            {
                'beg_date': datetime.date(2014, 9, 1),
                'person_name': u'Шоненова Шинвани Наровна',
                'diag': {
                    'code': 'O.15',
                    'name': u'Эклампсия',
                }
            },
            {
                'beg_date': datetime.date(2014, 9, 7),
                'person_name': u'Шоненова Шинвани Наровна',
                'diag': {
                    'code': 'O.10',
                    'name': u'Существовавшая ранее гипертензия, осложняющая беременность, роды и послеродовой период',
                }
            },
        ]
    }


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
    mother = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode == 'risar_mother_anamnesis').first()
    father = Action.query.join(ActionType).filter(
        Action.event == event,
        Action.deleted == 0,
        ActionType.flatCode == 'risar_father_anamnesis').first()

    represent_mother = represent_anamnesis_action(mother, True) if mother else None
    represent_father = represent_anamnesis_action(father, False) if father else None

    if represent_mother is not None:
        mother_blood_type = BloodHistory.query \
            .filter(BloodHistory.client_id == event.client_id) \
            .order_by(BloodHistory.bloodDate.desc()) \
            .first()
        if mother_blood_type:
            represent_mother['blood_type'] = mother_blood_type.bloodType

    return {
        'mother': represent_mother,
        'father': represent_father,
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


def represent_anamnesis_action(action, mother=False):
    """
    :type action: application.models.actions.Action
    :type mother: bool
    :param action:
    :param mother:
    :return:
    """
    codes = mother_codes if mother else father_codes
    return dict(
        (prop.type.code, prop.value)
        for prop in action.properties
        if prop.type.code in codes
    )

checkup_flat_codes = ['risarFirstInspection', 'risarSecondInspection']


def represent_ticket(ticket):
    from application.models.actions import Action, ActionType
    checkup_n = 0
    event_id = ticket.client_ticket.event_id if ticket.client_ticket else None
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