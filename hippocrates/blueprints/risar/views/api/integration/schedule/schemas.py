# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class ScheduleSchema(Schema):
    """
    Схемы для проверки валидности данных расписания специалиста
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule",
        "description": "Расписание",
        "type": "array",
        "items": {
            "description": "День",
            "type": "object",
            "properties": {
                "date": {
                    "description": "Дата",
                    "type": "string",
                    "format": "date"
                },
                "intervals": {
                    "description": "Рабочие промежутки",
                    "type": "array",
                    "items": {
                        "description": "Рабочий промежуток",
                        "type": "object",
                        "properties": {
                            "begin_time": {
                                "description": "Время начала промежутка",
                                "type": "string",
                                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                            },
                            "end_time": {
                                "description": "Время завершения промежутка",
                                "type": "string",
                                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                            },
                            "quantity": {
                                "description": "Запланированное колиечство пациентов в интервале",
                                "type": "integer"
                            }
                        }
                    }
                }
            }
        },
        "minItems": 0
    }]


class Schedule2Schema(Schema):
    """
    Схемы для проверки валидности данных расписания специалиста2
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule",
        "description": "Расписание",
        "type": "array",
        "items": {
            "description": "День",
            "type": "object",
            "properties": {
                "date": {
                    "description": "Дата",
                    "type": "string",
                    "format": "date"
                },
                "intervals": {
                    "description": "Рабочие промежутки",
                    "type": "array",
                    "items": {
                        "description": "Рабочий промежуток",
                        "type": "object",
                        "properties": {
                            "begin_time": {
                                "description": "Время начала промежутка",
                                "type": "string",
                                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                            },
                            "end_time": {
                                "description": "Время завершения промежутка",
                                "type": "string",
                                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                            }
                        }
                    }
                }
            }
        },
        "minItems": 0
    }]
