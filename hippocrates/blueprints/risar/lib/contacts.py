# -*- coding: utf-8 -*-

from nemesis.models.exists import rbContactType
from nemesis.systemwide import db
from nemesis.models.person import PersonContact


def get_person_phones(person_id):
    phone_codes = [u"01", u"02", u"03", u"13"]
    phones = db.session.query(
        PersonContact.value.label('phone')
    ).join(
        rbContactType
    ).filter(
        rbContactType.code.in_(phone_codes),
        PersonContact.person_id == person_id,
        PersonContact.deleted != 1,
    )
    return [x.phone for x in phones.all()]
