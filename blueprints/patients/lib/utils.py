# -*- coding: utf-8 -*-

import datetime
import re

from application.models.client import Client, ClientAllergy, ClientContact, ClientDocument, ClientIdentification, \
    ClientIntoleranceMedicament, DirectClientRelation, ReversedClientRelation, ClientSocStatus, ClientPolicy, \
    BloodHistory, ClientAddress, Address, AddressHouse
from application.models.exists import (rbDocumentType, rbPolicyType, rbSocStatusClass, rbSocStatusType,
                                       rbBloodType, rbAccountingSystem, rbContactType, rbRelationType)
from application.lib.utils import string_to_datetime, safe_date, safe_traverse, get_new_uuid


# def format_snils(SNILS):
#     if SNILS:
#         s = SNILS+' '*14
#         return s[0:3]+'-'+s[3:6]+'-'+s[6:9]+' '+s[9:11]
#     else:
#         return u''

def unformat_snils(snils):
    return snils.replace('-', '').replace(' ', '')


class ClientSaveException(Exception):
    def __init__(self, message, data=None):
        super(ClientSaveException, self).__init__(message)
        self.data = data


def is_valid_name(name):
    # todo: ...
    return True, ''


def check_correct_snils_code(snils):
    def calc_snils_check_code(snils):
        result = 0
        for i in xrange(9):
            result += (9-i)*int(snils[i])
        result = result % 101
        if result == 100:
            result = 0
        return '%02.2d' % result

    return snils[:9] <= '001001998' or snils[-2:] == calc_snils_check_code(snils)


def check_snils(snils):
    if len(snils) != 11:
        return False, u'Код СНИЛС должен состоять из 11 цифр'
    elif not check_correct_snils_code(snils):
        return False, u'Введен некорректный код СНИЛС'
    return True, ''


def set_client_main_info(client, data):
    # TODO: re validation
    last_name = data.get('last_name')
    if not last_name:
        raise ClientSaveException(u'Отсутствует обязательное поле Фамилия')
    ok, msg = is_valid_name(last_name)
    if not ok:
        raise ClientSaveException(u'Фамилия содержит недопустимые символы: %s' % msg)
    client.lastName = last_name

    first_name = data.get('first_name')
    if not first_name:
        raise ClientSaveException(u'Отсутствует обязательное поле Имя')
    ok, msg = is_valid_name(first_name)
    if not ok:
        raise ClientSaveException(u'Имя содержит недопустимые символы: %s' % msg)
    client.firstName = first_name

    patr_name = data.get('patr_name', '')
    ok, msg = is_valid_name(patr_name)
    if not ok:
        raise ClientSaveException(u'Отчество содержит недопустимые символы: %s' % msg)
    client.patrName = patr_name

    birth_date = safe_date(data.get('birth_date'))
    if not birth_date:
        raise ClientSaveException(u'Отсутствует обязательное поле Дата рождения')
    client.birthDate = birth_date

    sex = safe_traverse(data, 'sex', 'id')
    if not sex:
        raise ClientSaveException(u'Отсутствует обязательное поле Пол')
    client.sexCode = sex

    snils = unformat_snils(data.get('snils', ''))
    if snils:
        ok, msg = check_snils(snils)
        if not ok:
            raise ClientSaveException(u'Ошибка сохранения поля СНИЛС: %s' % msg)
    client.SNILS = snils

    client.notes = data.get('notes', '')
    if not client.uuid:
        client.uuid = get_new_uuid()
    return client


def get_new_document(document_info):
    doc = ClientDocument()
    doc.createDatetime = doc.modifyDatetime = datetime.datetime.now()
    doc.version = 0
    doc.serial = document_info['serial']
    doc.number = document_info['number']
    doc.date = safe_date(document_info['begDate'])
    doc.endDate = safe_date(document_info['endDate'])
    doc.origin = document_info['origin']
    doc.documentType = rbDocumentType.query.filter(
        rbDocumentType.code == document_info['documentType']['code']).first()
    return doc


def get_modified_document(client, document_info):
    now = datetime.datetime.now()
    doc = client.documents.filter(ClientDocument.id == document_info['id']).first()

    def _big_changes(d, d_info):
        if (d.documentType.code != d_info['documentType']['code']
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
        doc.date = safe_date(document_info['begDate'])
        doc.endDate = safe_date(document_info['endDate'])
        doc.origin = document_info['origin']
        doc.modifyDatetime = now
        return (doc, None)


def add_or_update_policy(client, data):
    # todo: check for existing records ?
    policy_id = data.get('id')
    pol_type = safe_traverse(data, 'policy_type', 'id')
    if not pol_type:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Тип полиса')
    serial = data.get('serial')
    number = data.get('number')
    if not number:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Номер полиса')
    beg_date = data.get('beg_date')
    if not beg_date:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Дата выдачи')
    end_date = data.get('end_date')
    insurer = safe_traverse(data, 'insurer', 'id')
    if not insurer:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Выдан')
    deleted = data.get('deleted', 0)

    if policy_id:
        policy = ClientPolicy.query.get(policy_id)
        policy.serial = serial
        policy.number = number
        policy.beg_date = beg_date
        policy.end_date = end_date
        policy.insurer_id = insurer
        policy.client = client
        policy.deleted = deleted
    else:
        policy = ClientPolicy(pol_type, serial, number, beg_date, end_date, insurer, client)
    return policy


def add_or_update_soc_status(client, data):
    soc_status_id = data.get('id')
    soc_status_type = safe_traverse(data, 'ss_type', 'id')
    soc_status_class_code = safe_traverse(data, 'ss_class', 'code')
    if not soc_status_type:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Тип соц. статуса')
    beg_date = data.get('beg_date')
    if not beg_date:
        raise ClientSaveException(u'Ошибка сохранения полиса: Отсутствует обязательное поле Дата начала')
    # end_date = data.get('end_date')
    deleted = data.get('deleted', 0)

    if soc_status_id:
        soc_status = ClientSocStatus.query.get(soc_status_id)
        soc_status.socStatusType_id = soc_status_type
        soc_status.beg_date = beg_date
        soc_status.client = client
        soc_status.deleted = deleted
    else:
        soc_status_class = rbSocStatusClass.query.filter(rbSocStatusClass.code == soc_status_class_code).first().id
        soc_status = ClientSocStatus(soc_status_class, soc_status_type, beg_date, client)
    return soc_status


def get_new_address(addr_info):
    addr_type = addr_info['type']
    loc_type = safe_traverse(addr_info, 'locality_type', 'id')
    loc_kladr_code = safe_traverse(addr_info, 'address', 'locality', 'code')
    street_kladr_code = safe_traverse(addr_info, 'address', 'street', 'code')
    free_input = safe_traverse(addr_info, 'free_input')

    if (loc_kladr_code and street_kladr_code):
        house_number = safe_traverse(addr_info, 'address', 'house_number', default='')
        corpus_number = safe_traverse(addr_info, 'address', 'corpus_number', default='')
        flat_number = safe_traverse(addr_info, 'address', 'flat_number', default='')
        client_addr = ClientAddress.create_from_kladr(addr_type, loc_type, loc_kladr_code, street_kladr_code,
            house_number, corpus_number, flat_number)
    elif free_input:
        client_addr = ClientAddress.create_from_free_input(addr_type, loc_type, free_input)
    else:
        raise ValueError

    return client_addr


def get_modified_address(client, addr_info):
    addr = filter(lambda a: a.id == addr_info['id'], client.addresses)[0]

    if addr_info['deleted'] == 1:
        addr.deleted = 1
        return [addr, ]

    loc_type = safe_traverse(addr_info, 'locality_type', 'id')
    loc_kladr_code = safe_traverse(addr_info, 'address', 'locality', 'code')
    street_kladr_code = safe_traverse(addr_info, 'address', 'street', 'code')
    free_input = safe_traverse(addr_info, 'free_input')
    house_number = safe_traverse(addr_info, 'address', 'house_number', default='')
    corpus_number = safe_traverse(addr_info, 'address', 'corpus_number', default='')
    flat_number = safe_traverse(addr_info, 'address', 'flat_number', default='')

    def _big_changes(a):
        if ((a.address and a.address.KLADRCode) != loc_kladr_code or
                (a.address and a.address.KLADRStreetCode) != street_kladr_code or
                (a.address and a.address.number) != house_number or
                (a.address and a.address.corpus) != corpus_number or
                (a.address and a.address.flat) != flat_number):
            return True
        return False

    if _big_changes(addr):
        new_addr = get_new_address(addr_info)
        addr.set_deleted(2)
        return (addr, new_addr)
    else:
        addr.localityType = loc_type
        addr.freeInput = free_input
        return (addr, None)


def get_reg_address_copy(client, reg_address):
    # todo: check prev record and mark deleted
    live_ca = ClientAddress(1, reg_address.localityType)  # todo: enum
    live_ca.address = reg_address.address
    live_ca.freeInput = ''
    return live_ca


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