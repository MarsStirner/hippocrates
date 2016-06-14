# -*- coding: utf-8 -*-

from sqlalchemy import func
from nemesis.systemwide import db
from nemesis.models.person import PersonContact
from nemesis.models.exists import rbContactType


def get_person_contacts(person_id, delimiter=", "):
    """

    @param person_id:
    @param delimiter:
    @return: dict('02'="+79312694076, ", "12"="skype1, skype2")
    """
    contacts = db.session.query(rbContactType.code,
                                func.group_concat(PersonContact.value.op('SEPARATOR')(delimiter))). \
        join(PersonContact). \
        filter(PersonContact.person_id == person_id,
               PersonContact.deleted != 1). \
        group_by(PersonContact.contactType_id).all()
    return contacts

def person_contacts_for_errand(person_id,
                               phone_codes=[u"01", u"02", u"03", u"13"],
                               skype_code=u"12",
                               email_code=u"04",
                               delimiter=", "
                               ):
    """

    @param person_id: Person.id
    @param phone_codes: list of phones from rbContactType
    @param skype_code: rbContactType
    @param email_code: rbContactType
    @param delimiter: ","
    @return:
    """

    contacts = get_person_contacts(person_id, delimiter)
    dc = dict(contacts)
    template = ''
    if dc:
        skypes = dc.get(skype_code)
        emails = dc.get(email_code)
        phones = []

        for x in phone_codes:
            any_phone = dc.get(x)
            if any_phone:
                phones.append(any_phone)

        if phones:
            template += u"Телефоны: %s \n" % "{0}".format(delimiter).join(phones)

        if emails:
            template += u"Email: %s \n" % emails

        if skypes:
            template += u"Skype: %s \n" % skypes

    return template


