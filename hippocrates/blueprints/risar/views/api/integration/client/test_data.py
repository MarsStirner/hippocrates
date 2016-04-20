# coding: utf-8

test_client_data_1 = {
    "FIO": {
        "middlename": u'Интова2',
        "name": u'Тестовая интеграция',
        "surname": u'Интегра'
    },
    "birthday_date": '2016-01-01',
    "gender": 2,
    "document": {
        "document_type_code": 1,
        "document_series": '01 01',
        "document_number": '555000',
        "document_beg_date": '2016-01-01',
        "document_issuing_authority": 'UFMS'
    },
}

test_client_data_2 = {
    "FIO": {
        "name": u'Тестовая интеграция',
        "surname": u'Интегра'
    },
    "birthday_date": "1990-04-15",
    "SNILS": "12345678910",
    "gender": 2,
    "patient_external_code": "67193001",
    "document": {"document_type_code": 10,
                 "document_series": "55",
                 "document_number": "734533",
                 "document_beg_date": "2011-04-04",
                 "document_issuing_authority": "Саратовский ОВД красная 5"},
    "insurance_documents": [
        {"insurance_document_type": "3",
         "insurance_document_number": "15978645",
         "insurance_document_beg_date": "2015-04-06",
         "insurance_document_issuing_authority": "-1"},
        {"insurance_document_type": "6",
         "insurance_document_number": "000",
         "insurance_document_beg_date": "2015-04-06",
         "insurance_document_issuing_authority": "-1"}
    ],
    "residential_address": {
        "KLADR_locality": "6400000500000",
        "KLADR_street": "64000005000000300",
        "house": "5",
        "flat": "5",
        "locality_type": 1
    },
    "blood_type_info": [
        {
            "blood_type": "B(III)Rh-"
        }
    ],
    "allergies_info": [
        {
            "allergy_power": 4,
            "allergy_substance": "ромашка"
        }
    ],
    "medicine_intolerance_info": [
        {
          "medicine_intolerance_power": 4,
          "medicine_substance": "анальгетики"
        },
        # {
        #   "medicine_intolerance_power": 3,
        #   "medicine_substance": "анальгетики Б"
        # }
    ]
}
