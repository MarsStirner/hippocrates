# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class ClientSchema(object):
    """
    Схемы для проверки валидности данных пациента
    """
    schema = [{
        "type": "object",
        "$schema": "http://json-schema.org/draft-04/schema",
        "id": "http://jsonschema.net",
        "properties": {
            "FIO": {
                "type": "object",
                "id": "http://jsonschema.net/FIO",
                "description": "ФИО пациента",
                "properties": {
                    "middlename": {
                        "type": "string",
                        "id": "http://jsonschema.net/FIO/middlename",
                        "description": "Отчество пациента",
                        "minLength": 1,
                        "maxLength": 255,
                    },
                    "name": {
                        "type": "string",
                        "id": "http://jsonschema.net/FIO/name",
                        "description": "Имя пациента",
                        "minLength": 1,
                        "maxLength": 255,
                    },
                    "surname": {
                        "type": "string",
                        "id": "http://jsonschema.net/FIO/surname",
                        "description": "Фамилия пациента",
                        "minLength": 1,
                        "maxLength": 255,
                    }
                },
                "required": [
                    "name",
                    "surname"
                ]
            },
            "birthday_date": {
                "type": "string",
                "id": "http://jsonschema.net/birthday_date",
                "description": "Дата рождения"
            },
            "gender": {
                "type": "integer",
                "id": "http://jsonschema.net/gender",
                "description": "Пол пациента: 0 - Пол не указан, 1 - Мужской, 2 - Женский",
                "enum": [2],
            },
            "SNILS": {
                "type": "string",
                "id": "http://jsonschema.net/SNILS",
                "description": "СНИЛС пациента",
                "minLength": 11,
                "maxLength": 14,
            },
            "document": {
                "type": "object",
                "id": "http://jsonschema.net/document",
                "description": "Документ, удостоверяющий личность пациента",
                "properties": {
                    "document_type_code": {
                        "type": "integer",
                        "id": "http://jsonschema.net/document/document_type_code",
                        "description": "Код типа документа, идентифицирующего личность по федеральному приказу ФОМС №79 от 7.04.2011",
                        "enum": [
                            1,
                            2,
                            3,
                            5,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            21,
                            22,
                            23,
                            24,
                            25,
                            26,
                            27,
                            28,
                        ]
                    },
                    "document_series": {
                        "type": "string",
                        "id": "http://jsonschema.net/document/document_series",
                        "description": "Серия документа, удостоверяющего личность пациента",
                        "maxLength": 8,
                    },
                    "document_number": {
                        "type": "string",
                        "id": "http://jsonschema.net/document/document_number",
                        "description": "Номер документа, удостоверяющего личность пациента",
                        "maxLength": 16,
                    },
                    "document_beg_date": {
                        "type": "string",
                        "id": "http://jsonschema.net/document/document_beg_date",
                        "description": "Дата выдачи документа, удостоверяющего личность пациента"
                    },
                    "document_issuing_authority": {
                        "type": "string",
                        "id": "http://jsonschema.net/document/document_issuing_authority",
                        "description": "Орган, выдавший документ, удостоверяющий личность пациента"
                    }
                },
                "required": [
                    "document_type_code",
                    "document_series",
                    "document_beg_date",
                    "document_issuing_authority"
                ]
            },
            "insurance_documents": {
                "type": "array",
                "id": "http://jsonschema.net/insurance_documents",
                "description": "Полисы медицинского страхования",
                "items": {
                    "type": "object",
                    "description": "Полис медицинского страхования",
                    "properties": {
                        "insurance_document_type": {
                            "type": "string",
                            "id": "http://jsonschema.net/insurance_documents/insurance_document_type",
                            "description": "Код ТФОМС типа полиса медицинского страхования"
                        },
                        "insurance_document_series": {
                            "type": "string",
                            "id": "http://jsonschema.net/insurance_documents/insurance_document_series",
                            "description": "Серия полиса медицинского страхования",
                            "maxLength": 16
                        },
                        "insurance_document_number": {
                            "type": "string",
                            "id": "http://jsonschema.net/insurance_documents/insurance_document_number",
                            "description": "Номер полиса медицинского страхования",
                            "maxLength": 16
                        },
                        "insurance_document_beg_date": {
                            "type": "string",
                            "id": "http://jsonschema.net/insurance_documents/insurance_document_beg_date",
                            "description": "Дата выдачи полиса медицинского страхования"
                        },
                        "insurance_document_issuing_authority": {
                            "type": "string",
                            "id": "http://jsonschema.net/insurance_documents/insurance_document_beg_date",
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
                "id": "http://jsonschema.net/residential_address",
                "description": "Адрес проживания пациента",
                "properties": {
                    "KLADR_locality": {
                        "type": "string",
                        "id": "http://jsonschema.net/residential_address/KLADR_locality",
                        "description": "Код населённого пункта адреса проживания по справочнику КЛАДР"
                    },
                    "KLADR_street": {
                        "type": "string",
                        "id": "http://jsonschema.net/residential_address/KLADR_street",
                        "description": "Код улицы адреса проживания по справочнику КЛАДР"
                    },
                    "house": {
                        "type": "string",
                        "id": "http://jsonschema.net/residential_address/house",
                        "description": "Данные дома адреса проживания",
                        "maxLength": 8
                    },
                    "building": {
                        "type": "string",
                        "id": "http://jsonschema.net/residential_address/building",
                        "description": "Корпус дома адреса проживания",
                        "maxLength": 8
                    },
                    "flat": {
                        "type": "string",
                        "id": "http://jsonschema.net/residential_address/flat",
                        "description": "Данные квартиры адреса проживания",
                        "maxLength": 6
                    },
                    "locality_type": {
                        "type": "integer",
                        "id": "http://jsonschema.net/residential_address/locality_type",
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
                "id": "http://jsonschema.net/blood_type_info",
                "description": "Данные группы крови и резус-фактора пациентки",
                "items": {
                    "type": "object",
                    "description": "Сведение о группе крови и резус-факторе",
                    "properties": {
                        "blood_type": {
                            "type": "string",
                            "id": "http://jsonschema.net/blood_type/blood_type",
                            "description": "Код группы крови",
                            "enum": [
                                "0(I)Rh-",
                                "0(I)Rh+",
                                "A(II)Rh-",
                                "A(II)Rh+",
                                "B(III)Rh-",
                                "B(III)Rh+",
                                "AB(IV)Rh-",
                                "AB(IV)Rh+"
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
                "id": "http://jsonschema.net/allergies_info",
                "description": "Данные аллергии пациентки",
                "items": {
                    "type": "object",
                    "description": "Сведение об аллергии",
                    "properties": {
                        "allergy_power": {
                            "type": "integer",
                            "id": "http://jsonschema.net/allergies_info/allergy_power",
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
                            "id": "http://jsonschema.net/allergies_info/substance",
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
                "id": "http://jsonschema.net/medicine_intolerance_info",
                "description": "Данные медицинской непереносимости",
                "items": {
                    "type": "object",
                    "description": "Сведение о медикаментозной непереносимости",
                    "properties": {
                        "medicine_intolerance__power": {
                            "type": "integer",
                            "id": "http://jsonschema.net/medicine_intolerance_info/medicine_intolerance__power",
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
                            "id": "http://jsonschema.net/medicine_intolerance_info/medicine_substance",
                            "description": "Вещество",
                            "maxLength": 128
                        }
                    },
                    "required": [
                        "medicine_intolerance__power",
                        "medicine_substance"
                    ]
                }
            },
            "patient_external_code": {
                "type": "string",
                "id": "http://jsonschema.net/patient_external_code",
                "description": "Идентификатор пациента во внешней учетной системе"
            },
        },
        "required": [
            "FIO",
            "birthday_date",
            "gender",
        ]
    },
]
