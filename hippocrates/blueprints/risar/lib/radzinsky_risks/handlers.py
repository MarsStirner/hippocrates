# -*- coding: utf-8 -*-

from nemesis.lib.utils import safe_bool


def mother_younger_18(card):
    return card.event.client.age_tuple()[3] < 18


def mother_older_40(card):
    return card.event.client.age_tuple()[3] >= 18


def father_older_40(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return anamnesis['age'].value is not None and anamnesis['age'].value >= 40
    return False


def mother_professional_properties(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['professional_properties'].value is not None and \
               anamnesis['professional_properties'].value_raw != 'psychic_tension'
    return False


def father_professional_properties(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return anamnesis['professional_properties'].value is not None
    return False


def mother_smoking(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return safe_bool(anamnesis['smoking'].value)
    return False


def mother_alcohol(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def father_alcohol(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return safe_bool(anamnesis['alcohol'].value)
    return False


def emotional_stress(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['professional_properties'].value_raw == 'psychic_tension'
    return False


def height_less_150(card):
    fi = card.first_inspection
    if fi:
        return fi['height'].value is not None and \
               fi['height'].value <= 150
    return False


def overweight(card):
    fi = card.first_inspection
    if fi:
        weight = fi['weight'].value
        height = fi['height'].value
        return weight is not None and height is not None and float(height - 100) * 1.25 < weight
    return False


def not_married(card):
    anamnesis = card.anamnesis.mother
    if anamnesis:
        return anamnesis['marital_status'].value_raw in ('01', '02', '05', '06')
    return False