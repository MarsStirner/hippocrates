#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class EpicrisisSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "epicrisis",
            "description": "эпикриз",
            "type": "object",
            "properties": {
                "epicrisis": {
                    "description": "Эпикриз",
                    "type": "object",
                    "properties": {
                        "hospital": {
                            "description": "ЛПУ эпикриза (код)",
                            "type": "string"
                        },
                        "hospital_chief_doctor": {
                            "description": "Заведующая ЖК (код)",
                            "type": "string"
                        },
                        "hospital_doctor": {
                            "description": "Лечащий врач (код)",
                            "type": "string"
                        },
                        "date_close": {
                            "description": "Дата закрытия случая",
                            "type": "string",
                            "format": "date"
                        }
                    }
                }
            }
        },
    ]
