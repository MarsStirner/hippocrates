#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""


class CheckupObsFirstSchema(object):
    """
    Схемы для проверки валидности данных первичного осмотра
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "firstcheckup",
            "description": "Первичный осмотр беременной акушером-гинекологом и специалистом ПЦ",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "general_info": {
                    "description": "Общие данные осмотра",
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
                        "height": {
                            "description": "Рост",
                            "type": "number",
                            "format": "double"
                        },
                        "weight": {
                            "description": "Масса при осмотре",
                            "type": "number",
                            "format": "double"
                        }
                    },
                    "required": ["date", "hospital", "doctor", "height", "weight"]
                },
                "somatic_status": {
                    "description": "Данные соматического статуса",
                    "type": "object",
                    "properties": {
                        "state": {
                            "description": "Общее состояние, справочник rbRisarState",
                            "type": "string",
                            "enum": ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
                        },
                        "subcutaneous_fat": {
                            "description": "Подкожно-жировая клетчатка, справочник rbRisarSubcutaneous_Fat",
                            "type": "string",
                            "enum": ["izbytocnorazvita", "nedostatocnorazvita", "umerennorazvita"]
                        },
                        "tongue": {
                            "description": "Язык, справочник rbRisarTongue",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["01", "02", "03", "04", "vlajnyj"]
                            }
                        },
                        "complaints": {
                            "description": "Жалобы, справочник rbRisarComplaints",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "epigastrii",
                                    "golovnaabol_",
                                    "moving",
                                    "net",
                                    "oteki",
                                    "rvota",
                                    "tosnota",
                                    "zrenie"
                                ]
                            }
                        },
                        "skin": {
                            "description": "Кожа, справочник rbRisarSkin",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "naliciekrovoizlianij",
                                    "naliciesypi",
                                    "obycnojokraskiivlajnosticistaa",
                                    "povysennojvlajnosti",
                                    "suhaa"
                                ]
                            }
                        },
                        "lymph": {
                            "description": "Лимфоузлы, справочник rbRisarLymph",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "boleznennye",
                                    "neboleznennye",
                                    "nepal_piruutsa",
                                    "neuvelicennye",
                                    "pal_piruutsa",
                                    "uvelicennye"
                                ]
                            }
                        },
                        "breast": {
                            "description": "Молочные железы, справочник rbRisarBreast",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "bezpatologiceskihizmenenij",
                                    "mestnoeuplotnenie",
                                    "nagrubanie",
                                    "pokrasnenie",
                                    "tresinysoskov"
                                ]
                            }
                        },
                        "heart_tones": {
                            "description": "Тоны сердца, справочник rbRisarHeart_Tones",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "akzentIItona",
                                    "aritmicnye",
                                    "asnye",
                                    "gluhie",
                                    "prigluseny",
                                    "proslusivautsa",
                                    "ritmicnye"
                                ]
                            }
                        },
                        "pulse": {
                            "description": "Пульс, справочник, справочник rbRisarPulse",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["defizitpul_sa",
                                         "udovletvoritel_nogonapolnenia"]
                            }
                        },
                        "nipples": {
                            "description": "Состояние сосков, справочник rbRisarNipples",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "norma",
                                    "tresiny",
                                    "vospalenie"
                                ]
                            }
                        },
                        "mouth": {
                            "description": "Полость рта, справочник rbRisarMouth",
                            "type": "string",
                            "enum": ["nujdaetsavsanazii", "sanirovana"]
                        },
                        "respiratory": {
                            "description": "Органы дыхания, справочник rbRisarBreathe",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "dyhaniejestkoe",
                                    "dyhanievezikularnoe",
                                    "hripyotsutstvuut",
                                    "hripysuhie",
                                    "hripyvlajnye"
                                ]
                            }
                        },
                        "abdomen": {
                            "description": "Органы брюшной полости, справочник rbRisarStomach",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "jivotmagkijbezboleznennyj",
                                    "jivotnaprajennyj",
                                    "jivotuvelicenzascetberemennojmatki"
                                ]
                            }
                        },
                        "liver": {
                            "description": "Печень, справочник rbRisarLiver",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["nepal_piruetsa", "uvelicena"]
                            }
                        },
                        "urinoexcretory": {
                            "description": "Мочевыводящая система, справочник rbRisarUrinoexcretory",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "moceispuskanieucasennoe",
                                    "moceispuskanievnorme",
                                    "СindromPasternazkogo"
                                ]
                            }
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
                        "edema": {
                            "description": "Отёки",
                            "type": "string"
                        },
                        "veins": {
                            "description": "Состояние вен, справочник rbRisarVein",
                            "type": "string",
                            "enum": ["noma", "poverhnostnyjvarikoz", "varikoznoerassirenieven"]
                        },
                        "bowel_and_bladder_habits": {
                            "description": "Физиологические отправления",
                            "type": "string"
                        },
                        "heart_rate": {
                            "description": "ССС: пульс",
                            "type": "integer"
                        }
                    },
                    "required": [
                        "state",
                        "subcutaneous_fat",
                        "tongue",
                        "complaints",
                        "skin",
                        "lymph",
                        "breast",
                        "heart_tones",
                        "pulse",
                        "nipples",
                        "mouth",
                        "respiratory",
                        "abdomen",
                        "liver",
                        "urinoexcretory",
                        "ad_right_high",
                        "ad_left_high",
                        "ad_right_low",
                        "ad_left_low",
                        "veins",
                        "heart_rate"
                    ]
                },
                "obstetric_status": {
                    "description": "Акушерский статус",
                    "type": "object",
                    "properties": {
                        "horiz_diagonal": {
                            "description": "Горизонтальная диагональ",
                            "type": "number",
                            "format": "double"
                        },
                        "vert_diagonal": {
                            "description": "Вертикальная диагональ",
                            "type": "number",
                            "format": "double"
                        },
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
                            "enum": ["gipertonus", "normal_nyjtonus"]
                        },
                        "dssp": {
                            "description": "Ds.SP",
                            "type": "number",
                            "format": "double"
                        },
                        "dscr": {
                            "description": "Ds.Cr",
                            "type": "number",
                            "format": "double"
                        },
                        "dstr": {
                            "description": "Ds.Tr",
                            "type": "number",
                            "format": "double"
                        },
                        "cext": {
                            "description": "C.Ext",
                            "type": "number",
                            "format": "double"
                        },
                        "cdiag": {
                            "description": "C.Diag",
                            "type": "number",
                            "format": "double"
                        },
                        "cvera": {
                            "description": "C.Vera",
                            "type": "number",
                            "format": "double"
                        },
                        "soloviev_index": {
                            "description": "Индекс Соловьёва",
                            "type": "number",
                            "format": "double"
                        },
                        "pelvis_narrowness": {
                            "description": "Степень сужения таза, справочник rbRisarPelvis_Narrowness",
                            "type": "string",
                            "enum": [
                                "IIIsteen_",
                                "IIstepen_",
                                "IVstepen_",
                                "Istepen_",
                                "norma"
                            ]
                        },
                        "pelvis_form": {
                            "description": "Форма таза, справочник rbRisarPelvis_Form",
                            "type": "string",
                            "enum": [
                                "normal_nyj",
                                "obseravnomernosujennyj",
                                "obsesujennyjploskij",
                                "ploskorahiticeskij",
                                "poperecnosujennyj",
                                "prostojploskij"
                            ]
                        }
                    },
                    "required": [
                        "uterus_state",
                        "dssp",
                        "dscr",
                        "dstr",
                        "cext",
                        "soloviev_index"
                    ]
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
                                "enum": ["kosoe", "poperecnoe", "prodol_noe"]
                            },
                            "fetus_position": {
                                "description": "Позиция плода, справочник rbRisarFetus_Position_2",
                                "type": "string",
                                "enum": ["pervaa", "vtoraa"]
                            },
                            "fetus_type": {
                                "description": "Вид плода, справочник rbRisarFetus_Type",
                                "type": "string",
                                "enum": ["perednij", "zadnij"]
                            },
                            "fetus_presentation": {
                                "description": "Предлежащая часть плода, справочник rbRisarPresenting_Part",
                                "type": "string",
                                "enum": [
                                    "cistoagodicnoepredlejanie",
                                    "golovnoepredlejanie",
                                    "lizevoepredlejanie",
                                    "lobnoepredlejanie",
                                    "nojnoepredlejanie",
                                    "perednegolovnoepredlejanie",
                                    "smesannoeagodicnoepredlejanie",
                                    "tazovoepredlejanie",
                                    "zatylocnoepredlejanie"
                                ]
                            },
                            "fetus_heartbeat": {
                                "description": "Сердцебиение плода, справочник rbRisarFetus_Heartbeat",
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["asnoe", "ritmicnoe"]
                                }
                            },
                            "fetus_heart_rate": {
                                "description": "ЧСС плода",
                                "type": "number",
                                "format": "double"
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
                            "type": "string",
                            "enum": ["svobodnoe", "uzkoe"]
                        },
                        "cervix": {
                            "description": "Шейка матки, справочник rbRisarCervix",
                            "type": "string",
                            "enum": [
                                "koniceskaacistaa",
                                "koniceskaaerozirovannaa",
                                "zilindriceskaacistaa",
                                "zilindriceskaaerozirovanaa"
                            ]
                        },
                        "cervix_length": {
                            "description": "Длина шейки матки, справочник rbRisarCervix_Length",
                            "type": "string",
                            "enum": ["bolee2sm", "menee1sm", "menee2smnobolee1sm"]
                        },
                        "cervical_canal": {
                            "description": "Цервикальный канал, справочник rbRisarCervical_Canal",
                            "type": "string",
                            "enum": [
                                "narujnyjzevprohodimdla1poperecnogopal_za",
                                "narujnyjzevzakryt",
                                "vnutrennijzevpriotkryt"
                            ]
                        },
                        "cervix_consistency": {
                            "description": "Консистенция шейки матки, справочник rbRisarCervix_Consistency",
                            "type": "string",
                            "enum": ["magkaa", "plotnaa", "razmagcennaa"]
                        },
                        "cervix_position": {
                            "description": "Позиция шейки матки, справочник rbRisarCervix_Position",
                            "type": "string",
                            "enum": ["kperediotprovodnoj",
                                     "kzadiotprovodnojosi",
                                     "poprovodnojositaza"]
                        },
                        "cervix_maturity": {
                            "description": "Зрелость шейки матки, справочник rbRisarCervix_Maturity",
                            "type": "string",
                            "enum": ["nezrelaa", "sozrevausaa", "zrelaa"]
                        },
                        "body_of_uterus": {
                            "description": "Тело матки, справочник rbRisarBody_Of_Womb",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "bezboleznennopripal_pazii",
                                    "boleznennopripal_pazii",
                                    "magkovatojkonsistenzii",
                                    "nepodvijno",
                                    "podvijno"
                                ]
                            }
                        },
                        "adnexa": {
                            "description": "Придатки, справочник rbRisarAppendages",
                            "type": "string",
                            "enum": ["bezosobennostej", "uveliceny"]
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
                            "description": "Околоматочное пространство",
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
                    },
                    "required": ["vagina", "cervix"]
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
                            "type": "string",
                            "enum": ["osvobojdenieotnocnyhsmen", "vsmenerabotynenujdaetsa"]
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
                        "recommendations": {
                            "description": "Рекомендации",
                            "type": "string"
                        },
                        "notes": {
                            "description": "Примечания",
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
            "required": ["external_id", "general_info", "somatic_status",
                         "obstetric_status", "medical_report"]
        },
    ]
