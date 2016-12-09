# coding: utf-8

concilium_data_1 = {
    "external_id": "qwerty_012345",
    "date": "2011-11-11",
    "hospital": "-1",
    "doctor": "-1",
    "doctors": [
        {
            "doctor": "-1",
            "doctor_hospital": "-1",
        },
        {
            "doctor": "-3",
            "opinion": u'Всё не так',
            "doctor_hospital": "-1",
        },
        {
            "doctor": "-4",
            "opinion": u'И всё не то',
            "doctor_hospital": "-1",
        },
        {
            "doctor": "999",
            "opinion": u'Когда твоя девушка больна',
            "doctor_hospital": "-2",
        },
    ],
    "patient_presence": True,
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
            "doctor": "-1",
            "doctor_hospital": "-1",
        },
        {
            "doctor": "-3",
            "doctor_hospital": "-1",
        },
        {
            "doctor": "-4",
            "opinion": u'Всё не так',
            "doctor_hospital": "-1",
        }
    ],
    # "patient_presence": True,
    "diagnosis": "Q00.0",
    "reason": "Больной заболел",
    "patient_condition": "Средненькое",
    "decision": "<p>spam</p><br /><bar>foo</bar> BAZ" * 1000
}