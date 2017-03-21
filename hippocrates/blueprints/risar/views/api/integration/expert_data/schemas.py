#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class ExpertDataSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema",
            "type": "object",
            "id": "expert_data",
            "properties": {
                "risk_degree": {
                    "type": "string",
                    "id": "expert_data/risk_degree",
                    "description": "Степень перинатального риска. Код из справочника степеней риска"
                },
                "risk_diagnosis": {
                    "type": "array",
                    "id": "expert_data/risk_diagnosis",
                    "description": "Рискообразующие диагнозы пациентки",
                    "items": {
                        "type": "object",
                        "description": "Список диагнозов",
                        "properties":
                            {
                                "diagnosis_code": {
                                    "type": "string",
                                    "id": "expert_data/risk_diagnosis/diagnosis_code",
                                    "description": "Код МКБ диагноза"
                                },
                                "diagnosis_name": {
                                    "type": "string",
                                    "id": "expert_data/risk_diagnosis/diagnosis_name",
                                    "description": "Наименование диагноза"
                                }
                            }
                    }
                },
                "established_preeclampsia": {
                    "type": "string",
                    "id": "expert_data/established_preeclampsia",
                    "description": "Степень установленной преэклампсии. Код из справочника степеней преэклампсии"
                },
                "suspected_preeclampsia": {
                    "type": "string",
                    "id": "expert_data/suspected_preeclampsia",
                    "description": "Степень подозреваемой преэклампсии. Код из справочника степеней преэклампсии"
                },
                "estimated_birth_date": {
                    "type": "string",
                    "id": "expert_data/estimated_birth_date",
                    "description": "Предполагаемая дата родов"
                },
                "risk_groups": {
                    "type": "array",
                    "id": "expert_data/risk_groups",
                    "description": "Группы риска пациентки",
                    "items": {
                        "type": "string",
                        "description": "Код группы риска. Код из справочника групп рисков"
                    }
                },
                "patology_groups": {
                    "type": "array",
                    "id": "expert_data/patology_groups",
                    "description": "Группы патологий пациентки",
                    "items": {
                        "type": "string",
                        "description": "Код группы риска. Код из справочника групп рисков"
                    }
                }
            }
        },
    ]


class ExpertDataTomskSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema",
            "type": "object",
            "id": "expert_data",
            "properties": {
                "risk_degree": {
                    "type": "string",
                    "id": "expert_data/risk_degree",
                    "description": "Степень перинатального риска. Код из справочника степеней риска"
                },
                "risk_diagnosis": {
                    "type": "array",
                    "id": "expert_data/risk_diagnosis",
                    "description": "Рискообразующие диагнозы пациентки",
                    "items": {
                        "type": "object",
                        "description": "Список диагнозов",
                        "properties": {
                            "diagnosis_code": {
                                "type": "string",
                                "id": "expert_data/risk_diagnosis/diagnosis_code",
                                "description": "Код МКБ диагноза"
                            },
                            "diagnosis_name": {
                                "type": "string",
                                "id": "expert_data/risk_diagnosis/diagnosis_name",
                                "description": "Наименование диагноза"
                            }
                        }
                    }
                },
                "established_preeclampsia": {
                    "type": "string",
                    "id": "expert_data/established_preeclampsia",
                    "description": "Степень установленной преэклампсии. Код из справочника степеней преэклампсии"
                },
                "suspected_preeclampsia": {
                    "type": "string",
                    "id": "expert_data/suspected_preeclampsia",
                    "description": "Степень подозреваемой преэклампсии. Код из справочника степеней преэклампсии"
                },
                "estimated_birth_date": {
                    "type": "string",
                    "id": "expert_data/estimated_birth_date",
                    "description": "Предполагаемая дата родов"
                },
                "risk_groups": {
                    "type": "array",
                    "id": "expert_data/risk_groups",
                    "description": "Группы риска пациентки",
                    "items": {
                        "type": "string",
                        "description": "Код группы риска. Код из справочника групп рисков"
                    }
                },
                "patology_groups": {
                    "type": "array",
                    "id": "expert_data/patology_groups",
                    "description": "Группы патологий пациентки",
                    "items": {
                        "type": "string",
                        "description": "Код группы риска. Код из справочника групп рисков"
                    }
                },
                "regional_scale_risks": {
                    "type": "array",
                    "id": "expert_data/regional_scale_risks",
                    "description": "Информация о степени риска пациентки по региональной шкале рисков",
                    "items": {
                        "type": "object",
                        "properties": {
                            "stage": {
                                "type": "string",
                                "id": "expert_data/regional_scale_risks/stage",
                                "description": "Этап определения риска, код по таблице rbRegionalRiskStage"
                            },
                            "factors": {
                                "type": "array",
                                "id": "expert_data/regional_scale_risks/factors",
                                "description": "Факторы, которые сработали на этапе, список кодов",
                                "items": {
                                    "type": "string",
                                    "description": "Код фактора по таблице rbRadzRiskFactor"
                                }
                            },
                            "sum": {
                                "type": "integer",
                                "id": "expert_data/regional_scale_risks/sum",
                                "description": "Сумма факторов на этапе"
                            }
                        }
                    }
                }
            }
        }
    ]
