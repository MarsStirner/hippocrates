# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class MeasureListSchema(Schema):
    """
    Схемы для проверки валидности данных списка
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "measure_list",
        "description": "Список мероприятий случая",
        "type": "array",
        "items": {
            "description": "Мероприятие случая",
            "type": "object",
            "properties": {
                "measure_id": {
                    "description": "ID мероприятия случая",
                    "type": "string"
                },
                "measure_type_code": {
                    "description": "Код мероприятия, справочник Measure",
                    "type": "string"
                },
                "begin_datetime": {
                    "description": "Дата-время начала интервала действия мероприятия",
                    "type": "string",
                    "format": "date"
                },
                "end_datetime": {
                    "description": "Дата-время конца интервала действия мероприятия",
                    "type": "string",
                    "format": "date"
                },
                "status": {
                    "description": "Статус мероприятия, справочник rbMeasureStatus",
                    "type": "string"
                },
                "result_action_id": {
                    "description": "Результаты мероприятия, ссылка на {Action}",
                    "type": "string"
                },
                "indications": {
                    "description": "Показания к госпитализации",
                    "type": "string"
                }
            },
            "required": ["measure_id", "measure_type_code", "begin_datetime", "end_datetime", "status"]
        },
        "minItems": 0
    }]
