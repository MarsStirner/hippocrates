# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class OrganizationSchema(Schema):
    """
    Схемы для проверки валидности данных организаций и лпу
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "object",
        "id": "organization",
        "properties": {
            "full_name":{
                "type": "string",
                "id": "organization/full_name",
                "description": "Полное наименование организации"
                },
            "short_name":{
                "type": "string",
                "id": "organization/short_name",
                "description": "Краткое наименование организации"
            },
            "infis_code":{
                "type": "string",
                "id": "organization/infis_code",
                "description": "Код ИНФИС"
            },
            "address":{
                "type": "string",
                "id": "organization/Address",
                "description": "Адрес организации"
            },
            "area":{
                "type": "string",
                "id": "organization/Area",
                "description": "КЛАДР-код территории для ЛПУ, первые 11 цифр",
                "pattern": "^([0-9]{11})$"
            },
            "phone":{
                "type": "string",
                "id": "organization/phone",
                "description": "Телефон организации"
            },
            "LPU_id":{
                "type": "string",
                "description": "Уникальный идентификатор ЛПУ"
            },
            "TFOMSCode":{
                "type": "string",
                "id": "organization/TFOMSCode",
                "description": "ТФОМС код организации"
            },
            "Department_TFOMSCode":{
                "type": "string",
                "description": "ТФОМС код подразделения"
            },
            "INN":{
                "type": "string",
                "id": "organization/INN",
                "description": "ИНН организации"
            },
            "KPP":{
                "type": "string",
                "id": "organization/KPP",
                "description": "КПП организации"
            },
            "OGRN":{
                "type": "string",
                "id": "organization/OGRN",
                "description": "ОГРН организации"
            },
            "OKATO":{
                "type": "string",
                "id": "organization/OKATO",
                "description": "ОКАТО организации"
            },
            "is_LPU":{
                "type": "integer",
                "id": "organization/is_LPU",
                "description": "Организация является ЛПУ. Если организация ЛПУ - передать 1. Если нет - 0"
            },
            "is_stationary":{
                "type": "integer",
                "id": "organization/is_stationary",
                "description": "Организация является стационаром. Если организация стационар - передать 1. Если нет - 0"
            },
            "is_insurer":{
                "type": "integer",
                "id": "organization/is_insurer",
                "description": "Организация является СМО. Если организация СМО - передать 1. Если нет - 0"
            }
        },
        "required": ["full_name", "short_name", "address", "area", "TFOMSCode", "is_LPU"]
    }]
