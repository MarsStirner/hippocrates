# -*- coding: utf-8 -*-

import datetime
from application.models.exists import (ClientPolicy, ClientAllergy, ClientIntoleranceMedicament,
    ClientContact, ClientIdentification, DirectClientRelation, ReversedClientRelation, ClientSocStatus,
    ClientDocument, Client, rbDocumentType, rbPolicyType, rbSocStatusClass, rbSocStatusType)

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


def create_new_client():
    new_client = Client()
    new_client.createDatetime = new_client.modifyDatetime = datetime.datetime.now()
    new_client.version = 0
    new_client.bloodNotes = ''
    new_client.growth = 0
    new_client.weight = 0
    return new_client


def get_new_document(document_info):
    doc = ClientDocument()
    doc.createDatetime = doc.modifyDatetime = datetime.datetime.now()
    doc.version = 0
    doc.serial = document_info['serial']
    doc.number = document_info['number']
    doc.date = document_info['begDate']
    doc.endDate = document_info['endDate']
    doc.origin = document_info['origin']
    doc.documentType = rbDocumentType.query.filter(
        rbDocumentType.code == document_info['typeCode']).first()
    return doc


def get_modified_document(client, document_info):
    doc = client.get_document_by_id(document_info['id'])
    doc.modifyDatetime = datetime.datetime.now()
    doc.serial = document_info['serial']
    doc.number = document_info['number']
    doc.date = document_info['begDate']
    doc.endDate = document_info['endDate']
    doc.origin = document_info['origin']
    doc.documentType = rbDocumentType.query.filter(
        rbDocumentType.code == document_info['typeCode']).first()
    return doc


def get_new_policy(policy_info):
    policy = ClientPolicy()
    policy.createDatetime = policy.modifyDatetime = datetime.datetime.now()
    policy.version = 0
    policy.policyType = rbPolicyType.query.filter(rbPolicyType.code == policy_info['typeCode']).first()
    policy.serial = policy_info.get('serial')
    policy.number = policy_info['number']
    policy.begDate = policy_info.get('begDate')
    policy.endDate = policy_info.get('endDate')
    policy.insurer_id = policy_info['insurer_id']
    return policy


def get_modified_policy(client, policy_info):
    now = datetime.datetime.now()
    policy = client.get_policy_by_id(policy_info['id'])

    if policy_info['deleted'] == 1:
        policy.deleted = 1
        return [policy, ]

    def _big_changes(p, p_info):
        if (p.policyType.code != p_info['typeCode']
                or p.serial != p_info['serial']
                or p.number != p_info['number']):
            return True
        return False

    if _big_changes(policy, policy_info):
        new_policy = get_new_policy(policy_info)
        policy.deleted = 2
        policy.modifyDatetime = now
        return [policy, new_policy]
    else:
        policy.begDate = policy_info['begDate']
        policy.endDate = policy_info['endDate']
        policy.insurer_id = policy_info['insurer_id']
        policy.modifyDatetime = now
        return [policy, ]


def get_new_soc_status(ss_info):
    ss = ClientSocStatus()
    ss.createDatetime = ss.modifyDatetime = datetime.datetime.now()
    ss.version = 0
    ss.deleted = ss_info['deleted']
    ss.soc_status_class = rbSocStatusClass.query.filter(
        rbSocStatusClass.code == ss_info['classCode']).first()
    ss.socStatusType = rbSocStatusType.query.filter(
        rbSocStatusType.code == ss_info['typeCode']).first()
    ss.begDate = ss_info['begDate']#.split('T')[0]
    ss.endDate = ss_info['endDate']
    return ss


def get_modified_soc_status(client, ss_info):
    now = datetime.datetime.now()
    ss = client.socStatuses.filter(ClientSocStatus.id == ss_info['id']).first()

    if ss_info['deleted'] == 1:
        ss.deleted = 1
        return ss

    ss.soc_status_class = rbSocStatusClass.query.filter(
        rbSocStatusClass.code == ss_info['classCode']).first()
    ss.socStatusType = rbSocStatusType.query.filter(
        rbSocStatusType.code == ss_info['typeCode']).first()
    ss.begDate = ss_info['begDate']#.split('T')[0]
    ss.endDate = ss_info['endDate']
    return ss
