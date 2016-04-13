# coding: utf-8

anamnesis_m_data = {
    "last_period_date": "2016-03-03",
    "marital_status": u"01"
}


anamnesis_m_data2 = {
    "education": "05",
    "work_group": "02",
    "professional_properties": "psychic_tension",
    "family_income": "02",
    "menstruation_start_age": "12",
    "menstruation_duration": "28",
    "menstruation_period": "5",
    "menstrual_disorder": False,
    "sex_life_age": 23,
    "fertilization_type": "01",
    "intrauterine_operation": False,
    "multiple_fetation": False,
    "infertility": {
        "infertility_occurence": True,
        "infertility_type": "01",
        "infetrility_duration": 2,
        "infertility_treatment": ["02", "03"],
        "infertility_causes": ["02", "03"]
    },
    "smoking": False,
    "alcohol": False,
    "toxic": True,
    "drugs": False,
    "contraception": ["1", "2"],
    "hereditary": ["11", "12"],
    "finished_diseases": u"краснуха",
    "current_diseases": ["O12.1", "O23.2"],
    "last_period_date": "2015-12-31",
    "preeclampsia_mother_sister": False,
    "marital_status": "03"
}


anamnesis_f_data = {
    "FIO": u"Иванов Андрей Петрович",
    "age": "35",
    "education": "03",
    "work_group": "01",
    "professional_properties": "dust",
    "telephone_number": "89342134590",
    "fluorography": u"Без особенностей",
    "hiv": False,
    "blood_type": "0(I)Rh-",
    "infertility": {
        "infertility_occurence": True,
        "infertility_type": "01",
        "infetrility_duration": 2,
        "infertility_treatment": ["02", "03"],
        "infertility_causes": ["02", "03"]
    },
    "smoking": False,
    "alcohol": False,
    "toxic": False,
    "drugs": False,
    "hereditary": ["01", "10"],
    "finished_diseases": u"Анемия",
    "current_diseases": u"Отсутствуют"
}


prev_preg_data10 = {
    "pregnancy_year": 1990,
    "pregnancy_result": "premature_birth_28-37",
    "gestational_age": 36,
    "preeclampsia": False,
    "after_birth_complications": ["O86.1", "O86.4"],
    "assistance_and_operations": ["03"],
    "pregnancy_pathologies": ["O32.3"],
    "birth_pathologies": ["O64.3", "O67.8"],
    "child_information": [
        {
            "is_alive": True,
            "weight": 3250,
            "abnormal_development": True,
            "neurological_disorders": False
        }
    ]
}


prev_preg_data11 = {
    "pregnancy_year": 1990,
    "pregnancy_result": "premature_birth_28-37",
    "gestational_age": 36,
    "preeclampsia": False,
    "after_birth_complications": ["O86.1", "O86.4"],
    "assistance_and_operations": ["01"],
    "pregnancy_pathologies": ["O32.3"],
    "birth_pathologies": ["O64.3", "O67.8"],
    "child_information": [
        {
            "is_alive": True,
            "weight": 3000,
            "abnormal_development": False,
            "neurological_disorders": False
        }
    ]
}


prev_preg_data20 = {
    "pregnancy_year": 1990,
    "pregnancy_result": "premature_birth_28-37",
    "gestational_age": 35,
    "preeclampsia": False,
    "after_birth_complications": ["O86.1", "O86.3"],
    "assistance_and_operations": ["03"],
    "pregnancy_pathologies": ["O32.3"],
    "birth_pathologies": ["O64.3", "O67.8"],
    "child_information": [
        {
            "is_alive": True,
            "weight": 3250,
            "abnormal_development": True,
            "neurological_disorders": False
        },
        {
            "is_alive": True,
            "weight": 3520,
            "abnormal_development": False,
            "neurological_disorders": False
        },
        {
            "is_alive": True,
            "weight": 3777,
            "abnormal_development": True,
            "neurological_disorders": True
        },
        {
            "is_alive": False,
            "weight": 3778,
            "abnormal_development": True,
            "neurological_disorders": True,
            "death_at": "01",
            "death_cause": u'н'
        }
    ]
}


prev_preg_data21 = {
    "pregnancy_year": 1990,
    "pregnancy_result": "premature_birth_28-37",
    "gestational_age": 35,
    "preeclampsia": False,
    "after_birth_complications": ["O86.1", "O86.3"],
    "assistance_and_operations": ["03"],
    "pregnancy_pathologies": ["O32.3"],
    "birth_pathologies": ["O64.3", "O67.8"],
    "child_information": [
        {
            "is_alive": True,
            "weight": 3250,
            "abnormal_development": True,
            "neurological_disorders": False
        },
        # {
        #     "is_alive": True,
        #     "weight": 3520,
        #     "abnormal_development": False,
        #     "neurological_disorders": False
        # },
        {
            "is_alive": True,
            "weight": 3777,
            "abnormal_development": True,
            "neurological_disorders": True
        },
        # {
        #     "is_alive": False,
        #     "weight": 3778,
        #     "abnormal_development": True,
        #     "neurological_disorders": True,
        #     "death_at": "01",
        #     "death_cause": u'н'
        # }
    ]
}
