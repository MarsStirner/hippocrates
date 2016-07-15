#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class CheckupPuerperaSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "puerperacheckup",
            "description": "Осмотр родильницы акушером-гинекологом",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "exam_puerpera_id": {
                    "description": "ID осмотра",
                    "type": "string"
                },
                "date": {
                    "description": "Дата осмотра",
                    "type": "string",
                    "format": "date"
                },
                "date_of_childbirth": {
                    "description": "Дата родов",
                    "type": "string",
                    "format": "date"
                },
                "hospital": {
                    "description": "ЛПУ осмотра (код)",
                    "type": "string"
                },
                "doctor": {
                    "description": "Врач (код)",
                    "type": "string"
                },
                "time_since_childbirth": {
                    "description": "Срок после родов, недель",
                    "type": "integer"
                },
                "complaints": {
                    "description": "Жалобы, справочник rbRisarComplaints_Puerpera",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(0[1-5])$"
                    }
                },
                "nipples": {
                    "description": "Состояние сосков, справочник rbRisarNipples_Puerpera",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(01|02)$"
                    }
                },
                "secretion": {
                    "description": "Выделения, справочник rbRisarSecretion_Puerpera",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(0[1-3])$"
                    }
                },
                "breast": {
                    "description": "Состоние молочных желез, справочник rbRisarBreast_Puerpera",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^(0[1-5])$"
                    }
                },
                "lactation": {
                    "description": "Лактация, справочник rbRisarLactation_Puerpera",
                    "type": "string",
                    "pattern": "^(01|02)$"
                },
                "uterus": {
                    "description": "Состояние матки, справочник rbRisarUterus_Puerpera",
                    "type": "string",
                    "pattern": "^(0[1-5])$"
                },
                "scar": {
                    "description": "Состояние послеоперационного рубца, справочник rbRisarScar_Puerpera",
                    "type": "string",
                    "pattern": "^(01|02)$"
                },
                "state": {
                    "description": "Общее состояние, справочник rbRisarState",
                    "type": "string",
                    # "enum": ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
                },
                "ad_right_high": {
                    "description": "AD правая рука верхн.",
                    "type": "number",
                    "format": "double"
                },
                "ad_left_high": {
                    "description": "AD левая рука верхн.",
                    "type": "number",
                    "format": "double"
                },
                "ad_right_low": {
                    "description": "AD правая рука ниж.",
                    "type": "number",
                    "format": "double"
                },
                "ad_left_low": {
                    "description": "AD левая рука ниж.",
                    "type": "number",
                    "format": "double"
                },
                "veins": {
                    "description": "Состояние вен, справочник rbRisarVein",
                    "type": "string",
                    # "enum": ["noma", "poverhnostnyjvarikoz", "varikoznoerassirenieven"]
                },
                "diagnosis": {
                    "description": "Основной диагноз, код диагноза по МКБ-10",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "contraception_recommendations": {
                    "description": "Рекомендации по контрацепции, справочник rbRisarContraception_Puerpera",
                    "type": "string",
                    "pattern": "^(0[1-4])$"
                },
                "treatment": {
                    "description": "Лечение",
                    "type": "string"
                },
                "recommendations": {
                    "description": "Рекомендации",
                    "type": "string"
                }
            },
            "required": [
                "external_id",
                "date",
                "date_of_childbirth",
                "hospital",
                "doctor",
                "diagnosis"
            ]
        },
    ]
