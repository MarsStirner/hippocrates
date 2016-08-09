#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.views.api.integration.schemas import Schema


class ErrandSchema(Schema):
    """
    Схемы для проверки валидности данных поручения
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "errand",
            "description": "Поручение",
            "type": "object",
            "properties": {
                "status": {
                    "description": "Статус поручения, справочник rbErrandStatus",
                    "type": "string"
                },
                "execution_date": {
                    "description": "Фактическая дата исполнения",
                    "type": "string",
                    "format": "date"
                },
                "execution_comment": {
                    "description": "Текст ответа на поручение",
                    "type": "string"
                },
                "communication": {
                    "description": "Контактные данные автора поручения",
                    "type": "string"
                },
                "attached_files": {
                    "description": "Файлы, относящиеся к поручению",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "description": "id прикрепления файла",
                                "type": "string"
                            },
                            "name": {
                                "description": "Название файла",
                                "type": "string"
                            },
                            "url": {
                                "description": "Ссылка на скачивание",
                                "type": "string"
                            },
                            "comment": {
                                "description": "Комментарий",
                                "type": "string"
                            },
                            "doctor_code": {
                                "description": "Код пользователя хозяина файла",
                                "type": "string"
                            },
                            "hospital_code": {
                                "description": "Код ЛПУ пользователя хозяина файла",
                                "type": "string"
                            },
                            "attach_date": {
                                "description": "Дата прикрепления",
                                "type": "string",
                                "format": "date"
                            },
                            "mimetype": {
                                "description": "MIME type файла",
                                "type": "string"
                            }
                        }
                    },
                    "minItems": 0
                }
            }
        }
    ]


class ErrandListSchema(Schema):
    """
    Схемы для проверки валидности данных списка поручений
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "errands_list",
            "description": "Список поручений",
            "type": "array",
            "items": {
                "description": "Поручение",
                "type": "object",
                "properties": {
                    "errand_id": {
                        "description": "id поручения",
                        "type": "string"
                    },
                    "hospital": {
                        "description": "ЛПУ (код ЛПУ)",
                        "type": "string"
                    },
                    "doctor": {
                        "description": "Врач автор поручения (код врача)",
                        "type": "string"
                    },
                    "communication": {
                        "description": "Контактные данные автора поручения",
                        "type": "string"
                    },
                    "date": {
                        "description": "Плановая дата выполнения",
                        "type": "string",
                        "format": "date"
                    },
                    "comment": {
                        "description": "Текст поручения",
                        "type": "string"
                    },
                    "execution_hospital": {
                        "description": "ЛПУ исполнения (код ЛПУ)",
                        "type": "string"
                    },
                    "execution_doctor": {
                        "description": "Врач исполнитель (код врача)",
                        "type": "string"
                    },
                    "status": {
                        "description": "Статус поручения, справочник rbErrandStatus",
                        "type": "string"
                    },
                    "execution_date": {
                        "description": "Фактическая дата выполнения",
                        "type": "string",
                        "format": "date"
                    },
                    "execution_comment": {
                        "description": "Текст ответа на поручения",
                        "type": "string"
                    },
                    "attached_files": {
                        "description": "Файлы, относящиеся к поручению",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "description": "id прикрепления файла",
                                    "type": "string"
                                },
                                "name": {
                                    "description": "Название файла",
                                    "type": "string"
                                },
                                "url": {
                                    "description": "Ссылка на скачивание",
                                    "type": "string"
                                },
                                "comment": {
                                    "description": "Комментарий",
                                    "type": "string"
                                },
                                "doctor_code": {
                                    "description": "Код пользователя хозяина файла",
                                    "type": "string"
                                },
                                "hospital_code": {
                                    "description": "Код ЛПУ пользователя хозяина файла",
                                    "type": "string"
                                },
                                "attach_date": {
                                    "description": "Дата прикрепления",
                                    "type": "string",
                                    "format": "date"
                                },
                                "mimetype": {
                                    "description": "MIME type файла",
                                    "type": "string"
                                }
                            }
                        },
                        "minItems": 0
                    }
                }
            },
            "minItems": 0
        }
    ]
