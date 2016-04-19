#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.views.api.integration.schemas import Schema


class ChildbirthSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "childbirth",
            "description": "2-3 часть обменной карты (данные родоразрешения)",
            "type": "object",
            "properties": {
                "general_info": {
                    "description": "Общая информация",
                    "type": "object",
                    "properties": {
                        "admission_date": {
                            "description": "Дата поступления",
                            "type": "string",
                            "format": "date"
                        },
                        "pregnancy_duration": {
                            "description": "Срок родоразрешения",
                            "type": "integer",
                            "maximum": 50
                        },
                        "delivery_date": {
                            "description": "Дата родоразрешения",
                            "type": "string",
                            "format": "date"
                        },
                        "delivery_time": {
                            "description": "Время родоразрешения",
                            "type": "string",
                            "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                        },
                        "maternity_hospital": {
                            "description": "ЛПУ, принимавшее роды (код)",
                            "type": "string"
                        },
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
                        "pregnancy_speciality": {
                            "description": "Особенности течения беременности",
                            "type": "string"
                        },
                        "postnatal_speciality": {
                            "description": "Особенности течения послеродового периода",
                            "type": "string"
                        },
                        "help": {
                            "description": "Оказанная помощь",
                            "type": "string"
                        },
                        "pregnancy_final": {
                            "description": "Исход беременности, справочник rbRisarPregnancy_Final",
                            "type": "string",
                            # "enum": ["abortom", "rodami"]
                        },
                        "abortion": {
                            "description": "Вид аборта, справочник rbRisarAbort",
                            "type": "string",
                            # "enum": [
                            #     "'abortmedikamentoznymmetodom-posostoaniurebenka",
                            #     "abortmedikamentoznymmetodom-posostoaniujensiny",
                            #     "drugievidypreryvaniaberemennosti(kriminal_nye)",
                            #     "iskusstvennyj-pojelaniujensiny",
                            #     "iskusstvennyj-pomed.pokazaniamjensiny",
                            #     "iskusstvennyj-pomed.pokazaniamploda",
                            #     "iskusstvennyj-posozial_nympokazaniam",
                            #     "neutocnennye",
                            #     "samoproizvol_nyj"
                            # ]
                        },
                        "maternity_hospital_doctor": {
                            "description": "Лечащий врач роддома (код)",
                            "type": "string"
                        },
                        "curation_hospital": {
                            "description": "ЛПУ курации новорождённого",
                            "type": "string"
                        }
                    },
                    "required": ["admission_date", "pregnancy_duration", "delivery_date", "delivery_time", "maternity_hospital", "diagnosis_osn", "pregnancy_final"]
                },
                "mother_death": {
                    "description": "Информация о смерти матери",
                    "type": "object",
                    "properties": {
                        "death": {
                            "description": "Смерть матери",
                            "type": "boolean"
                        },
                        "reason_of_death": {
                            "description": "Причина смерти матери",
                            "type": "string"
                        },
                        "death_date": {
                            "description": "Дата смерти матери",
                            "type": "string",
                            "format": "date"
                        },
                        "death_time": {
                            "description": "Время смерти матери",
                            "type": "string",
                            "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                        },
                        "pat_diagnosis_osn": {
                            "description": "Основной патологоанатомический диагноз, код диагноза по МКБ-10",
                            "type": "string",
                            "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                        },
                        "pat_diagnosis_sop": {
                            "description": "Диагноз сопутствующий (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            },
                            "minItems": 0
                        },
                        "pat_diagnosis_osl": {
                            "description": "Диагноз осложнения (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            },
                            "minItems": 0
                        },
                        "control_expert_conclusion": {
                            "description": "Заключение ЛКК",
                            "type": "string"
                        }
                    },
                    "required": [
                        "reason_of_death",
                        "death_date",
                        "death_time"
                    ]
                },
                "complications": {
                    "description": "Осложнения при родах",
                    "type": "object",
                    "properties": {
                        "delivery_waters": {
                            "description": "Излитие околоплодных вод, справочник rbRisarDelivery_Waters",
                            "type": "string",
                            # "enum": ["prejdevremennye", "rannie"]
                        },
                        "weakness": {
                            "description": "Слабость родовых сил, справочник rbRisarWeakness",
                            "type": "string",
                            # "enum": ["pervicnaa", "vtoricnaa"]
                        },
                        "meconium_color": {
                            "description": "Мекониальная окраска амниотических вод",
                            "type": "boolean"
                        },
                        "pathological_preliminary_period": {
                            "description": "Патологический прелиминарный период",
                            "type": "boolean"
                        },
                        "abnormalities_of_labor": {
                            "description": "Аномалии родовой деятельности",
                            "type": "boolean"
                        },
                        "chorioamnionitis": {
                            "description": "Хориоамнионит",
                            "type": "boolean"
                        },
                        "perineal_tear": {
                            "description": "Разрыв промежностей (степень)",
                            "type": "string"
                        },
                        "eclampsia": {
                            "description": "Нефропатия/эклампсия в родах, справочник rbRisarEclampsia",
                            "type": "string",
                            # "enum": ["eklampsia", "nefropatia", "net"]
                        },
                        "funiculus": {
                            "description": "Патология пуповины, справочник rbRisarFuniculus",
                            "type": "string",
                            # "enum": [
                            #     "drugaaineutocnennaapatologiapupoviny",
                            #     "korotkaapupovina",
                            #     "obvitie",
                            #     "patologiasosudovpupoviny",
                            #     "vypadeniepupoviny",
                            #     "zaputyvanieiuzelpupoviny"
                            # ]
                        },
                        "afterbirth": {
                            "description": "Патология плаценты, справочник rbRisarAfterbirth",
                            "type": "string",
                            # "enum": [
                            #     "giploplaziaplazenty",
                            #     "plencataaplazenta",
                            #     "polnoeprirasenieplazenty",
                            #     "sosudistaapatologiaplazenty"
                            # ]
                        },
                        "anemia": {
                            "description": "Анемия после родов (Hb<110 г/л)",
                            "type": "string"
                        },
                        "infections_during_delivery": {
                            "description": "Инфекции в родах",
                            "type": "string"
                        },
                        "infections_after_delivery": {
                            "description": "Инфекции после родов",
                            "type": "string"
                        }
                    }
                },
                "manipulations": {
                    "description": "Пособия и манипуляции при родах",
                    "type": "object",
                    "properties": {
                        "caul": {
                            "description": "Вскрытие околоплодного пузыря",
                            "type": "boolean"
                        },
                        "calfbed": {
                            "description": "Ручное обследование матки",
                            "type": "boolean"
                        },
                        "perineotomy": {
                            "description": "Эпизио/перинеотомия",
                            "type": "string"
                        },
                        "secundines": {
                            "description": "Ручное выделение последа",
                            "type": "boolean"
                        },
                        "other_manipulations": {
                            "description": "Другие пособия и манипуляции",
                            "type": "string"
                        }
                    }
                },
                "operations": {
                    "description": "Операции при родах",
                    "type": "object",
                    "properties": {
                        "caesarean_section": {
                            "description": "Кесарево сечение, справочник rbRisarCaesarean_Section",
                            "type": "string",
                            # "enum": ["korporal_noe", "vn.m.segmente"]
                        },
                        "obstetrical_forceps": {
                            "description": "Акушерские щипцы, справочник rbRisarObstetrical_Forceps",
                            "type": "string",
                            # "enum": ["polostnye", "vyhodnye"]
                        },
                        "vacuum_extraction": {
                            "description": "Вакуум-экстракция",
                            "type": "boolean"
                        },
                        "indication": {
                            "description": "Показания к операции, справочник rbRisarIndication",
                            "type": "string",
                            # "enum": ["kombinirovannye", "sostoronymateri", "sostoronyploda"]
                        },
                        "specialities": {
                            "description": "Особенности операции, справочник rbRisarSpecialities",
                            "type": "string",
                            # "enum": [
                            #     "donacalarodov",
                            #     "ekstrennoe",
                            #     "kogdaproizvodilas_operazia",
                            #     "periodrodov",
                            #     "planovoe"
                            # ]
                        },
                        "anesthetization": {
                            "description": "Обезболивание, справочник rbRisarAnesthetization",
                            "type": "string",
                            "pattern": "^(0[1-9]|10)$"
                        },
                        "hysterectomy": {
                            "description": "Гистерэктомия, справочник rbRisarHysterectomy",
                            "type": "string",
                            # "enum": ["boleedvuhsutokposlerodov", "vpredelahdvuhsutokposlerodov"]
                        },
                        "complications": {
                            "description": "Осложнения при родах (массив, код диагноза по МКБ-10)",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            },
                            "minItems": 0
                        },
                        "embryotomy": {
                            "description": "Плодоразрушающие операции",
                            "type": "boolean"
                        }
                    }
                },
                "kids": {
                    "description": "Инфомрация о детях",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "alive": {
                                "description": "Живой",
                                "type": "boolean"
                            },
                            "sex": {
                                "description": "Пол",
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2
                            },
                            "weight": {
                                "description": "Масса",
                                "type": "number",
                                "format": "double"
                            },
                            "length": {
                                "description": "Длина",
                                "type": "number",
                                "format": "double"
                            },
                            "date": {
                                "description": "Дата рождения",
                                "type": "string",
                                "format": "date"
                            },
                            "maturity_rate": {
                                "description": "Степень доношенности, справочник rbRisarMaturity_Rate",
                                "type": "string",
                                # "enum": ["donosennyj", "nedonosennyj", "perenosennyj"]
                            },
                            "apgar_score_1": {
                                "description": "Оценка по Апгар на 1 минуту",
                                "type": "integer"
                            },
                            "apgar_score_5": {
                                "description": "Оценка по Апгар на 5 минуту",
                                "type": "integer"
                            },
                            "apgar_score_10": {
                                "description": "Оценка по Апгар на 10 минуту",
                                "type": "integer"
                            },
                            "death_date": {
                                "description": "Дата смерти",
                                "type": "string",
                                "format": "date"
                            },
                            "death_time": {
                                "description": "Время смерти",
                                "type": "string",
                                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
                            },
                            "death_reason": {
                                "description": "Причина смерти",
                                "type": "string"
                            }
                        },
                        "required": ["alive", "sex", "weight", "length", "date"]
                    },
                    "minItems": 0
                }
            },
            "required": [
                "general_info",
                "kids"
            ]
        },
    ]
