#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

"""
Преобразующий схему паттерн:
[ ]+"(\w+)": \{\n[ ]+"descr\w+": "([А-я\w ,/<\(\)Ёё\-]+)"[\w ,\(\)\n":\d\-\[\]\|\^\$\?\+\\.\{\}A-Z]+([ ]+# "enum": \[\n([ ]+#[ ]+"([\-\w'\(\)._]+)"(,|)\n)+[ ]+# ]\n)*([ ]+# "enum": \[("([\-\w'\(\)._]+)"(, |))+]\n)*[ ]+\},\n
        "$1": "",  # $2 ["$5$9",]\n
"""


test_childbirth_data = {
    "general_info": {  # Общая информация
        "admission_date": "2016-04-14",  # Дата поступления
        "pregnancy_duration": 16,  # * Срок родоразрешения
        "delivery_date": "2016-04-14",  # * Дата родоразрешения
        "delivery_time": "13:30",  # * Время родоразрешения
        "maternity_hospital": "6202",  # * ЛПУ, принимавшее роды (код)
        "diagnosis_osn": "Z34.0",  # Основной диагноз, код диагноза по МКБ-10
        "diagnosis_sop": ["O30.2", "O42.0", "A00", "B05.0", "A04.3"],  # Диагноз сопутствующий (массив, код диагноза по МКБ-10)
        "diagnosis_osl": [],  # Диагноз осложнения (массив, код диагноза по МКБ-10)
        "pregnancy_speciality": "течение родовое",  # Особенности течения беременности
        "postnatal_speciality": "течение послеродовое",  # Особенности течения послеродового периода
        "help": "помощь",  # Оказанная помощь
        "pregnancy_final": "rodami",  # Исход беременности, справочник rbRisarPregnancy_Final ["rodami",]
        # "abortion": None,  # Вид аборта, справочник rbRisarAbort ["samoproizvol_nyj",]
        "maternity_hospital_doctor": "33",  # Лечащий врач роддома (код)
        "curation_hospital": "6202",  # ЛПУ курации новорождённого
    },
    "mother_death": {  # Информация о смерти матери
        "death": True,  # Смерть матери
        "reason_of_death": "не",  # * Причина смерти матери
        "death_date": "2016-04-07",  # * Дата смерти матери
        "death_time": "00:30",  # * Время смерти матери
        "pat_diagnosis_osn": "Z34.0",  # Основной патологоанатомический диагноз, код диагноза по МКБ-10
        "pat_diagnosis_sop": ["O30.2", "O42.0", "A00", "A04.3"],  # Диагноз сопутствующий (массив, код диагноза по МКБ-10)
        "pat_diagnosis_osl": ["B05.0"],  # Диагноз осложнения (массив, код диагноза по МКБ-10)
        "control_expert_conclusion": "лкккк",  # Заключение ЛКК
    },
    "complications": {  # Осложнения при родах
        "delivery_waters": "rannie",  # Излитие околоплодных вод, справочник rbRisarDelivery_Waters ["rannie",]
        "pre_birth_delivery_waters": True,  # Дородовое излитие вод
        "weakness": "pervicnaa",  # Слабость родовых сил, справочник rbRisarWeakness ["pervicnaa", "vtoricnaa"]
        "meconium_color": True,  # Мекониальная окраска амниотических вод
        "pathological_preliminary_period": True,  # Патологический прелиминарный период
        "abnormalities_of_labor": True,  # Аномалии родовой деятельности
        "chorioamnionitis": True,  # Хориоамнионит
        "perineal_tear": "02",  # Разрыв промежностей (степень) rbPerinealTear
        "eclampsia": "net",  # Нефропатия/эклампсия в родах, справочник rbRisarEclampsia ["net",]
        "funiculus": "vypadeniepupoviny",  # Патология пуповины, справочник rbRisarFuniculus ["zaputyvanieiuzelpupoviny",]
        "afterbirth": "giploplaziaplazenty",  # Патология плаценты, справочник rbRisarAfterbirth ["sosudistaapatologiaplazenty",]
        "anemia": True,  # Анемия после родов (Hb<110 г/л)
        "infections_during_delivery": "была",  # Инфекции в родах
        "infections_after_delivery": "осталась",  # Инфекции после родов
    },
    "manipulations": {  # Пособия и манипуляции при родах
        "caul": True,  # Вскрытие околоплодного пузыря
        "calfbed": True,  # Ручное обследование матки
        "perineotomy": "эпи",  # Эпизио/перинеотомия
        "secundines": True,  # Ручное выделение последа
        "other_manipulations": "манипул",  # Другие пособия и манипуляции
    },
    "operations": {  # Операции при родах
        "caesarean_section": "korporal_noe",  # Кесарево сечение, справочник rbRisarCaesarean_Section ["vn.m.segmente",]
        "obstetrical_forceps": "vyhodnye",  # Акушерские щипцы, справочник rbRisarObstetrical_Forceps ["vyhodnye",]
        "vacuum_extraction": True,  # Вакуум-экстракция
        "indication": "sostoronyploda",  # Показания к операции, справочник rbRisarIndication ["sostoronyploda",]
        "specialities": "особ",  # Особенности операции, справочник rbRisarSpecialities ["planovoe",]
        "anesthetization": "02",  # Обезболивание, справочник rbRisarAnesthetization ("01")
        "hysterectomy": "vpredelahdvuhsutokposlerodov",  # Гистерэктомия, справочник rbRisarHysterectomy ["vpredelahdvuhsutokposlerodov", "boleedvuhsutokposlerodov"]
        "complications": ["A00.1"],  # Осложнения при родах (массив, код диагноза по МКБ-10)
        "embryotomy": True,  # Плодоразрушающие операции
    },
    "kids": [  # Сведения о родившихся детях
        {
            "alive": True,  # * Живой
            "sex": 1,  # * Пол
            "weight": 1000,  # * Масса
            "length": 20,  # * Длина
            "date": "2016-04-14",  # * Дата рождения
            "time": "13:30",  # * Время рождения
            "maturity_rate": "nedonosennyj",  # Степень доношенности, справочник rbRisarMaturity_Rate ["perenosennyj",]
            "apgar_score_1": 2,  # Оценка по Апгар на 1 минуту
            "apgar_score_5": 3,  # Оценка по Апгар на 5 минуту
            "apgar_score_10": 4,  # Оценка по Апгар на 10 минуту
            "diseases": ["A00"],  # Заболевания новорождённого
            # "death_date": None,  # Дата смерти
            # "death_time": None,  # Время смерти
            # "death_reason": None,  # Причина смерти
        },
        # {
        #     "alive": True,  # * Живой
        #     "sex": 1,  # * Пол
        #     "weight": 1000,  # * Масса
        #     "length": 20,  # * Длина
        #     "date": "2016-04-14",  # * Дата рождения
        #     "time": "13:30",  # * Время рождения
        #     "maturity_rate": "nedonosennyj",  # Степень доношенности, справочник rbRisarMaturity_Rate ["perenosennyj",]
        #     "apgar_score_1": 2,  # Оценка по Апгар на 1 минуту
        #     "apgar_score_5": 3,  # Оценка по Апгар на 5 минуту
        #     "apgar_score_10": 4,  # Оценка по Апгар на 10 минуту
        #     # "death_date": None,  # Дата смерти
        #     # "death_time": None,  # Время смерти
        #     # "death_reason": None,  # Причина смерти
        # }
    ],
}
