# coding: utf-8


obs_gyn_data = {
    "external_id": "1234567",
    # "exam_gyn_id": "",
    "date": "2016-10-20",  # *
    "hospital": "-1",  # *
    "doctor": "-1",  # *
    "general_info": {
        "last_menstruation_date": '2016-10-07',
        'last_menstruation_features': 'ontime',
        'last_menstruation_character': ['blood_clot', 'excessive'],
        "medicament": 'bnbn',
        "shivers": True,
    },
    "medical_report": {  # Заключение
        "diagnosis_osn": "N80.1",  # Основной диагноз
        "diagnosis_sop": ["G01"],  # Диагноз сопутствующий
        "diagnosis_osl": ["H01", "H02"],  # Диагноз осложнения
        'encompassing_comments': 'vbnm',
        'encompassing_treatment': u'кенгш'
    },
    'objective': {
        'weight': 70,
        'temperature': 36.6,
        'AD_right_high': 120,
        'AD_left_low': 80,
        'skin': ['blue', 'naliciekrovoizlianij'],
        'stomach': ['painful', 'painless']
    }
}
