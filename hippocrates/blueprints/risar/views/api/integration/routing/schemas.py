#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class RoutingSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "routing",
            "description": "Список ЛПУ родоразрешения",
            "type": "object",
            "properties": {
                "hospital_planned": {
                    "description": "Выбранное плановое ЛПУ (код ЛПУ)",
                    "type": "string"
                },
                "hospital_emergency": {
                    "description": "Выбранное экстренное ЛПУ (код ЛПУ)",
                    "type": "string"
                },
                "hospital_planned_list": {
                    "description": "Список ЛПУ планового родоразрешения (код ЛПУ)",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 0
                },
                "hospital_emergency_list": {
                    "description": "Список ЛПУ экстренного родоразрешения (код ЛПУ)",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 0
                },
                "hospital_emergency_list_district": {
                    "description": "Список ЛПУ экстренного родоразрешения в районе проживания пациентки (код ЛПУ)",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 0
                }
            }
        },
    ]
