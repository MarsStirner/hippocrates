# -*- coding: utf-8 -*-


def get_client_info(client):
    if not client:
        return {}
    return {
        'id': client.id,
        'nameText': client.nameText,
        'birthDate': client.birthDate,
        'age': client.age,
    }


def get_org_structure_info(org_struct):
    if not org_struct:
        return {}
    return {
        'code': org_struct.code,
        'name': org_struct.name,
    }


def get_person_info(person):
    if not person:
        return {}
    return {
        'id': person.id,
        'shortNameText': person.shortNameText,
    }


def get_bed_info(bed_data):
    return {}


def get_hospitalization_info(hosp_data):
    if not hosp_data:
        return {}
    return {
        'id': hosp_data.Event.id,
        'setDate': hosp_data.Event.setDate,
        'begDate': hosp_data.begDate,
        'endDate': hosp_data.endDate,
        'client': get_client_info(hosp_data.Event.client),
        'orgStructure': {'os_stay_name': hosp_data.os_stay_name},
        'bed': {
            'os_ward_number': 100,
            'os_hosp_bed': hosp_data.os_hosp_bed,
            'hosp_length': hosp_data.hosp_length,
            # 'bed_days': 3,  # TODO: Посчитать кол-во койкодней
        },
        'execPerson': get_person_info(hosp_data.Event.execPerson),
        'diet': {'name': u'Стол 1'},
    }

