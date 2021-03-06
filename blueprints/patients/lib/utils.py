# -*- coding: utf-8 -*-

from application.models.client import ClientAllergy, ClientContact, ClientDocument, \
    ClientIntoleranceMedicament, ClientSocStatus, ClientPolicy, \
    BloodHistory, ClientAddress, ClientRelation, Address
from application.models.enums import AddressType
from application.models.exists import rbSocStatusClass
from application.lib.utils import safe_date, safe_traverse, get_new_uuid


# def format_snils(snils):
#     if snils:
#         snils = '%s-%s-%s %s' % (snils[0:3], snils[3:6], snils[6:9], snils[9:11])
#         return snils
#     else:
#         return u''

def unformat_snils(snils):
    return snils.replace('-', '').replace(' ', '')


class ClientSaveException(Exception):
    def __init__(self, message, data=None):
        super(ClientSaveException, self).__init__(message)
        self.data = data


def is_valid_name(name):
    # todo: только допустимые символы - русские буквы и тире
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
    err_msg = u'Ошибка сохранения основной информации пациента'
    last_name = data.get('last_name')
    if not last_name:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Фамилия')
    ok, msg = is_valid_name(last_name)
    if not ok:
        raise ClientSaveException(err_msg, u'Фамилия содержит недопустимые символы: %s' % msg)
    client.lastName = last_name

    first_name = data.get('first_name')
    if not first_name:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Имя')
    ok, msg = is_valid_name(first_name)
    if not ok:
        raise ClientSaveException(err_msg, u'Имя содержит недопустимые символы: %s' % msg)
    client.firstName = first_name

    patr_name = data.get('patr_name') or ''
    ok, msg = is_valid_name(patr_name)
    if not ok:
        raise ClientSaveException(err_msg, u'Отчество содержит недопустимые символы: %s' % msg)
    client.patrName = patr_name

    birth_date = safe_date(data.get('birth_date'))
    if not birth_date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата рождения')
    client.birthDate = birth_date

    sex = safe_traverse(data, 'sex', 'id')
    if not sex:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Пол')
    client.sexCode = sex

    snils = unformat_snils(data.get('snils', '') or '')
    if snils:
        ok, msg = check_snils(snils)
        if not ok:
            raise ClientSaveException(err_msg, u'Ошибка сохранения поля СНИЛС: %s' % msg)
    client.SNILS = snils

    client.notes = data.get('notes', '')
    if not client.uuid:
        client.uuid = get_new_uuid()
    return client


def add_or_update_doc(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения документа'
    doc_id = data.get('id')
    doc_type = safe_traverse(data, 'doc_type', 'id')
    if not doc_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Тип документа')
    serial = data.get('serial') or ''
    number = data.get('number')
    if not number:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Номер документа')
    beg_date = safe_date(data.get('beg_date'))
    if not beg_date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата выдачи')
    end_date = safe_date(data.get('end_date'))
    origin = data.get('origin')
    if not origin:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Выдан')
    deleted = data.get('deleted', 0)

    if doc_id:
        doc = ClientDocument.query.get(doc_id)
        doc.documentType_id = doc_type
        doc.serial = serial
        doc.number = number
        doc.date = beg_date
        doc.endDate = end_date
        doc.origin = origin
        doc.client = client
        doc.deleted = deleted
    else:
        doc = ClientDocument(doc_type, serial, number, beg_date, end_date, origin, client)
    return doc


def add_or_update_address(client, data):
    # todo: check for existing records ?
    addr_id = data.get('id')
    addr_type = data.get('type')
    msg_err = u'Ошибка сохранения адреса %s' % {0: u'регистрации', 1: u'проживания'}.get(addr_type)
    if addr_type is None:
        raise ClientSaveException(msg_err, u'Отсутствует обязательное поле Тип')
    deleted = data.get('deleted', 0)
    if deleted:
        client_addr = ClientAddress.query.get(addr_id)
        client_addr.deleted = deleted
        return client_addr

    loc_type = safe_traverse(data, 'locality_type', 'id')
    loc_kladr = safe_traverse(data, 'address', 'locality')
    loc_kladr_code = loc_kladr.get('code') if isinstance(loc_kladr, dict) else loc_kladr
    street_kladr = safe_traverse(data, 'address', 'street')
    street_kladr_code = street_kladr.get('code') if isinstance(street_kladr, dict) else street_kladr
    free_input = safe_traverse(data, 'free_input')
    house_number = safe_traverse(data, 'address', 'house_number', default='')
    corpus_number = safe_traverse(data, 'address', 'corpus_number', default='')
    flat_number = safe_traverse(data, 'address', 'flat_number', default='')

    if addr_id:
        client_addr = ClientAddress.query.get(addr_id)

        #TODO: проверить еще раз условие (client_addr.address.house.KLADRCode and client_addr.address.house.KLADRStreetCode)
        if client_addr.address and client_addr.address.house:
            if free_input:
                raise ClientSaveException(msg_err, u'попытка сохранения адреса в свободном виде для '
                                          u'записи адреса из справочника адресов. Добавьте новую запись адреса.')
            if not (loc_kladr_code and street_kladr_code):
                raise ClientSaveException(msg_err, u'Отсутствуют обязательные поля: Населенный пункт и Улица.')
            client_addr.address.flat = flat_number

            loc_kladr_code, street_kladr_code = Address.compatible_kladr(loc_kladr_code, street_kladr_code)
            client_addr.address.house.KLADRCode = loc_kladr_code
            client_addr.address.house.KLADRStreetCode = street_kladr_code
            client_addr.address.house.number = house_number
            client_addr.address.house.corpus = corpus_number
        elif client_addr.freeInput:
            if loc_kladr_code or street_kladr_code:
                raise ClientSaveException(msg_err, u'попытка сохранения адреса из справочника адресов '
                                          u'для записи адреса в свободном виде. Добавьте новую запись адреса.')
            if not free_input:
                raise ClientSaveException(msg_err, u'Отсутствует обязательное поле Адрес в свободном виде.')
            client_addr.freeInput = free_input
        else:
            raise ClientSaveException(msg_err, u'попытка сохранения адреса из справочника адресов '
                                      u'Свяжитесь с администратором.')

        client_addr.localityType = loc_type
        client_addr.deleted = deleted
    else:
        if loc_kladr_code and street_kladr_code:
            client_addr = ClientAddress.create_from_kladr(addr_type, loc_type, loc_kladr_code, street_kladr_code,
                                                          house_number, corpus_number, flat_number, client)
        elif free_input:
            client_addr = ClientAddress.create_from_free_input(addr_type, loc_type, free_input, client)
        else:
            raise ClientSaveException(msg_err, u'Отсутствуют обязательные поля: Населенный пункт и Улица '
                                      u'или Адрес в свободном виде.')
    return client_addr


def add_or_update_copy_address(client, data, copy_from):
    # todo: check for existing records ?
    msg_err = u'Ошибка сохранения адреса проживания'
    addr_id = data.get('live_id')
    deleted = data.get('deleted')
    if deleted:
        client_addr = ClientAddress.query.get(addr_id)
        client_addr.deleted = deleted
        return client_addr

    from_id = data.get('id')
    from_addr = ClientAddress.query.get(from_id) if from_id else copy_from
    if from_addr is None:
        raise ClientSaveException(msg_err, u'Для адреса проживания указано, что он совпадает с адресом регистрации, '
                                           u'но соответствующий адрес не найден. Свяжитесь с администратором.')

    if addr_id:
        client_addr = ClientAddress.query.get(addr_id)
        client_addr.address = from_addr.address
        client_addr.freeInput = from_addr.freeInput
        client_addr.localityType = from_addr.localityType
    else:
        client_addr = ClientAddress.create_from_copy(AddressType.live[0], from_addr, client)
    return client_addr


def add_or_update_policy(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения полиса'
    policy_id = data.get('id')
    pol_type = safe_traverse(data, 'policy_type', 'id')
    if not pol_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Тип полиса')
    serial = data.get('serial') or ''
    number = data.get('number')
    if not number:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Номер полиса')
    beg_date = safe_date(data.get('beg_date'))
    if not beg_date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата выдачи')
    end_date = safe_date(data.get('end_date'))
    insurer = data['insurer']
    if not (insurer['id'] or insurer['full_name']):
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Страховая медицинская организация')
    deleted = data.get('deleted', 0)

    if policy_id:
        policy = ClientPolicy.query.get(policy_id)
        policy.policyType_id = pol_type
        policy.serial = serial
        policy.number = number
        policy.begDate = beg_date
        policy.endDate = end_date
        policy.insurer_id = insurer['id']
        policy.name = insurer['full_name'] if not insurer['id'] else None
        policy.client = client
        policy.deleted = deleted
    else:
        policy = ClientPolicy(pol_type, serial, number, beg_date, end_date, insurer, client)
    return policy


def add_or_update_blood_type(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения группы крови'
    bt_id = data.get('id')
    bt_type = safe_traverse(data, 'blood_type', 'id')
    if not bt_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Группа крови')
    date = safe_date(data.get('date'))
    if not date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата установления')
    person = safe_traverse(data, 'person', 'id')
    if not person:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Врач, установивший группу крови')

    if bt_id:
        bt = BloodHistory.query.get(bt_id)
        bt.bloodDate = date
        bt.bloodType_id = bt_type
        bt.person_id = person
    else:
        bt = BloodHistory(bt_type, date, person, client)
    return bt


def add_or_update_allergy(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения аллергии'
    alg_id = data.get('id')
    alg_name = data.get('name')
    if not alg_name:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Вещество')
    alg_power = safe_traverse(data, 'power', 'id')
    if alg_power is None:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Степень')
    date = safe_date(data.get('date'))
    if not date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата установления')
    notes = data.get('notes', '') or ''
    deleted = data.get('deleted', 0)

    if alg_id:
        alg = ClientAllergy.query.get(alg_id)
        alg.name = alg_name
        alg.power = alg_power
        alg.createDate = date
        alg.notes = notes
        alg.deleted = deleted
    else:
        alg = ClientAllergy(alg_name, alg_power, date, notes, client)
    return alg


def add_or_update_intolerance(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения медикаментозной непереносимости'
    intlr_id = data.get('id')
    intlr_name = data.get('name')
    if not intlr_name:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Вещество')
    intlr_power = safe_traverse(data, 'power', 'id')
    if intlr_power is None:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Степень')
    date = safe_date(data.get('date'))
    if not date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата установления')
    notes = data.get('notes', '') or ''
    deleted = data.get('deleted', 0)

    if intlr_id:
        intlr = ClientIntoleranceMedicament.query.get(intlr_id)
        intlr.name = intlr_name
        intlr.power = intlr_power
        intlr.createDate = date
        intlr.notes = notes
        intlr.deleted = deleted
    else:
        intlr = ClientIntoleranceMedicament(intlr_name, intlr_power, date, notes, client)
    return intlr


def add_or_update_soc_status(client, data):
    err_msg = u'Ошибка сохранения соц. статуса'
    soc_status_id = data.get('id')

    deleted = data.get('deleted', 0)
    if deleted:
        soc_status = ClientSocStatus.query.get(soc_status_id)
        soc_status.deleted = deleted
        if soc_status.self_document:
            soc_status.self_document.deleted = deleted
        return soc_status

    soc_status_type = safe_traverse(data, 'ss_type', 'id')
    soc_status_class_code = safe_traverse(data, 'ss_class', 'code')
    if not soc_status_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Тип соц. статуса')
    beg_date = safe_date(data.get('beg_date'))
    if not beg_date:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Дата начала')
    end_date = safe_date(data.get('end_date'))
    doc_info = data.get('self_document')
    doc = add_or_update_doc(client, doc_info) if doc_info else None

    if soc_status_id:
        soc_status = ClientSocStatus.query.get(soc_status_id)
        soc_status.socStatusType_id = soc_status_type
        soc_status.begDate = beg_date
        soc_status.endDate = end_date
        soc_status.client = client
        soc_status.self_document = doc
    else:
        soc_status_class = rbSocStatusClass.query.filter(rbSocStatusClass.code == soc_status_class_code).first().id
        soc_status = ClientSocStatus(soc_status_class, soc_status_type, beg_date, end_date, client, doc)
    return soc_status


def add_or_update_relation(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения родственной связи'
    rel_id = data.get('id')
    rel_type = safe_traverse(data, 'rel_type', 'id')
    if not rel_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Тип')
    direct = data.get('direct')
    if direct is None:
        raise ClientSaveException(err_msg, u'Не указан вид связи - прямая или обратная')
    relative_id = safe_traverse(data, 'relative', 'id')
    if not relative_id:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Родственник')
    deleted = data.get('deleted', 0)

    if direct:
        client = client
        relative_id = relative_id
        if rel_id:
            rel = ClientRelation.query.get(rel_id)
            rel.relativeType_id = rel_type
            rel.relative_id = relative_id
            rel.client = client
            rel.deleted = deleted
        else:
            rel = ClientRelation.create_direct(rel_type, relative_id, client)
    else:
        client_id = relative_id
        relative = client
        if rel_id:
            rel = ClientRelation.query.get(rel_id)
            rel.relativeType_id = rel_type
            rel.relative = relative
            rel.client_id = client_id
            rel.deleted = deleted
        else:
            rel = ClientRelation.create_reverse(rel_type, relative, client_id)
    return rel


def add_or_update_contact(client, data):
    # todo: check for existing records ?
    err_msg = u'Ошибка сохранения контакта'
    cont_id = data.get('id')
    cont_type = safe_traverse(data, 'contact_type', 'id')
    if not cont_type:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Тип')
    text = data.get('contact_text')
    if not text:
        raise ClientSaveException(err_msg, u'Отсутствует обязательное поле Номер')
    notes = data.get('notes', '') or ''
    deleted = data.get('deleted', 0)

    if cont_id:
        cont = ClientContact.query.get(cont_id)
        cont.contactType_id = cont_type
        cont.contact = text
        cont.notes = notes
        cont.client = client
        cont.deleted = deleted
    else:
        cont = ClientContact(cont_type, text, notes, client)
    return cont


# def get_new_identification(id_info):
#     id_ext = ClientIdentification()
#     id_ext.createDatetime = id_ext.modifyDatetime = datetime.datetime.now()
#     id_ext.version = 0
#     id_ext.deleted = id_info['deleted']
#     id_ext.accountingSystems = rbAccountingSystem.query.filter(
#         rbAccountingSystem.code == id_info['accountingSystem_code']).first()
#     id_ext.checkDate = id_info['checkDate']
#     id_ext.identifier = id_info['identifier']
#     return id_ext
#
#
# def get_modified_identification(client, id_info):
#     now = datetime.datetime.now()
#     id_ext = client.identifications.filter(ClientIdentification.id == id_info['id']).first()
#
#     if id_info['deleted'] == 1:
#         id_ext.deleted = 1
#         return id_ext
#
#     id_ext.accountingSystems = rbAccountingSystem.query.filter(
#         rbAccountingSystem.code == id_info['accountingSystem_code']).first()
#     id_ext.checkDate = id_info['checkDate']
#     id_ext.identifier = id_info['identifier']
#     id_ext.modifyDatetime = now
#     return id_ext