#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class SpecialistsCheckupSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "type": "object",
            "$schema": "http://json-schema.org/draft-04/schema",
            "id": "specialists_checkup",
            "properties": {
                "result_action_id": {
                    "type": "string",
                    "id": "research/result_action_id",
                    "description": "ID Action с результатами мероприятия"
                },
                "external_id": {
                    "type": "string",
                    "id": "specialists_checkup/external_id",
                    "description": "Внешний ID"
                },
                "measure_id": {
                    "type": "string",
                    "id": "specialists_checkup/measure_id",
                    "description": "ID мероприятия случая"
                },
                "measure_type_code": {
                    "type": "string",
                    "id": "specialists_checkup/measure_type_code",
                    "description": "Код мероприятия. Передается для идентификации типа соответствующего мероприятия"
                },
                "checkup_date": {
                    "type": "string",
                    "id": "specialists_checkup/checkup_date",
                    "description": "Дата осмотра"
                },
                "lpu_code": {
                    "type": "string",
                    "id": "specialists_checkup/lpu_code",
                    "description": "Код ЛПУ проведения осмотра. Код по классификатору Ф003"
                },
                "doctor_code": {
                    "type": "string",
                    "id": "specialists_checkup/doctor_code",
                    "description": "Врач, проводивший осмотр. Код из реестра сотрудников ЛПУ"
                },
                "diagnosis": {
                    "type": "string",
                    "id": "specialists_checkup/diagnosis",
                    "description": "Диагноз в формате кода МКБ"
                },
                "status": {
                    "description": "Статус мероприятия, справочник rbMeasureStatus",
                    "type": "string"
                }
            },
            "required": [
                "measure_type_code",
                "checkup_date",
                "doctor_code",
                "lpu_code"
            ]
        },
    ]
