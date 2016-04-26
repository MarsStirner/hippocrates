#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.views.api.integration.schemas import Schema


class ErrandsSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "errand",
            "description": "Поручение",
            "type": "object",
            "properties": {
                "execution_date": {
                    "description": "Фактическая дата исполнения",
                    "type": "string",
                    "format": "date"
                },
                "execution_comment": {
                    "description": "Текст ответа на поручение",
                    "type": "string"
                }
            }
        },
    ]

    schema_output = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "errands_list",
            "description": "Список поручений",
            "type": "array",
            "items": {
                "description": "Поручение",
                "type": "object",
                "properties": {
                    "errand_id": {
                        "description": "id поручения",
                        "type": "string"
                    },
                    "hospital": {
                        "description": "ЛПУ (код ЛПУ)",
                        "type": "string"
                    },
                    "doctor": {
                        "description": "Врач автор поручения (код врача)",
                        "type": "string"
                    },
                    "date": {
                        "description": "Плановая дата выполнения",
                        "type": "string",
                        "format": "date"
                    },
                    "comment": {
                        "description": "Текст поручения",
                        "type": "string"
                    },
                    "execution_hospital": {
                        "description": "ЛПУ исполнения (код ЛПУ)",
                        "type": "string"
                    },
                    "execution_doctor": {
                        "description": "врач исполнитель (код врача)",
                        "type": "string"
                    },
                    "execution_date": {
                        "description": "Плановая дата выполнения",
                        "type": "string",
                        "format": "date"
                    },
                    "execution_comment": {
                        "description": "Текст поручения",
                        "type": "string"
                    }
                }
            },
            "minItems": 0
        },
    ]
