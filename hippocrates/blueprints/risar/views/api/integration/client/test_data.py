#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

test_client_data_1 = {
    "FIO": {
        # "middlename": '',
        "name": u'Тестовая интеграция',
        "surname": u'Интегра'
    },
    "birthday_date": '2016-01-01',
    "SNILS": '1234567891011',
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
    "birthday_date": "1990-04-15",
    "SNILS": "           ",
    "gender": 2,
    "patient_external_code": "67193001",
    "FIO": {"middlename": "Олеговна",
            "name": "Татьяна",
            "surname": "Первая"},
    "document": {"document_type_code": 3,  # 2
                 "document_series": "12 12",
                 "document_number": "734533",
                 "document_beg_date": "2011-04-04",
                 "document_issuing_authority": "Саратовский ОВД красная 5"},
    "insurance_documents": [
        {"insurance_document_type": "3",
         "insurance_document_number": "15978645",
         "insurance_document_beg_date": "2015-04-06",
         "insurance_document_issuing_authority": "64005"}
    ],
    "residential_address": {
        "KLADR_locality": "6400000500000",
        "KLADR_street": "64000005000000300",
        "house": "5",
        "flat": "5",
        "locality_type": 1
    }
}

test_client_data_3 = {
    "birthday_date": "1986-01-26",
    "SNILS": "           ",
    "gender": 2,
    "patient_external_code": "65947953",
    "FIO": {
        "middlename": "Карповна",
        "name": "Карпина",
        "surname": "Карпова"},
    "document": {
        "document_type_code": 2,
        "document_series": "45 78",
        "document_number": "478787",
        "document_beg_date": "2016-02-01",
        "document_issuing_authority": " "
    },
    "insurance_documents": [
        {"insurance_document_type": "1",
         "insurance_document_series": " ",
         "insurance_document_number": "6450930828052233",
         "insurance_document_beg_date": "2013-09-06",
         "insurance_document_issuing_authority": "64005"}],
    "residential_address": {
        "KLADR_locality": "1600000100000",
        "KLADR_street": "16000001000001500",
        "house": "12", "flat": "25",
        "locality_type": 1
    }
}
