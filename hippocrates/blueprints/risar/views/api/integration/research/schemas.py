#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.views.api.integration.schemas import Schema


class ResearchSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema",
            "type": "object",
            "id": "research",
            "properties": {
                "result_action_id": {
                    "type": "string",
                    "id": "research/result_action_id",
                    "description": "ID Action с результатами мероприятия"
                },
                "external_id": {
                    "type": "string",
                    "id": "research/external_id",
                    "description": "Внешний ID"
                },
                "measure_id": {
                    "type": "string",
                    "id": "research/measure_id",
                    "description": "ID мероприятия случая"
                },
                "measure_type_code": {
                    "type": "string",
                    "id": "research/measure_type_code",
                    "description": "Код мероприятия. Передается для идентификации типа соответствующего мероприятия"
                },
                "realization_date": {
                    "type": "string",
                    "id": "research/realization_date",
                    "description": "Дата выполнения исследования"
                },
                "lpu_code": {
                    "type": "string",
                    "id": "research/lpu_code",
                    "description": "Код ЛПУ проведения исследования. Код по классификатору Ф003"
                },
                "analysis_number": {
                    "type": "string",
                    "id": "research/analysis_number",
                    "description": "Номер анализа"
                },
                "results": {
                    "type": "string",
                    "id": "research/results",
                    "description": "Результаты исследования. Передавать в формате: параметр: значение; параметр: значение"
                },
                "comment": {
                    "type": "string",
                    "id": "research/comment",
                    "description": "Комментарий к исследованию"
                },
                "doctor_code": {
                    "type": "string",
                    "id": "research/doctor_code",
                    "description": "Врач, проводивший исследование. Код из реестра сотрудников ЛПУ"
                },
                "status": {
                    "description": "Статус мероприятия, справочник rbMeasureStatus",
                    "type": "string"
                }
            },
            "required": [
                "measure_type_code",
                "realization_date",
                "results"
            ]
        },
    ]
