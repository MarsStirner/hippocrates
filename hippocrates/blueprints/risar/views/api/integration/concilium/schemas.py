# -*- coding: utf-8 -*-
from blueprints.risar.views.api.integration.schemas import Schema


class ConciliumSchema(Schema):
    """
    Схемы для проверки валидности данных консилиума
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "concilium",
        "description": "Консилиум",
        "type": "object",
        "properties": {
            "concilium_id": {
                "description": "Внутренний ID",
                "type": "string"
            },
            "external_id": {
                "description": "Внешний ID",
                "type": "string"
            },
            "date": {
                "description": "Дата консилиума",
                "type": "string",
                "format": "date"
            },
            "hospital": {
                "description": "ЛПУ консилиума (код)",
                "type": "string"
            },
            "doctor": {
                "description": "Врач (код)",
                "type": "string"
            },
            "doctors":{
                "description": "Состав консилиума (коды врачей)",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "doctor":{
                            "description": "Участник консилиума (код врача)",
                            "type": "string"
                        },
                        "opinion":{
                            "description": "Особое мнение участника консилиума (если есть)",
                            "type": "string"
                        }
                    },
                    "required": ["doctor"]
                },
                "minItems": 3
            },
            "patient_presence": {
                "description": "Присутствие пациента на консилиуме",
                "type": "boolean"
            },
            "diagnosis": {
                "description": "Основной диагноз, код диагноза по МКБ-10",
                "type": "string",
                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
            },
            "reason": {
                "description": "Причина проведения консилиума",
                "type": "string"
            },
            "patient_condition": {
                "description": "Состояние пациента",
                "type": "string"
            },
            "decision": {
                "description": "Заключение консилиума",
                "type": "string"
            }
        },
        "required": ["external_id", "date", "hospital", "doctor", "doctors", "diagnosis", "reason", "decision"]
    }]
