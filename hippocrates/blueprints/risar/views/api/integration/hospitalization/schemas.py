#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.views.api.integration.schemas import Schema


class HospitalizationSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "hospitalization",
            "description": "Госпитализация",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "hospitalization_id": {
                    "description": "ID госпистализации",
                    "type": "string"
                },
                "measure_id": {
                    "description": "ID мероприятия случая",
                    "type": "string"
                },
                "date_in": {
                    "description": "Дата поступленияя",
                    "type": "string",
                    "format": "date"
                },
                "date_out": {
                    "description": "Дата выписки",
                    "type": "string",
                    "format": "date"
                },
                "hospital": {
                    "description": "ЛПУ (код)",
                    "type": "string"
                },
                "doctor": {
                    "description": "Лечащий врач (код)",
                    "type": "string"
                },
                "pregnancy_week": {
                    "description": "Срок беременности при поступлении (недель)",
                    "type": "integer"
                },
                "diagnosis_in": {
                    "description": "Диагноз при поступлении",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "diagnosis_out": {
                    "description": "Диагноз при выписке",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                }
            }
        },
    ]
