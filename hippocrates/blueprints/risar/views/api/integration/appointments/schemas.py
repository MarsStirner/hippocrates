# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class AppointmentListSchema(Schema):
    """
    Схемы для проверки валидности данных списка направлений
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Appointment_list",
        "description": "Список направлений",
        "type": "array",
        "items": {
            "description": "id направления",
            "type": "string"
        },
        "minItems": 0
    }]


class AppointmentSchema(Schema):
    """
    Схемы для проверки валидности данных направления
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Appointment",
        "description": "Направление",
        "type": "object",
        "properties": {
            "measure_code": {
                "description": "Код мероприятия, справочник Measure",
                "type": "string"
            },
            "diagnosis": {
                "description": "Направительный диагноз",
                "type": "string",
                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
            },
            "time": {
                "description": "Время забора материала",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "date": {
                "description": "Дата забора материала",
                "type": "string",
                "format": "date"
            },
            "parameters": {
                "description": "Параметры (список)",
                "type": "string"
            },
            "referral_lpu": {
                "description": "Направлен в (код ЛПУ)",
                "type": "string"
            },
            "referral_date": {
                "description": "Дата направления",
                "type": "string",
                "format": "date"
            },
            "comment": {
                "description": "Комментарий",
                "type": "string"
            }
        }
    }]
