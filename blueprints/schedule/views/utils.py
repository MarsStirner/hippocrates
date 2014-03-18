# -*- coding: utf-8 -*-

import datetime
from blueprints.schedule.models.exists import ClientPolicy, ClientAllergy, ClientIntoleranceMedicament

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