# -*- coding: utf-8 -*-
from nemesis.lib.utils import safe_bool_none

__author__ = 'viruzzz-kun'


def represent_concilium(concilium):
    return {
        'id': concilium.id,
        'date': concilium.date,
        'hospital': concilium.hospital,
        'doctor': concilium.doctor,
        'patient_presence': safe_bool_none(concilium.patient_presence),
        'mkb': concilium.mkb,
        'reason': concilium.reason,
        'patient_condition': concilium.patient_condition,
        'decision': concilium.decision,
        'members': [
            represent_concilium_member(member)
            for member in concilium.members
        ]
    }


def represent_concilium_member(member):
    return {
        'doctor': member.person,
        'opinion': member.opinion
    }