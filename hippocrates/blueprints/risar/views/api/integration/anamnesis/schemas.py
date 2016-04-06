# -*- coding: utf-8 -*-


class AnamnesisMotherSchema(object):
    """
    Схемы для проверки валидности данных анамнеза матери
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "id": "mother_anamnesis_schema",
        "type": "object",
        "properties": {
            "anamnesis_id": {
                "id": "mother_anamnesis_schema/anamnesis_id",
                "type": "string",
                "description": "Идентификатор анамнеза в системе БАРС МР"
            },
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
            "last_period_date",
            "marital_status"
        ]
    }]


class AnamnesisFatherSchema(object):
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