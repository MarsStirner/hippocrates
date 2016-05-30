# -*- coding: utf-8 -*-


def mother_younger_18(card):
    return card.event.client.age_tuple()[3] < 18


def mother_older_40(card):
    return card.event.client.age_tuple()[3] >= 18


def father_older_40(card):
    anamnesis = card.anamnesis.father
    if anamnesis:
        return anamnesis['age'].value is not None and anamnesis['age'].value >= 40
    return False