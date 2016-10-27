# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class AnamnesisGynSchema(Schema):
    """
    Схемы для проверки валидности данных анамнеза карты небеременной
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "gynecological_anamnesis",
        "description": "Гинекологический анамнез",
        "type": "object",
        "properties": {
            "age": {
                "description": "Менструальная функция. С возраста",
                "type": "integer"
            },
            "duration": {
                "description": "Менструальная функция. Длительность",
                "type": "string"
            },
            "period_duration": {
                "description": "Менструальная функция. Продолжительность цикла",
                "type": "string"
            },
            "disorder": {
                "description": "Менструальная функция. Нарушения",
                "type": "boolean"
            },
            "menstrual_character": {
                "description": "Менструальная функция. Характер менструаций, массив, справочник rbRisarMenstruationCharacter",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "intermenstrual_spotting": {
                "description": "Менструальная функция. Межменструальные выделения",
                "type": "string"
            },
            "menstrual_pain": {
                "description": "Менструальная функция. Менструальные боли",
                "type": "string"
            },
            "menopause": {
                "description": "Менопауза. Наличие",
                "type": "boolean"
            },
            "menopause_age": {
                "description": "Менопауза.С возраста",
                "type": "integer"
            },
            "sex_life_age": {
                "description": "Половая жизнь. С возраста",
                "type": "integer"
            },
            "intercourse_partner_number": {
                "description": "Половая жизнь. Количество половых партнеров",
                "type": "integer"
            },
            "marital_status": {
                "description": "Семейное положение, справочник rbRisarMarital_Status",
                "type": "string"
            },
            "std": {
                "description": "ЗППП, массив, справочник rbRisarSTD",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "gynecopathy": {
                "description": "Гинекологические заболевания, массив, справочник rbRisarGynecopathy",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "hepatitis": {
                "description": "Гепатит",
                "type": "string"
            },
            "tuberculosis": {
                "description": "Туберкулез",
                "type": "string"
            },
            "somatic_disease": {
                "description": "Соматические заболевания",
                "type": "string"
            },
            "hereditary": {
                "description": "Наследственность, массив, справочник rbRisarHereditary",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "gyn_operation": {
                "description": "Оперативные вмешательства на половых органах",
                "type": "string"
            },
            "infertility": {
                "description": "Бесплодие. Наличие",
                "type": "boolean"
            },
            "infertility_kind": {
                "description": "Бесплодие. Вид, справочник rbRisarInfertilityKind",
                "type": "string"
            },
            "infertility_duration": {
                "description": "Бесплодие. Длительность",
                "type": "number"
            },
            "infertility_etiology": {
                "description": "Бесплодие. Причины, массив, справочник rbRisarInfertilityEtiology",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "infertility_treatment": {
                "description": "Бесплодие. Лечение, массив, справочник rbRisarInfertilityTreatment",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "traumas": {
                "description": "Травмы",
                "type": "string"
            },
            "operations": {
                "description": "Операции (кроме гинекологических)",
                "type": "string"
            },
            "alcohol": {
                "description": "Алкоголь",
                "type": "boolean"
            },
            "smoking": {
                "description": "Курение",
                "type": "boolean"
            },
            "drugs": {
                "description": "Наркотики",
                "type": "boolean"
            },
            "toxic": {
                "description": "Токсичные вещества",
                "type": "boolean"
            },
            "work_group": {
                "description": "Общественно-профилактическая группа, справочник rbRisarWork_Group",
                "type": "string"
            },
            "professional_properties": {
                "description": "Профессиональные вредности, справочник rbRisarProfessional_Properties",
                "type": "string"
            },
            "additional_info": {
                "description": "Дополнительная информация",
                "type": "string"
            },
            "epidemic": {
                "description": "Эпидемиологический анамнез",
                "type": "string"
            }
        }
    }]