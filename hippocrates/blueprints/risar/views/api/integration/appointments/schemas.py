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
            "execution_time": {
                "description": "Время забора материала",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "parameters": {
                "description": "Параметры (список)",
                "type": "string"
            },
            "appointed_lpu":{
                "type": "string",
                "description": "Код ЛПУ в котором было назначено мероприятие"
            },
            "appointed_doctor":{
                "type": "string",
                "description": "Код врача, назначившего мероприятие"
            },
            "referral_lpu": {
                "description": "Направлен в (код ЛПУ)",
                "type": "string"
            },
            "referral_department": {
                "description": "Код подразделения",
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
            },
            "appointment_code": {
                "description": "Код направления",
                "type": "string"
            },
            "appointed_date": {
                "description": "Дата назначения",
                "type": "string",
                "format": "date"
            },
            "hospitalization_form": {
                "description": "Код формы госпитализации, справочник rbHosp_form_regional",
                "type": "string"
            },
            "operation": {
                "description": "Код справочника требуется ли операция, справочник rb_operationNeed_regional",
                "type": "string"
            },
            "profile": {
                "description": "Код профиля, справочник rbProfMedHelp",
                "type": "string"
            }
        }
    }]
