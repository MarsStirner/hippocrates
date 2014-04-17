# -*- coding: utf-8 -*-

import datetime
from application.models.exists import (ClientPolicy, ClientAllergy, ClientIntoleranceMedicament,
    ClientContact, ClientIdentification, DirectClientRelation, ReversedClientRelation, ClientSocStatus,
    ClientDocument, Client, rbDocumentType, rbPolicyType, rbSocStatusClass, rbSocStatusType,
    BloodHistory, rbBloodType, rbAccountingSystem, rbContactType, rbRelationType)


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
    now = datetime.datetime.now()
    doc = client.documents.filter(ClientDocument.id == document_info['id']).first()

    def _big_changes(d, d_info):
        if (d.documentType.code != d_info['typeCode']
                or d.serial != d_info['serial']
                or d.number != d_info['number']):
            return True
        return False

    if _big_changes(doc, document_info):
        new_doc = get_new_document(document_info)
        doc.deleted = 2
        doc.modifyDatetime = now
        return (doc, new_doc)
    else:
        doc.serial = document_info['serial']
        doc.number = document_info['number']
        doc.date = document_info['begDate']
        doc.endDate = document_info['endDate']
        doc.origin = document_info['origin']
        doc.modifyDatetime = now
        return (doc, None)


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
    policy = client.policies.filter(ClientPolicy.id == policy_info['id']).first()

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
        return (policy, new_policy)
    else:
        policy.begDate = policy_info['begDate']
        policy.endDate = policy_info['endDate']
        policy.insurer_id = policy_info['insurer_id']
        policy.modifyDatetime = now
        return (policy, None)


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
    ss.modifyDatetime = now
    return ss


def get_new_blood(blood_info):
    b = BloodHistory()
    b.createDatetime = b.modifyDatetime = datetime.datetime.now()
    b.version = 0
    b.bloodType = rbBloodType.query.filter(rbBloodType.code == blood_info['bloodGroup_code']).first()
    b.bloodDate = blood_info['bloodDate']
    b.person_id = blood_info['person_id']
    return b


def get_new_allergy(allergy_info):
    a = ClientAllergy()
    a.createDatetime = a.modifyDatetime = datetime.datetime.now()
    a.version = 0
    a.deleted = allergy_info['deleted']
    a.name = allergy_info['nameSubstance']
    a.createDate = allergy_info['createDate']#.split('T')[0]
    a.power = allergy_info['power']
    a.notes = allergy_info['notes']
    a.deleted = allergy_info['deleted']
    return a


def get_modified_allergy(client, allergy_info):
    now = datetime.datetime.now()
    a = client.allergies.filter(ClientAllergy.id == allergy_info['id']).first()

    if allergy_info['deleted'] == 1:
        a.deleted = 1
        return a

    a.name = allergy_info['nameSubstance']
    a.createDate = allergy_info['createDate']#.split('T')[0]
    a.power = allergy_info['power']
    a.notes = allergy_info['notes']
    a.deleted = allergy_info['deleted']
    a.modifyDatetime = now
    return a


def get_new_intolerance(intolerance_info):
    i = ClientIntoleranceMedicament()
    i.createDatetime = i.modifyDatetime = datetime.datetime.now()
    i.version = 0
    i.deleted = intolerance_info['deleted']
    i.name = intolerance_info['nameMedicament']
    i.createDate = intolerance_info['createDate']
    i.power = intolerance_info['power']
    i.notes = intolerance_info['notes']
    i.deleted = intolerance_info['deleted']
    return i


def get_modified_intolerance(client, intolerance_info):
    now = datetime.datetime.now()
    i = client.allergies.filter(ClientIntoleranceMedicament.id == intolerance_info['id']).first()

    if intolerance_info['deleted'] == 1:
        i.deleted = 1
        return i

    i.name = intolerance_info['nameMedicament']
    i.createDate = intolerance_info['createDate']
    i.power = intolerance_info['power']
    i.notes = intolerance_info['notes']
    i.deleted = intolerance_info['deleted']
    i.modifyDatetime = now
    return i


def get_new_identification(id_info):
    id_ext = ClientIdentification()
    id_ext.createDatetime = id_ext.modifyDatetime = datetime.datetime.now()
    id_ext.version = 0
    id_ext.deleted = id_info['deleted']
    id_ext.accountingSystems = rbAccountingSystem.query.filter(
        rbAccountingSystem.code == id_info['accountingSystem_code']).first()
    id_ext.checkDate = id_info['checkDate']
    id_ext.identifier = id_info['identifier']
    return id_ext


def get_modified_identification(client, id_info):
    now = datetime.datetime.now()
    id_ext = client.identifications.filter(ClientIdentification.id == id_info['id']).first()

    if id_info['deleted'] == 1:
        id_ext.deleted = 1
        return id_ext

    id_ext.accountingSystems = rbAccountingSystem.query.filter(
        rbAccountingSystem.code == id_info['accountingSystem_code']).first()
    id_ext.checkDate = id_info['checkDate']
    id_ext.identifier = id_info['identifier']
    id_ext.modifyDatetime = now
    return id_ext


def get_new_direct_relation(relation_info):
    rel = DirectClientRelation()
    rel.createDatetime = rel.modifyDatetime = datetime.datetime.now()
    rel.version = 0
    rel.deleted = relation_info['deleted']
    rel.relativeType = rbRelationType.query.filter(
        rbRelationType.code == relation_info['relativeType']['code']).first()
    rel.other = Client.query.filter(Client.id == relation_info['other_id']).first()
    return rel


def get_modified_direct_relation(client, relation_info):
    now = datetime.datetime.now()
    rel = client.direct_relations.filter(DirectClientRelation.id == relation_info['id']).first()

    if relation_info['deleted'] == 1:
        rel.deleted = 1
        return rel

    rel.relativeType = rbRelationType.query.filter(
        rbRelationType.code == relation_info['relativeType']['code']).first()
    rel.other = Client.query.filter(Client.id == relation_info['other_id']).first()
    rel.modifyDatetime = now
    return rel


def get_new_reversed_relation(relation_info):
    rel = ReversedClientRelation()
    rel.createDatetime = rel.modifyDatetime = datetime.datetime.now()
    rel.version = 0
    rel.deleted = relation_info['deleted']
    rel.relativeType = rbRelationType.query.filter(
        rbRelationType.code == relation_info['relativeType']['code']).first()
    rel.other = Client.query.filter(Client.id == relation_info['other_id']).first()
    return rel


def get_modified_reversed_relation(client, relation_info):
    now = datetime.datetime.now()
    rel = client.reversed_relations.filter(ReversedClientRelation.id == relation_info['id']).first()

    if relation_info['deleted'] == 1:
        rel.deleted = 1
        return rel

    rel.relativeType = rbRelationType.query.filter(
        rbRelationType.code == relation_info['relativeType']['code']).first()
    rel.other = Client.query.filter(Client.id == relation_info['other_id']).first()
    rel.modifyDatetime = now
    return rel


def get_new_contact(contact_info):
    con = ClientContact()
    con.createDatetime = con.modifyDatetime = datetime.datetime.now()
    con.version = 0
    con.contactType = rbContactType.query.filter(rbContactType.code == contact_info['contactType_code']).first()
    con.contact = contact_info['contact']
    con.deleted = contact_info['deleted']
    con.notes = contact_info['notes']
    return con


def get_modified_contact(client, contact_info):
    now = datetime.datetime.now()
    con = client.contacts.filter(ClientContact.id == contact_info['id']).first()

    if contact_info['deleted'] == 1:
        con.deleted = 1
        return con

    con.contactType = rbContactType.query.filter(rbContactType.code == contact_info['contactType_code']).first()
    con.contact = contact_info['contact']
    con.deleted = contact_info['deleted']
    con.notes = contact_info['notes']
    con.modifyDatetime = now
    return con


def get_deleted_document(client, doc_info):
    if 'documentText' in doc_info:
        doc = ClientDocument.query.get(doc_info['id'])
    elif 'policyText' in doc_info:
        doc = ClientPolicy.query.get(doc_info['id'])
    doc.deleted = 1
    return doc