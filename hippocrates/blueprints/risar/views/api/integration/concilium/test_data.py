# coding: utf-8

concilium_data_1 = {
    "external_id": "qwerty_012345",
    "date": "2011-11-11",
    "hospital": "-1",
    "doctor": "-1",
    "doctors": [
        {
            "doctor": "-1"
        },
        {
            "doctor": "-3"
        },
        {
            "doctor": "-4",
            "opinion": u'Всё не так'
        },
        {
            "doctor": "-5",
            "opinion": u'Долой этот консилиум'
        },
    ],
    "diagnosis": "Q00.0",
    "reason": "Больной заболел",
    "patient_condition": "Средненькое",
    "decision": "Будем лечить"
}

concilium_data_2 = {
    "external_id": "qwerty_012345",
    "date": "2011-11-11",
    "hospital": "-1",
    "doctor": "-1",
    "doctors": [
        {
            "doctor": "-1"
        },
        {
            "doctor": "-3",
        },
        {
            "doctor": "-4",
            "opinion": u'Всё не так'
        }
    ],
    "patient_presence": True,
    "diagnosis": "Q00.0",
    "reason": "Больной заболел",
    "patient_condition": "Средненькое",
    "decision": "<p>spam</p><br /><bar>foo</bar> BAZ" * 1000
}