# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class ClientSchema(object):
    """
    Схемы для проверки валидности данных пациента
    """
    schema = [{
        "type": "object",
        "$schema": "http://json-schema.org/draft-04/schema",
        "properties": {
            "FIO": {
                "type": "object",
                "description": "ФИО пациента",
                "properties": {
                    "middlename": {
                        "type": "string",
                        "description": "Отчество пациента",
                        "minLength": 1,
                        "maxLength": 255
                    },
                    "name": {
                        "type": "string",
                        "description": "Имя пациента",
                        "minLength": 1,
                        "maxLength": 255
                    },
                    "surname": {
                        "type": "string",
                        "description": "Фамилия пациента",
                        "minLength": 1,
                        "maxLength": 255
                    }
                },
                "required": [
                    "name",
                    "surname"
                ]
            },
            "birthday_date": {
                "type": "string",
                "description": "Дата рождения"
            },
            "SNILS": {
                "type": "string",
                "description": "СНИЛС пациента",
                "minLength": 11,
                "maxLength": 14
            },
            "gender": {
                "type": "integer",
                "description": "Пол пациента: 0 - Пол не указан, 1 - Мужской, 2 - Женский",
                "enum": [
                    2
                ]
            },
            "document": {
                "type": "object",
                "description": "Документ, удостоверяющий личность пациента",
                "properties": {
                    "document_type_code": {
                        "type": "integer",
                        "description": "Код типа документа, идентифицирующего личность по федеральному приказу ФОМС №79 от 7.04.2011",
                        "enum": [
                            14,
                            2,
                            5,
                            8,
                            9,
                            21,
                            22,
                            23,
                            24,
                            25,
                            26,
                            27,
                            28,
                            1,
                            15,
                            3,
                            10,
                            11,
                            12,
                            13
                        ]
                    },
                    "document_series": {
                        "type": "string",
                        "description": "Серия документа, удостоверяющего личность пациента",
                        "maxLength": 8
                    },
                    "document_number": {
                        "type": "string",
                        "description": "Номер документа, удостоверяющего личность пациента",
                        "maxLength": 16
                    },
                    "document_beg_date": {
                        "type": "string",
                        "description": "Дата выдачи документа, удостоверяющего личность пациента"
                    },
                    "document_issuing_authority": {
                        "type": "string",
                        "description": "Орган, выдавший документ, удостоверяющий личность пациента"
                    }
                },
                "required": [
                    "document_type_code",
                    "document_series",
                    "document_number",
                    "document_beg_date",
                    "document_issuing_authority"
                ]
            },
            "insurance_documents": {
                "type": "array",
                "description": "Полисы медицинского страхования",
                "items": {
                    "type": "object",
                    "description": "Полис медицинского страхования",
                    "properties": {
                        "insurance_document_type": {
                            "type": "string",
                            "description": "Код ТФОМС типа полиса медицинского страхования"
                        },
                        "insurance_document_series": {
                            "type": "string",
                            "description": "Серия полиса медицинского страхования",
                            "maxLength": 16
                        },
                        "insurance_document_number": {
                            "type": "string",
                            "description": "Номер полиса медицинского страхования",
                            "maxLength": 16
                        },
                        "insurance_document_beg_date": {
                            "type": "string",
                            "description": "Дата выдачи полиса медицинского страхования"
                        },
                        "insurance_document_issuing_authority": {
                            "type": "string",
                            "description": "Код ИНН органа выдачи полиса медицинского страхования"
                        }
                    },
                    "required": [
                        "insurance_document_type",
                        "insurance_document_number",
                        "insurance_document_beg_date",
                        "insurance_document_issuing_authority"
                    ]

                }
            },
            "residential_address": {
                "type": "object",
                "description": "Адрес проживания пациента",
                "properties": {
                    "KLADR_locality": {
                        "type": "string",
                        "description": "Код населённого пункта адреса проживания по справочнику КЛАДР"
                    },
                    "KLADR_street": {
                        "type": "string",
                        "description": "Код улицы адреса проживания по справочнику КЛАДР"
                    },
                    "house": {
                        "type": "string",
                        "description": "Данные дома адреса проживания",
                        "maxLength": 8
                    },
                    "building": {
                        "type": "string",
                        "description": "Корпус дома адреса проживания",
                        "maxLength": 8
                    },
                    "flat": {
                        "type": "string",
                        "description": "Данные квартиры адреса проживания",
                        "maxLength": 6
                    },
                    "locality_type": {
                        "type": "integer",
                        "description": "Тип населенного пункта: 0-село, 1 - город",
                        "enum": [
                            0,
                            1
                        ]
                    }
                },
                "required": [
                    "KLADR_locality",
                    "KLADR_street",
                    "house",
                    "locality_type"
                ]
            },
            "blood_type_info": {
                "type": "array",
                "description": "Данные группы крови и резус-фактора пациентки",
                "items": {
                    "type": "object",
                    "description": "Сведение о группе крови и резус-факторе",
                    "properties": {

                        "blood_type": {
                            "type": "string",
                            "description": "Код группы крови",
                            "enum":
                                [
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
                        }
                    },
                    "required": [
                        "blood_type"
                    ]
                }
            },
            "allergies_info": {
                "type": "array",
                "description": "Данные аллергии пациентки",
                "items": {
                    "type": "object",
                    "description": "Сведение об аллергии",
                    "properties": {
                        "allergy_power": {
                            "type": "integer",
                            "description": "Код степени аллергии: 0-не известно, 1-малая, 2-средняя, 3- высокая, 4-строгая",
                            "enum": [
                                0,
                                1,
                                2,
                                3,
                                4
                            ]
                        },
                        "allergy_substance": {
                            "type": "string",
                            "description": "Вещество",
                            "maxLength": 128
                        }
                    },
                    "required": [
                        "allergy_power",
                        "allergy_substance"
                    ]
                }
            },
            "medicine_intolerance_info": {
                "type": "array",
                "description": "Данные медицинской непереносимости",
                "items": {
                    "type": "object",
                    "description": "Сведение о медикаментозной непереносимости",
                    "properties": {
                        "medicine_intolerance__power": {
                            "type": "integer",
                            "description": "Степень медикаментозной непереносимости: 0-не известно, 1-малая, 2-средняя, 3- высокая, 4-строгая",
                            "enum": [
                                0,
                                1,
                                2,
                                3,
                                4
                            ]
                        },
                        "medicine_substance": {
                            "type": "string",
                            "description": "Вещество",
                            "maxLength": 128
                        }
                    },
                    "required": [
                        "medicine_intolerance__power",
                        "medicine_substance"
                    ]
                }
            }
        },
        "required": [
            "FIO",
            "birthday_date",
            "gender",
            "document"
        ]
    }]