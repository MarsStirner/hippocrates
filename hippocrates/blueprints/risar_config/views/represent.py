# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


def represent_organisation(org):
    """
    :type org: application.models.exists.Organisation
    :param org:
    :return:
    """
    return {
        'id': org.id,
        'name': org.shortName,
        'diagnoses': org.mkbs
    }