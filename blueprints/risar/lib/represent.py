# -*- coding: utf-8 -*-
from application.lib.utils import safe_dict
from application.models.enums import Gender

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
            'snils': client.SNILS,
            'full_name': client.nameText,
            'notes': client.notes,
            'age_tuple': client.age_tuple(),
            'age': client.age,
            'sex_raw': client.sexCode,

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
        'characteristics': {
            'allergies': client.allergies.all() if client.id else None,
            'intolerances': client.intolerances.all() if client.id else None,
        },
        'anamnesis': {
            'data': 'Yo! No data yet!'
        },
        'epicrisis': {
            'text': 'Well, no epicrisis yet...'
        },
        'checkups': [
            {
                'data': 1
            },
            {
                'data': 2
            }
        ]
    }
