# -*- coding: utf-8 -*-

from nemesis.models.organisation import Organisation
from nemesis.models.person import Person


def get_org_by_tfoms_code(tfoms_code):
    org = Organisation.query.filter(
        Organisation.TFOMSCode == tfoms_code,
        Organisation.deleted == 0
    ).first()
    return org


def get_person_by_code(code):
    # TODO: what code?
    person = Person.query.filter(
        Person.regionalCode == code,
        Person.deleted == 0
    ).first()
    return person