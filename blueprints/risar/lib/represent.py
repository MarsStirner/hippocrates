# -*- coding: utf-8 -*-
import datetime
from application.lib.utils import safe_dict
from application.models.enums import Gender, AllergyPower

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
        'characteristics': [
            {
                'type': u'Аллергия',
                'name': row.name,
                'power': AllergyPower(row.power) if row.power is not None else None,
                'note': row.notes,
            }
            for row in client.allergies.all()
        ] + [
            {
                'type': u'Непереносимость',
                'name': row.name,
                'power': AllergyPower(row.power) if row.power is not None else None,
                'note': row.notes,
            }
            for row in client.intolerances.all()
        ],
        'anamnesis': {
            'mother': {
                'data': u'Данные по матери'
            },
            'father': {
                'data': u'Данные по отцу'
            },
            'transfusions': None,
            'pregnancies': None,
        },
        'epicrisis': None,
        'checkups': [
            {
                'beg_date': datetime.date(2014, 7, 15),
                'person_name': u'Занкоков Тенши Ноёнивич',
            },
            {
                'beg_date': datetime.date(2014, 8, 6),
                'person_name': u'Занкоков Тенши Ноёнивич',
            },
            {
                'beg_date': datetime.date(2014, 8, 14),
                'person_name': u'Занкоков Тенши Ноёнивич',
            },
            {
                'beg_date': datetime.date(2014, 8, 19),
                'person_name': u'Занкоков Тенши Ноёнивич',
            },
            {
                'beg_date': datetime.date(2014, 8, 24),
                'person_name': u'Шоненова Шинвани Наровна',
            },
            {
                'beg_date': datetime.date(2014, 9, 1),
                'person_name': u'Шоненова Шинвани Наровна',
            },
            {
                'beg_date': datetime.date(2014, 9, 7),
                'person_name': u'Шоненова Шинвани Наровна',
            },
        ]
    }
