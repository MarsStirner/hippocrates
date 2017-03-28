# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class DoctorSchema(Schema):
    """
    Схемы для проверки валидности данных врача (пользователя)
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "object",
        "id": "doctor",
        "properties": {
            "last_name": {
                "type": "string",
                "id": "doctor/last_name",
                "description": "Фамилия врача"
            },
            "first_name": {
                "type": "string",
                "id": "doctor/first_name",
                "description": "Имя врача"
            },
            "patr_name": {
                "type": "string",
                "id": "doctor/patr_name",
                "description": "Отчество врача"
            },
            "sex": {
                "type": "integer",
                "id": "doctor/sex",
                "description": "Пол пациента: 0 - Пол не указан, 1 - Мужской, 2 - Женский"
            },
            "birth_date": {
                "type": "string",
                "id": "doctor/birth_date",
                "description": "Дата рождения"
            },
            "SNILS": {
                "type": "string",
                "id": "doctor/SNILS",
                "description": "СНИЛС врача"
            },
            "INN": {
                "type": "string",
                "id": "doctor/INN",
                "description": "ИНН врача"
            },
            "organization": {
                "type": "string",
                "id": "doctor/organization",
                "description": "Идентификатор ЛПУ врача"
            },
            "department": {
                "type": "string",
                "description": "Идентификатор подразделения ЛПУ врача"
            },
            "speciality": {
                "type": "string",
                "id": "doctor/speciality",
                "description": "код специальности врача, справоник rbSpeciality"
            },
            "post": {
                "type": "string",
                "id": "doctor/post",
                "description": "код должности врача, справочник rbPost"
            },
            "login": {
                "type": "string",
                "id": "doctor/login",
                "description": "Логин врача"
            },
            "regional_code": {
                "type": "string",
                "id": "doctor/regional_code",
                "description": "Региональный код врача"
            }
        },
        "required": ["last_name", "first_name", "sex", "SNILS", "organization", "speciality", "post", "regional_code"]
    }]
