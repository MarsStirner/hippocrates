# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class AnamnesisMotherSchema(Schema):
    """
    Схемы для проверки валидности данных анамнеза матери
    """
    schema = [{
    "$schema": "http://json-schema.org/draft-04/schema",
    "id": "mother_anamnesis_schema",
    "type": "object",
    "properties": {
        "education": {
            "id": "mother_anamnesis_schema/education",
            "type": "string",
            "description": "Код значения образования"
        },
        "work_group": {
            "id": "mother_anamnesis_schema/work_group",
            "type": "string",
            "description": "Код значения общественно-профессиональной группы"
        },
        "professional_properties": {
            "id": "mother_anamnesis_schema/professional_properties",
            "type": "string",
            "description": "Код значения профессиональных вредностей"
        },
        "family_income": {
            "id": "mother_anamnesis_schema/family_income",
            "type": "string",
            "description": "Код значения дохода семьи"
        },
        "menstruation_start_age": {
            "id": "mother_anamnesis_schema/menstruation_start_age",
            "type": "string",
            "description": "Возраст женщины,когда начались менструации"
        },
        "menstruation_duration": {
            "id": "mother_anamnesis_schema/menstruation_duration",
            "type": "string",
            "description": "Продолжительность менструаций"
        },
        "menstruation_period": {
            "id": "mother_anamnesis_schema/menstruation_period",
            "type": "string",
            "description": "Продолжительность менструального цикла"
        },
        "menstrual_disorder": {
            "id": "mother_anamnesis_schema/menstrual_disorder",
            "type": "boolean",
            "description": "Сведения о нарушении менструального цикла женщины"
        },
        "sex_life_age": {
            "id": "mother_anamnesis__schema/sex_life_age",
            "type": "integer",
            "description": "Возраст начала половой жизни женщины"
        },
        "fertilization_type": {
            "id": "mother_anamnesis_schema/fertilization_type",
            "type": "string",
            "description": "Код значения способа оплодотворения"
        },
        "intrauterine_operation": {
            "id": "mother_anamnesis_schema/intrauterine_operation",
            "type": "boolean",
            "description": "Наличие внутриматочного вмешательства в анамнезе женщины"
        },
        "uterine_scar_quantity": {
            "type": "string",
            "description": "Количество рубцов на матке, код по справочнику rbRisarUterineScar"
        },
        "uterine_scar_location": {
            "type": "string",
            "description": "Расположение рубца на матке, код по справочнику rbRisarUterineScarLocation"
        },
        "solitary_paired": {
            "type": "boolean",
            "description": "Наличие единственной почки"
        },
        "multiple_fetation": {
            "id": "mother_anamnesis_schema/multiple_fetation",
            "type": "boolean",
            "description": "Наличие многоплодных беременностей в анамнезе матери"
        },
        "infertility": {
            "id": "mother_anamnesis_schema/infertility",
            "type": "object",
            "description": "Блок информации о бесплодии в анамнезе женщины, если такое имело место",
            "properties": {
                "infertility_occurence": {
                    "id": "mother_anamnesis_schema/infertility/infertility_occurence",
                    "type": "boolean",
                    "description": "Наличие бесплодия в анамнезе женщины"
                },
                "infertility_type": {
                    "id": "mother_anamnesis_schema/infertility/infertility_type",
                    "type": "string",
                    "description": "Код значения типа бесплодия"
                },
                "infetrility_duration": {
                    "id": "mother_anamnesis_schema/infertility/infetrility_duration",
                    "type": "integer",
                    "description": "Длительность бесплодия, лет"
                },
                "infertility_treatment": {
                    "id": "mother_anamnesis_schema/infertility/infertility_treatment",
                    "type": "array",
                    "description": "Сведения о методах лечения бесплодия",
                    "items": {
                        "type": "string",
                        "description": "Код значения метода лечения"
                    }
                },
                "infertility_causes": {
                    "id": "mother_anamnesis_schema/infertility/infertility_causes",
                    "type": "array",
                    "description": "Сведения о причинах бесплодия",
                    "items": {
                        "type": "string",
                        "description": "Код причины бесплодия"
                    }
                }
            },
            "required": [
                "infertility_occurence",
                "infertility_type",
                "infetrility_duration",
                "infertility_treatment",
                "infertility_causes"
            ]
        },
        "smoking": {
            "id": "mother_anamnesisr_schema/smoking",
            "type": "boolean",
            "description": "Сведения о курении"
        },
        "alcohol": {
            "id": "mother_anamnesis_schema/alcohol",
            "type": "boolean",
            "description": "Сведения об алкоголе"
        },
        "toxic": {
            "id": "mother_anamnesis_schema/toxic",
            "type": "boolean",
            "description": "Сведения о токсических веществах"
        },
        "drugs": {
            "id": "mother_anamnesis_schema/drugs",
            "type": "boolean",
            "description": "Сведения о наркотиках"
        },
        "contraception": {
            "id": "mother_anamnesis_schema/contraception",
            "type": "array",
            "description":"Сведения о методах контрацепции",
            "items": {
                    "type": "string",
                    "description": "Код метода контрацепции по справочнику"
                }
        },
        "hereditary": {
            "id": "mother_anamnesis_schema/hereditary",
            "type": "array",
            "description": "Сведения о наследственных заболеванияъ женщины",
            "items": {
                "type": "string",
                "description": "Код наследственного заболевания по справочнику"
            }
        },
        "finished_diseases": {
            "id": "mother_anamnesis_schema/finished_diseases",
            "type": "string",
            "description": "Сведения о перенесённых заболеваниях"
        },
        "current_diseases": {
            "id": "mother_anamnesis_schema/current_diseases",
            "type": "array",
            "description": "Список текущих заболеваний женщины в виде кодов МКБ",
            "items": {
                    "type": "string",
                    "description": "Код заболевания по МКБ-10",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                }
        },
        "last_period_date": {
            "id": "mother_anamnesis_schema/last_period_date",
            "type": "string",
            "description": "Дата первого дня последней менструации"
        },
        "preeclampsia_mother_sister": {
            "id": "mother_anamnesis_schema/preeclampsia_mother_sister",
            "type": "boolean",
            "description": "Наличие преэклампсии у матери или сестры"
        },
        "marital_status": {
            "id": "mother_anamnesis_schema/marital_status",
            "type": "string",
            "description": "Код значения семейного положения"
        }
    },
    "required": [
        "marital_status"
    ]
}]


class AnamnesisFatherSchema(Schema):
    """
    Схемы для проверки валидности данных анамнеза отца
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "father_anamnesis_schema",
        "description": "Схема, описывающая данные для регистрации или изменения данных анамнеза отца",
        "id": "father_anamnesis_schema",
        "type": "object",
        "properties": {
            "FIO": {
                "id": "father_anamnesis_schema/FIO",
                "type": "string",
                "description": "ФИО отца ребёнка"
            },
            "age": {
                "id": "father_anamnesis_schema/age",
                "type": "string",
                "description": "Возраст отца ребёнка"
            },
            "education": {
                "id": "father_anamnesis_schema/education",
                "type": "string",
                "description": "Код значения образования"
            },
            "work_group": {
                "id": "father_anamnesis_schema/work_group",
                "type": "string",
                "description": "Код значения общественно-профессиональной группы"
            },
            "professional_properties": {
                "id": "father_anamnesis_schema/professional_properties",
                "type": "string",
                "description": "Код значения профессиональных вредностей"
            },
            "telephone_number": {
                "id": "father_anamnesis_schema/telephone_number",
                "type": "string",
                "description": "Контактный телефонный номер отца ребенка"
            },
            "fluorography": {
                "id": "father_anamnesis_schema/fluorography",
                "type": "string",
                "description": "Сведения о флюорографии отца ребенка"
            },
            "hiv": {
                "id": "father_anamnesis_schema/hiv",
                "type": "boolean",
                "description": "Сведения о наличии заболевания ВИЧем отца ребенка"
            },
            "blood_type": {
                "id": "father_anamnesis_schema/blood_type",
                "type":"string",
                "description": "Сведения о группе крови и резус-факторе",
                "enum": [
                    "0(I)Rh-",
                    "0(I)Rh+",
                    "A(II)Rh-",
                    "A(II)Rh+",
                    "B(III)Rh-",
                    "B(III)Rh+",
                    "AB(IV)Rh-",
                    "AB(IV)Rh+",
                    "0(I)RhDu",
                    "A(II)RhDu",
                    "B(III)RhDu",
                    "AB(IV)RhDu"
                ]
            },
            "infertility": {
                "id": "father_anamnesis_schema/infertility",
                "type": "object",
                "description": "Блок информации о бесплодии в анамнезе отца ребенка, если такое имело место",
                "properties": {
                    "infertility_occurence": {
                        "id": "father_anamnesis_schema/infertility/infertility_occurence",
                        "type": "boolean",
                        "description": "Наличие бесплодия в анамнезе отца ребенка"
                    },
                    "infertility_type": {
                        "id": "father_anamnesis_schema/infertility/infertility_type",
                        "type": "string",
                        "description": "Код значения типа бесплодия"
                    },
                    "infetrility_duration": {
                        "id": "father_anamnesis_schema/infertility/infetrility_duration",
                        "type": "integer",
                        "description": "Длительность бесплодия, лет"
                    },
                    "infertility_treatment": {
                        "id": "father_anamnesis_schema/infertility/infertility_treatment",
                        "type": "array",
                        "description": "Сведения о методах лечения бесплодия",
                        "items": {
                            "type": "string",
                            "description": "Код значения метода лечения"
                        }
                    },
                    "infertility_causes": {
                        "id": "father_anamnesis_schema/infertility/infertility_causes",
                        "type": "array",
                        "description": "Сведения о причинах бесплодия",
                        "items": {
                            "type": "string",
                            "description": "Код причины бесплодия"
                        }
                    }
                },
                "required": [
                    "infertility_occurence",
                    "infertility_type",
                    "infetrility_duration",
                    "infertility_treatment",
                    "infertility_causes"
                ]
            },
            "smoking": {
                "id": "father_anamnesis_schema/smoking",
                "type": "boolean",
                "description": "Сведения о курении"
            },
            "alcohol": {
                "id": "father_anamnesis_schema/alcohol",
                "type": "boolean",
                "description": "Сведения об алкголе"
            },
            "toxic": {
                "id": "father_anamnesis_schema/toxic",
                "type": "boolean",
                "description": "Сведения о токсических веществах"
            },
            "drugs": {
                "id": "father_anamnesis_schema/drugs",
                "type": "boolean",
                "description": "Сведения о наркотиках"
            },
            "hereditary": {
                "id": "father_anamnesis_schema/hereditary",
                "type": "array",
                "description": "Сведения о наследственных заболеваниях",
                "items": {
                    "type": "string",
                    "description": "Код наследственного заболевания по справочнику"
                }
            },
            "finished_diseases": {
                "id": "father_anamnesis_schema/finished_diseases",
                "type": "string",
                "description": "Сведения о перенесённых заболеваниях"
            },
            "current_diseases": {
                "id": "father_anamnesis_schema/current_diseases",
                "type": "string",
                "description": "Сведения о текущих заболеваниях отца ребенка"
            }
        }
    }]


class AnamnesisPrevPregSchema(Schema):
    """
    Схемы для проверки валидности данных анамнеза предыдущих беременностей
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "id": "anamnesis_prev_pregnancy_schema",
        "title": "anamnesis_prev_pregnancy_schema",
        "type": "object",
        "description": "Сведение о предыдущей беременности",
        "properties": {
            "prevpregnancy_id": {
                "id": "anamnesis_prev_pregnancy_schema/prevpregnancy_id",
                "type": "string",
                "description": "Идентификатор анамнеза предыдущей беременности в системе БАРС МР"
            },
            "pregnancy_year": {
                "id": "anamnesis_prev_pregnancy_schema/pregnancy_year",
                "type": "integer",
                "maxLength": 4,
                "minLength": 4,
                "description": "Год беременности"
            },
            "pregnancy_result": {
                "id": "anamnesis_prev_pregnancy_schema/pregnancy_result",
                "type": "string",
                "description": "Код значения исхода беременности в анамнезе"
            },
            "gestational_age": {
                "id": "anamnesis_prev_pregnancy_schema/gestational_age",
                "type": "integer",
                "description": "Срок беременности"
            },
            "preeclampsia": {
                "id": "anamnesis_prev_pregnancy_schema/preeclampsia",
                "type": "boolean",
                "description": "Наличие преэклампсии при беременности в анамнезе"
            },
            "after_birth_complications": {
                "id": "anamnesis_prev_pregnancy_schema/after_birth_complications",
                "type": "array",
                "description": "Осложнения после родов или аборта в виде кодов МКБ",
                "items": {
                    "type": "string",
                    "description": "Код осложнения по МКБ-10",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                }
            },
            "assistance_and_operations": {
                "id": "anamnesis_prev_pregnancy_schema/assistance_and_operations",
                "type": "array",
                "description": "Коды значений пособий и операций",
                "items": {
                    "type": "string",
                    "description": "Код значения пособия/операции"
                }
            },
            "pregnancy_pathologies": {
                "id": "anamnesis_prev_pregnancy_schema/pregnancy_pathologies",
                "type": "array",
                "description": "Патологии беременности в виде кодов МКБ",
                "items": {
                    "type": "string",
                    "description": "Код патологии по МКБ-10",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                }
            },
            "birth_pathologies": {
                "id": "anamnesis_prev_pregnancy_schema/birth_pathologies",
                "type": "array",
                "description": "Патологии родов/аборта в виде кодов МКБ",
                "items": {
                    "type": "string",
                    "description": "Код патологии по МКБ-10",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                }
            },
            "features": {
                "id": "anamnesis_prev_pregnancy_schema/features",
                "type": "string",
                "description": "Особенности беременности"
            },
            "child_information": {
                "id": "anamnesis_prev_pregnancy_schema/child_information",
                "type": "array",
                "description": "Список детей и информации о них",
                "items": {
                    "type": "object",
                    "description": "Сведение о ребенке",
                    "properties": {
                        "is_alive": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/is_alive",
                            "type": "boolean",
                            "description": "Живой или нет"
                        },
                        "weight": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/weight",
                            "type": "number",
                            "description": "Вес при рождении в граммах"
                        },
                        "death_cause": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/death_cause",
                            "type": "string",
                            "description": "Причина смерти"
                        },
                        "death_at": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/death_at",
                            "type": "string",
                            "description": "Код значения срока смерти. Является обязательным при передаче,если значение isAlive = false"
                        },
                        "abnormal_development": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/abnormal_development",
                            "type": "boolean",
                            "description": "Наличие аномалий развития"
                        },
                        "neurological_disorders": {
                            "id": "anamnesis_prev_pregnancy_schema/child_information/neurological_disorders",
                            "type": "boolean",
                            "description": "Наличие неврологических нарушений"
                        }
                    }
                }
            }
        },
        "required": [
            "pregnancy_year",
            "pregnancy_result"
        ]
    }]