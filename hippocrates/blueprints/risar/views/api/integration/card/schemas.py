# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class CardSchema(Schema):
    """
    Схемы для проверки валидности данных карты случая
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "card_schema",
        "id": "card_schema",
        "type": "object",
        "description": "Схема, описывающая данные индивидуальной карты беременной",
        "properties": {
            "client_id": {
                "id": "card_register_schema/client_id",
                "type": "string",
                "description": "Идентификатор пациента в БАРС.МР"
            },
            "card_set_date": {
                "type": "string",
                "id": "card_change_schema/card_set_date",
                "description": "Дата постановки на учёт"
            },
            "card_doctor": {
                "type": "string",
                "id": "card_change_schema/card_doctor",
                "description": "Код врача, поставившего пациентку на учёт"
            },
            "card_LPU": {
                "type": "string",
                "id": "card_change_schema/card_LPU",
                "description": "Код ЛПУ постановки на учёт в соответствии с классификатором f003"
            }
        },
        "required": ["client_id", "card_set_date", "card_doctor", "card_LPU"]
    }]