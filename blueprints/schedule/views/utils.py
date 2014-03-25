# -*- coding: utf-8 -*-

import datetime
from blueprints.schedule.models.exists import ClientPolicy, ClientAllergy, ClientIntoleranceMedicament, ClientContact, \
    ClientIdentification, DirectClientRelation, ReversedClientRelation, ClientSocStatus, ClientDocument, Client, \
    rbDocumentType

#
# def format_snils(SNILS):
#     if SNILS:
#         s = SNILS+' '*14
#         return s[0:3]+'-'+s[3:6]+'-'+s[6:9]+' '+s[9:11]
#     else:
#         return u''
#
#
# def unformat_snils(snils):
#     return snils.replace('-', '').replace(' ', '')
#
#
# def calc_snils_сheck_сode(snils):
#     result = 0
#     for i in xrange(9):
#         result += (9-i)*int(snils[i])
#     result = result % 101
#     if result == 100:
#         result = 0
#     return '%02.2d' % result
#
#
# def check_snils(snils):
#     raw = unformat_snils(snils)
#     if len(raw) == 11:
#         return raw[:9] <= '001001998' or raw[-2:] == calc_snils_сheck_сode(raw)
#     return False
#
#
# def fix_snils(SNILS):
#     raw = unformat_snils(SNILS)
#     return (raw+'0'*11)[:9] + calc_snils_сheck_сode(raw)
#
#
# def check_snils_entered(snils):
#     SNILS = unformat_snils(snils)
#     if SNILS:
#         if len(SNILS) != 11:
#             result = u'СНИЛС указан с ошибкой. Необходимо ввести 11 цифр!'
#             return result
#         elif not check_snils(SNILS):
#             fixedSNILS = format_snils(fix_snils(SNILS))
#             result = u'СНИЛС указан с ошибкой.\nПравильный СНИЛС %s\nИсправить?' % fixedSNILS
#             return result
#     return True


def check_edit_policy(policy, serial, number, type):
    if policy.number == number and policy.serial == serial and policy.policyType.code == type:
        return True
    return False


def create_new_policy(policy_info, client_id):
    client_policy = ClientPolicy()
    client_policy.clientId = client_id
    client_policy.createDatetime = datetime.datetime.now()
    client_policy.modifyDatetime = datetime.datetime.now()
    client_policy.serial = policy_info['serial']
    client_policy.number = policy_info['number']
    client_policy.begDate = policy_info['begDate']
    client_policy.endDate = policy_info['endDate']
    return client_policy


def create_new_allergy(client_id):
    new_allergy = ClientAllergy()
    new_allergy.client_id = client_id
    new_allergy.createDatetime = datetime.datetime.now()
    new_allergy.modifyDatetime = datetime.datetime.now()
    new_allergy.version = 0
    return new_allergy


def create_new_intolerance(client_id):
    new_intolerance = ClientIntoleranceMedicament()
    new_intolerance.client_id = client_id
    new_intolerance.createDatetime = datetime.datetime.now()
    new_intolerance.modifyDatetime = datetime.datetime.now()
    new_intolerance.version = 0
    return new_intolerance


def create_new_contact(client_id):
    new_contact = ClientContact()
    new_contact.client_id = client_id
    new_contact.createDatetime = datetime.datetime.now()
    new_contact.modifyDatetime = datetime.datetime.now()
    new_contact.version = 0
    return new_contact


def create_new_identification(client_id):
    new_identification = ClientIdentification()
    new_identification.client_id = client_id
    new_identification.createDatetime = datetime.datetime.now()
    new_identification.modifyDatetime = datetime.datetime.now()
    new_identification.version = 0
    return new_identification


def create_new_direct_relation(client_id):
    new_relation = DirectClientRelation()
    new_relation.client_id = client_id
    new_relation.createDatetime = datetime.datetime.now()
    new_relation.modifyDatetime = datetime.datetime.now()
    new_relation.version = 0
    return new_relation


def create_new_reversed_relation(client_id):
    new_relation = ReversedClientRelation()
    new_relation.relative_id = client_id
    new_relation.createDatetime = datetime.datetime.now()
    new_relation.modifyDatetime = datetime.datetime.now()
    new_relation.version = 0
    return new_relation


def create_new_soc_status(client_id):
    new_status = ClientSocStatus()
    new_status.client_id = client_id
    new_status.createDatetime = datetime.datetime.now()
    new_status.modifyDatetime = datetime.datetime.now()
    new_status.version = 0
    return new_status


def create_new_document(client_id, document_info):
    new_document = ClientDocument()
    new_document .client_id = client_id
    fill_in_new_record(new_document)
    new_document.serial = document_info['serial']
    new_document.number = document_info['number']
    new_document.date = document_info['begDate']
    new_document.endDate = document_info['endDate']
    new_document.documentType = rbDocumentType.query.filter(rbDocumentType.code == document_info['typeCode']).first()
    return new_document


def fill_in_new_record(record):
    record.createDatetime = datetime.datetime.now()
    record.modifyDatetime = datetime.datetime.now()
    record.version = 0


def create_new_client():
    new_client = Client()
    fill_in_new_record(new_client)
    new_client.bloodNotes = ''
    new_client.growth = 0
    new_client.weight = 0
    return new_client
