# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class OrgDepartmentSchema(Schema):
    """
    Схемы для проверки валидности данных организаций и лпу
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "object",
        "id": "organization_department",
        "description": "Подразделение ЛПУ",
        "properties": {
            "organisation_id":{
                "type": "string",
                "description": "Идентификатор организации (ЛПУ)"
            },
            "parent_department":{
                "type": "string",
                "description": "Идентификатор вышестоящего подразделения"
            },
            "regionalCode":{
                "type": "string",
                "description": "Уникальный идентификатор подразделения"
            },
            "TFOMSCode":{
                "type": "string",
                "id": "organization/TFOMSCode",
                "description": "ТФОМС код подразделения"
            },
            "name":{
                "type": "string",
                "description": "Наименование подразделения"
            },
            "address":{
                "type": "string",
                "description": "Адрес подразделения"
            },
            "type":{
                "type": "integer",
                "description": "Код типа подразделения"
            }
        },
        "required": ["organisation_id", "regionalCode", "name", "address"]
    }]
