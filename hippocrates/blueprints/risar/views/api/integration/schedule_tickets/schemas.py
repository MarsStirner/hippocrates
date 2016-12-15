# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class ScheduleTicketsSchema(Schema):
    """
    Схемы для проверки валидности данных записей на прием пациента
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule_tickets",
        "description": "Список записей на прием",
        "type": "array",
        "items": {
            "description": "Запись на прием",
            "type": "object",
            "properties": {
                "schedule_ticket_id": {
                    "description": "id записи на прием",
                    "type": "string"
                },
                "schedule_id": {
                    "description": "id расписания",
                    "type": "string"
                },
                "hospital": {
                    "description": "ЛПУ (код ЛПУ)",
                    "type": "string"
                },
                "doctor": {
                    "description": "Врач (код врача)",
                    "type": "string"
                },
                "patient": {
                    "description": "Пациент (id пациента)",
                    "type": "string"
                },
                "date": {
                    "description": "Дата приема",
                    "type": "string",
                    "format": "date"
                },
                "time_begin": {
                    "description": "Время приема",
                    "type": "string",
                    "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                },
                "time_end": {
                    "description": "Время приема",
                    "type": "string",
                    "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                }
            },
            "required": ["schedule_ticket_id","hospital","doctor","patient","date","time_begin","time_end"]
        },
        "minItems": 0
    }]


class ScheduleTicketSchema(Schema):
    """
    Схемы для проверки валидности данных записи на прием пациента
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule_tickets",
        "description": "Запись на прием",
        "type": "object",
        "properties": {
            "schedule_ticket_id": {
                "description": "id записи на прием",
                "type": "string"
            },
            "hospital": {
                "description": "ЛПУ (код ЛПУ)",
                "type": "string"
            },
            "doctor": {
                "description": "Врач (код врача)",
                "type": "string"
            },
            "patient": {
                "description": "Пациент (id пациента)",
                "type": "string"
            },
            "date": {
                "description": "Дата приема",
                "type": "string",
                "format": "date"
            },
            "time_begin": {
                "description": "Время приема",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "time_end": {
                "description": "Время приема",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            }
        },
        "required": ["hospital","doctor","patient","date","time_begin","time_end"]
    }]
