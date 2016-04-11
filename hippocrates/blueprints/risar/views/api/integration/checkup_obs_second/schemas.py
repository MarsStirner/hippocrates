#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""


class CheckupObsSecondSchema(object):
    """
    Схемы для проверки валидности данных первичного осмотра
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
                "exam_obs_id": {
                    "description": "ID первичного осмотра",
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
                            "type": "string",
                            # "enum": ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
                        },
                        "complaints": {
                            "description": "Жалобы, справочник rbRisarComplaints",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "epigastrii",
                                #     "golovnaabol_",
                                #     "moving",
                                #     "net",
                                #     "oteki",
                                #     "rvota",
                                #     "tosnota",
                                #     "zrenie"
                                # ]
                            }
                        },
                        "skin": {
                            "description": "Кожа, справочник rbRisarSkin",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "naliciekrovoizlianij",
                                #     "naliciesypi",
                                #     "obycnojokraskiivlajnosticistaa",
                                #     "povysennojvlajnosti",
                                #     "suhaa"
                                # ]
                            }
                        },
                        "lymph": {
                            "description": "Лимфоузлы, справочник rbRisarLymph",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "boleznennye",
                                #     "neboleznennye",
                                #     "nepal_piruutsa",
                                #     "neuvelicennye",
                                #     "pal_piruutsa",
                                #     "uvelicennye"
                                # ]
                            }
                        },
                        "breast": {
                            "description": "Молочные железы, справочник rbRisarBreast",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "bezpatologiceskihizmenenij",
                                #     "mestnoeuplotnenie",
                                #     "nagrubanie",
                                #     "pokrasnenie",
                                #     "tresinysoskov"
                                # ]
                            }
                        },
                        "heart_tones": {
                            "description": "Тоны сердца, справочник rbRisarHeart_Tones",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "akzentIItona",
                                #     "aritmicnye",
                                #     "asnye",
                                #     "gluhie",
                                #     "prigluseny",
                                #     "proslusivautsa",
                                #     "ritmicnye"
                                # ]
                            }
                        },
                        "nipples": {
                            "description": "Состояние сосков, справочник rbRisarNipples",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "norma",
                                #     "tresiny",
                                #     "vospalenie"
                                # ]
                            }
                        },
                        "respiratory": {
                            "description": "Органы дыхания, справочник rbRisarBreathe",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "dyhaniejestkoe",
                                #     "dyhanievezikularnoe",
                                #     "hripyotsutstvuut",
                                #     "hripysuhie",
                                #     "hripyvlajnye"
                                # ]
                            }
                        },
                        "abdomen": {
                            "description": "Органы брюшной полости, справочник rbRisarStomach",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": [
                                #     "jivotmagkijbezboleznennyj",
                                #     "jivotnaprajennyj",
                                #     "jivotuvelicenzascetberemennojmatki"
                                # ]
                            }
                        },
                        "liver": {
                            "description": "Печень, справочник rbRisarLiver",
                            "type": "array",
                            "items": {
                                "type": "string",
                                # "enum": ["nepal_piruetsa", "uvelicena"]
                            }
                        },
                        "secretion": {
                            "description": "Выделения, справочник rbRisarSecretion",
                            "type": "string",
                            # "enum": [
                            #     "slizistye",
                            #     "sukrovicnye",
                            #     "tvorojistye"
                            # ]
                        },
                        "edema": {
                            "description": "Отёки",
                            "type": "string"
                        },
                        "bowel_and_bladder_habits": {
                            "description": "Физиологические отправления",
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
                            "type": "string",
                            # "enum": ["gipertonus", "normal_nyjtonus"]
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
                                "type": "string",
                                # "enum": ["kosoe", "poperecnoe", "prodol_noe"]
                            },
                            "fetus_position": {
                                "description": "Позиция плода, справочник rbRisarFetus_Position_2",
                                "type": "string",
                                # "enum": ["pervaa", "vtoraa"]
                            },
                            "fetus_type": {
                                "description": "Вид плода, справочник rbRisarFetus_Type",
                                "type": "string",
                                # "enum": ["perednij", "zadnij"]
                            },
                            "fetus_presentation": {
                                "description": "Предлежащая часть плода, справочник rbRisarPresenting_Part",
                                "type": "string",
                                # "enum": [
                                #     "cistoagodicnoepredlejanie",
                                #     "golovnoepredlejanie",
                                #     "lizevoepredlejanie",
                                #     "lobnoepredlejanie",
                                #     "nojnoepredlejanie",
                                #     "perednegolovnoepredlejanie",
                                #     "smesannoeagodicnoepredlejanie",
                                #     "tazovoepredlejanie",
                                #     "zatylocnoepredlejanie"
                                # ]
                            },
                            "fetus_heartbeat": {
                                "description": "Сердцебиение плода, справочник rbRisarFetus_Heartbeat",
                                "type": "string",
                                # "type": "array",
                                # "items": {
                                #     "type": "string",
                                #     # "enum": ["asnoe", "ritmicnoe"]
                                # }
                            },
                            "fetus_heart_rate": {
                                "description": "ЧСС плода",
                                "type": "number",
                                "format": "double"
                            },
                            "intrauterine_growth_retardation": {
                                "description": "Задержка в развитии плода, справочник rbRisarFetus_Delay",
                                "type": "string",
                                # "enum": [
                                #     "1-2nedeli",
                                #     "4_and_more",
                                #     ">3nedel_",
                                #     "otsutstvuet"
                                # ]
                            },
                            "ctg_data": {
                                "description": "Данные КТГ",
                                "type": "object",
                                "properties": {
                                    "fhr": {
                                        "description": "Базальный ритм, справочник rbRisarBasal",
                                        "type": "string",
                                        "pattern": "^(0[1-4])$"
                                    },
                                    "fhr_variability_amp": {
                                        "description": "Вариабельность (амплитуда), справочник rbRisarVariabilityRange",
                                        "type": "string",
                                        "pattern": "^(0[1-3])$"
                                    },
                                    "fhr_variability_freq": {
                                        "description": "Вариабельность (частота в минуту), справочник rbRisarFrequencyPerMinute",
                                        "type": "string",
                                        "pattern": "^(0[1-3])$"
                                    },
                                    "fhr_acceleration": {
                                        "description": "Акселерации за 30 минут, справочник rbRisarAcceleration",
                                        "type": "string",
                                        "pattern": "^(0[1-3])$"
                                    },
                                    "fhr_deceleration": {
                                        "description": "Децелерации за 30 минут, справочник rbRisarDeceleration",
                                        "type": "string",
                                        "pattern": "^(0[1-3])$"
                                    }
                                },
                                "required": ["fhr", "fhr_variability_amp", "fhr_variability_freq", "fhr_acceleration", "fhr_deceleration"]
                            }
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
                        # "working_conditions": {
                        #     "description": "Изменение условий труда, справочник rbRisarCraft",
                        #     "type": "string",
                        #     # "enum": ["osvobojdenieotnocnyhsmen", "vsmenerabotynenujdaetsa"]
                        # },
                        "diagnosis_osn": {
                            "description": "Основной диагноз, код диагноза по МКБ-10",
                            "type": "string",
                            "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                        },
                        "diagnosis_sop": {
                            "description": "Диагноз сопутствующий (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            },
                            "minItems": 0
                        },
                        "diagnosis_osl": {
                            "description": "Диагноз осложнения (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
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
                        "vitaminization":{
                            "description": "Витаминизация",
                            "type": "string"
                        },
                        "nutrition":{
                            "description": "Коррекция питания",
                            "type": "string"
                        },
                        "treatment":{
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
        },
    ]
