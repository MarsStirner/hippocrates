#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class CheckupObsSecondSchema(Schema):
    """
    Схемы для проверки валидности данных повторного осмотра
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "secondcheckup",
            "description": "Повторный осмотр беременной акушером-гинекологом",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "dynamic_monitoring": {
                    "description": "Лист динамического наблюдения",
                    "type": "object",
                    "properties": {
                        "date": {
                            "description": "Дата осмотра",
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
                        "weight": {
                            "description": "Масса при осмотре",
                            "type": "number",
                            "format": "double"
                        },
                        "urina_comment": {
                            "description": "Комментарии к анализу мочи",
                            "type": "string"
                        },
                        "blood_comment": {
                            "description": "Комментарии к анализу крови",
                            "type": "string"
                        },
                        "ultrasound_comment": {
                            "description": "Комментарии к УЗИ",
                            "type": "string"
                        },
                        "other_analyzes_comment": {
                            "description": "Комментарии к другим анализам",
                            "type": "string"
                        }
                    },
                    "required": [
                        "date",
                        "hospital",
                        "doctor",
                        "ad_right_high",
                        "ad_left_high",
                        "ad_right_low",
                        "ad_left_low",
                        "weight"
                    ]
                },
                "somatic_status": {
                    "description": "Данные соматического статуса",
                    "type": "object",
                    "properties": {
                        "state": {
                            "description": "Общее состояние, справочник rbRisarState",
                            "type": "string"
                        },
                        "complaints": {
                            "description": "Жалобы, справочник rbRisarComplaints",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "skin": {
                            "description": "Кожа, справочник rbRisarSkin",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "lymph": {
                            "description": "Лимфоузлы, справочник rbRisarLymph",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "breast": {
                            "description": "Молочные железы, справочник rbRisarBreast",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "heart_tones": {
                            "description": "Тоны сердца, справочник rbRisarHeart_Tones",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "nipples": {
                            "description": "Состояние сосков, справочник rbRisarNipples",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "respiratory": {
                            "description": "Органы дыхания, справочник rbRisarBreathe",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "abdomen": {
                            "description": "Органы брюшной полости, справочник rbRisarStomach",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "liver": {
                            "description": "Печень, справочник rbRisarLiver",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "secretion": {
                            "description": "Выделения, справочник rbRisarSecretion",
                            "type": "string"
                        },
                        "edema": {
                            "description": "Отёки",
                            "type": "string"
                        },
                        "bowel_and_bladder_habits": {
                            "description": "Физиологические отправления, справочник rbRisarBowelAndBladderFunctions",
                            "type": "string"
                        }
                    },
                    "required": ["state", "complaints"]
                },
                "obstetric_status": {
                    "description": "Акушерский статус",
                    "type": "object",
                    "properties": {
                        "abdominal_circumference": {
                            "description": "Окружность живота",
                            "type": "number",
                            "format": "double"
                        },
                        "fundal_height": {
                            "description": "Высота стояния дна матки",
                            "type": "number",
                            "format": "double"
                        },
                        "uterus_state": {
                            "description": "Состояние матки, справочник rbRisarMetra_State",
                            "type": "string"
                        },
                        "first_fetal_movement": {
                            "description": "Первое шевеление плода (дата)",
                            "type": "string",
                            "format": "date"
                        },
                        "fetal_movements": {
                            "description": "Шевеление",
                            "type": "string"
                        }
                    }
                },
                "fetus": {
                    "description": "Плод",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "fetus_lie": {
                                "description": "Положение плода, справочник rbRisarFetus_Position",
                                "type": "string"
                            },
                            "fetus_position": {
                                "description": "Позиция плода, справочник rbRisarFetus_Position_2",
                                "type": "string"
                            },
                            "fetus_type": {
                                "description": "Вид плода, справочник rbRisarFetus_Type",
                                "type": "string"
                            },
                            "fetus_presentation": {
                                "description": "Предлежащая часть плода, справочник rbRisarPresenting_Part",
                                "type": "string"
                            },
                            "fetus_heartbeat": {
                                "description": "Сердцебиение плода, справочник rbRisarFetus_Heartbeat",
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "fetus_heart_rate": {
                                "description": "ЧСС плода",
                                "type": "number",
                                "format": "double"
                            },
                            "intrauterine_growth_retardation": {
                                "description": "Задержка в развитии плода, справочник rbRisarFetus_Delay",
                                "type": "string"
                            },
                            "ctg_data": {
                                "description": "Данные КТГ",
                                "type": "object",
                                "properties": {
                                    "fhr": {
                                        "description": "Базальный ритм, справочник rbRisarBasal",
                                        "type": "string"
                                    },
                                    "fhr_variability_amp": {
                                        "description": "Вариабельность (амплитуда), справочник rbRisarVariabilityRange",
                                        "type": "string"
                                    },
                                    "fhr_variability_freq": {
                                        "description": "Вариабельность (частота в минуту), справочник rbRisarFrequencyPerMinute",
                                        "type": "string"
                                    },
                                    "fhr_acceleration": {
                                        "description": "Акселерации за 30 минут, справочник rbRisarAcceleration",
                                        "type": "string"
                                    },
                                    "fhr_deceleration": {
                                        "description": "Децелерации за 30 минут, справочник rbRisarDeceleration",
                                        "type": "string"
                                    }
                                },
                                "required": ["fhr", "fhr_variability_amp", "fhr_variability_freq", "fhr_acceleration",
                                             "fhr_deceleration"]
                            }
                        }
                    }
                },
                "vaginal_examination": {
                    "description": "Влагалищное исследование",
                    "type": "object",
                    "properties": {
                        "vagina": {
                            "description": "Влагалище, справочник rbRisarVagina",
                            "type": "string"
                        },
                        "cervix": {
                            "description": "Шейка матки, справочник rbRisarCervix",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "cervix_length": {
                            "description": "Длина шейки матки, справочник rbRisarCervix_Length",
                            "type": "string"
                        },
                        "cervical_canal": {
                            "description": "Цервикальный канал, справочник rbRisarCervical_Canal",
                            "type": "string"
                        },
                        "cervix_consistency": {
                            "description": "Консистенция шейки матки, справочник rbRisarCervix_Consistency",
                            "type": "string"
                        },
                        "cervix_position": {
                            "description": "Позиция шейки матки, справочник rbRisarCervix_Position",
                            "type": "string"
                        },
                        "cervix_maturity": {
                            "description": "Зрелость шейки матки, справочник rbRisarCervix_Maturity",
                            "type": "string"
                        },
                        "body_of_uterus": {
                            "description": "Тело матки, справочник rbRisarBody_Of_Womb",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "adnexa_right": {
                            "description": "Придатки, справочник rbRisarAppendages",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "adnexa_left": {
                            "description": "Придатки, справочник rbRisarAppendages",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "specialities": {
                            "description": "Особенности",
                            "type": "string"
                        },
                        "vulva": {
                            "description": "Наружные половые органы",
                            "type": "string"
                        },
                        "parametrium": {
                            "description": "Околоматочное пространство, справочник rbRisarParametrium",
                            "type": "string"
                        },
                        "vaginal_smear": {
                            "description": "Отделяемое из влагалища взято на анализ",
                            "type": "boolean"
                        },
                        "cervical_canal_smear": {
                            "description": "Отделяемое из цервикального канала взято на анализ",
                            "type": "boolean"
                        },
                        "onco_smear": {
                            "description": "Мазок на онкоцитологию взято на анализ",
                            "type": "boolean"
                        },
                        "urethra_smear": {
                            "description": "Отделяемое и при наличии данных з уретры взято на анализ",
                            "type": "boolean"
                        }
                    }
                },
                "medical_report": {
                    "description": "Заключение",
                    "type": "object",
                    "properties": {
                        "pregnancy_week": {
                            "description": "Беременность (недель)",
                            "type": "integer"
                        },
                        "next_visit_date": {
                            "description": "Плановая дата следующей явки",
                            "type": "string",
                            "format": "date"
                        },
                        "pregnancy_continuation": {
                            "description": "Возможность сохранения беременности",
                            "type": "boolean"
                        },
                        "abortion_refusal": {
                            "description": "Отказ от прерывания",
                            "type": "boolean"
                        },
                        "working_conditions": {
                            "description": "Изменение условий труда, справочник rbRisarCraft",
                            "type": "string"
                        },
                        "diagnosis_osn": {
                            "description": "Основной диагноз, код диагноза по МКБ-10",
                            "type": "object",
                            "properties": {
                                "MKB": {
                                    "type": "string",
                                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                                },
                                "descr": {
                                    "type": "string"
                                }
                            },
                            "required": ["MKB"]
                        },
                        "diagnosis_sop": {
                            "description": "Диагноз сопутствующий (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "MKB": {
                                        "type": "string",
                                        "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                                    },
                                    "descr": {
                                        "type": "string"
                                    }
                                },
                                "required": ["MKB"]
                            },
                            "minItems": 0
                        },
                        "diagnosis_osl": {
                            "description": "Диагноз осложнения (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "MKB": {
                                        "type": "string",
                                        "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                                    },
                                    "descr": {
                                        "type": "string"
                                    }
                                },
                                "required": ["MKB"]
                            },
                            "minItems": 0
                        },
                        "recommendations": {
                            "description": "Рекомендации",
                            "type": "string"
                        },
                        "notes": {
                            "description": "Примечания",
                            "type": "string"
                        },
                        "vitaminization": {
                            "description": "Витаминизация",
                            "type": "string"
                        },
                        "nutrition": {
                            "description": "Коррекция питания",
                            "type": "string"
                        },
                        "treatment": {
                            "description": "Лечение",
                            "type": "string"
                        }
                    },
                    "required": [
                        "pregnancy_week",
                        "next_visit_date",
                        "pregnancy_continuation",
                        "diagnosis_osn"
                    ]
                }
            },
            "required": ["external_id", "dynamic_monitoring", "obstetric_status", "medical_report"]
        }
    ]
