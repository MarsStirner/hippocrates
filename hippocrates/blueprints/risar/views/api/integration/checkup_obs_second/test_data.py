#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

obs_second_data = {
    "external_id": "1234567",
    # "exam_obs_id": "",
    "dynamic_monitoring": {
        "date": "2016-10-09",  # *
        "hospital": "-1",  # *
        "doctor": "22",  # *
        "ad_right_high": 120,  # *
        "ad_left_high": 120,  # *
        "ad_right_low": 80,  # *
        "ad_left_low": 80,  # *
        "weight": 51,  # *
    },
    "somatic_status": {
        "state": "tajeloe",  # * Общ. состояние ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
        "complaints": ["moving", "golovnaabol_"],  # * Жалобы ["epigastrii", "golovnaabol_", "moving", "net", "oteki", "rvota", "tosnota", "zrenie"]
        "skin": [],  # * Кожа ["naliciekrovoizlianij", "naliciesypi", "obycnojokraskiivlajnosticistaa", "povysennojvlajnosti", "suhaa"]
        "lymph": [],  # * Лимфоузлы ["boleznennye", "neboleznennye", "nepal_piruutsa", "neuvelicennye", "pal_piruutsa", "uvelicennye"]
        "breast": [],  # * Молочные железы ["bezpatologiceskihizmenenij", "mestnoeuplotnenie", "nagrubanie", "pokrasnenie", "tresinysoskov"]
        "heart_tones": [],  # * Тоны сердца ["akzentIItona", "aritmicnye", "asnye", "gluhie", "prigluseny", "proslusivautsa", "ritmicnye"]
        "nipples": [],  # * Состояние сосков ["norma", "tresiny", "vospalenie"]
        "respiratory": [],  # * Органы дыхания ["dyhaniejestkoe", "dyhanievezikularnoe", "hripyotsutstvuut", "hripysuhie", "hripyvlajnye"]
        "abdomen": [],  # * Органы брюшной полости ["jivotmagkijbezboleznennyj", "jivotnaprajennyj", "jivotuvelicenzascetberemennojmatki"]
        "liver": [],  # * Печень ["nepal_piruetsa","uvelicena"]
        "edema": u"Средние",  #  "Отёки"
        "bowel_and_bladder_habits": "",  # Физиологические отправления",
    },
    "obstetric_status": {  # Акушерский статус",
        "abdominal_circumference": 65,  # Окружность живота"
        # "fundal_height": None,  # Высота стояния дна матки"
        "uterus_state": "normal_nyjtonus",  # Состояние матки ["gipertonus", "normal_nyjtonus"]
        "first_fetal_movement": "2016-03-12",  # Первое шевеление плода (дата)
        "fetal_movements": "",  # Шевеление
    },
    "fetus": [  # Плод
        {
            "fetus_lie": "prodol_noe",  # Положение плода ["kosoe", "poperecnoe", "prodol_noe"]
            "fetus_position": "vtoraa",  # Позиция плода ["pervaa", "vtoraa"]
            "fetus_type": "perednij",  # Вид плода ["perednij", "zadnij"]
            "fetus_presentation": "zatylocnoepredlejanie",  # Предлежащая часть плода ["cistoagodicnoepredlejanie", "golovnoepredlejanie", "lizevoepredlejanie", "lobnoepredlejanie", "nojnoepredlejanie", "perednegolovnoepredlejanie", "smesannoeagodicnoepredlejanie", "tazovoepredlejanie", "zatylocnoepredlejanie"]
            "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heart_rate": 121,  # ЧСС плода
            # "intrauterine_growth_retardation": "otsutstvuet",  # Задержка в развитии плода ["1-2nedeli", "4_and_more", ">3nedel_", "otsutstvuet"]
            # "ctg_data": {
            #     "fhr": "",  # Базальный ритм
            #     "fhr_variability_amp": "",  # Вариабельность (амплитуда) []
            #     "fhr_variability_freq": "",  # Вариабельность (частота в минуту) []
            #     "fhr_acceleration": "",  # Акселерации за 30 минут []
            #     "fhr_deceleration": "",  # Децелерации за 30 минут []
            # }
        },
        {
            "fetus_lie": "kosoe",  # Положение плода ["kosoe", "poperecnoe", "prodol_noe"]
            "fetus_position": "pervaa",  # Позиция плода ["pervaa", "vtoraa"]
            "fetus_type": "zadnij",  # Вид плода ["perednij", "zadnij"]
            "fetus_presentation": "cistoagodicnoepredlejanie",  # Предлежащая часть плода ["cistoagodicnoepredlejanie", "golovnoepredlejanie", "lizevoepredlejanie", "lobnoepredlejanie", "nojnoepredlejanie", "perednegolovnoepredlejanie", "smesannoeagodicnoepredlejanie", "tazovoepredlejanie", "zatylocnoepredlejanie"]
            "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heart_rate": 120,  # ЧСС плода
            # "intrauterine_growth_retardation": "otsutstvuet",  # Задержка в развитии плода ["1-2nedeli", "4_and_more", ">3nedel_", "otsutstvuet"]
            "ctg_data": {
                "fhr": "04",  # * Базальный ритм ["04", "03", "02", "01"]
                "fhr_variability_amp": "03",  # * Вариабельность (амплитуда) ["03", "02", "01"]
                "fhr_variability_freq": "02",  # * Вариабельность (частота в минуту) ["03", "02", "01"]
                "fhr_acceleration": "01",  # * Акселерации за 30 минут ["03", "02", "01"]
                "fhr_deceleration": "02",  # * Децелерации за 30 минут ["03", "02", "01"]
            }
        },
    ],
    "vaginal_examination": {  # Влагалищное исследование
        "vagina": "svobodnoe",  # * Влагалище ["svobodnoe", "uzkoe"]
        "cervix": "koniceskaacistaa",
    # * Шейка матки ["koniceskaacistaa", "koniceskaaerozirovannaa", "zilindriceskaacistaa", "zilindriceskaaerozirovanaa"]
        # "cervix_length": None,  # Длина шейки матки ["bolee2sm", "menee1sm", "menee2smnobolee1sm"]
        # "cervical_canal": None,  # Цервикальный канал ["narujnyjzevprohodimdla1poperecnogopal_za", "narujnyjzevzakryt", "vnutrennijzevpriotkryt"]
        # "cervix_consistency": None,  # Консистенция шейки матки ["magkaa", "plotnaa", "razmagcennaa"]
        # "cervix_position": None,  # Позиция шейки матки ["kperediotprovodnoj", "kzadiotprovodnojosi", "poprovodnojositaza"]
        # "cervix_maturity": None,  # Зрелость шейки матки ["nezrelaa", "sozrevausaa", "zrelaa"]
        # "body_of_uterus": [],  # Тело матки ["bezboleznennopripal_pazii", "boleznennopripal_pazii", "magkovatojkonsistenzii", "nepodvijno", "podvijno"]
        # "adnexa": None,  # Придатки ["bezosobennostej", "uveliceny"]
        # "specialities": "",  # Особенности
        # "vulva": "",  # Наружные половые органы
        "parametrium": 'plotnoe',  # Околоматочное пространство
        # "vaginal_smear": False,  # Отделяемое из влагалища взято на анализ
        # "cervical_canal_smear": False,  # Отделяемое из цервикального канала взято на анализ
        # "onco_smear": False,  # Мазок на онкоцитологию взято на анализ
        # "urethra_smear": False,  # Отделяемое и при наличии данных з уретры взято на анализ
    },
    "medical_report": {  # Заключение
        "pregnancy_week": 07,  # * Беременность (недель)
        "next_visit_date": "2016-04-15",  # * Плановая дата следующей явки
        "pregnancy_continuation": False,  # * Возможность сохранения беременности
        "abortion_refusal": True,  # * Отказ от прерывания
        # "working_conditions": "",  # Изменение условий труда ["osvobojdenieotnocnyhsmen", "vsmenerabotynenujdaetsa"]
        "diagnosis_osn": {      # Основной диагноз
            "MKB": "Z34.0",
            "descr": "Описание основного диагноза",
        },
        "diagnosis_sop": [
            {     # Диагноз сопутствующий
                "MKB": "G01",
                "descr": "Описание сопутствующего диагноза",
            }
        ],
        "diagnosis_osl": [
            {     # Диагноз осложнения
                "MKB": "H01",
                "descr": "Описание осложнения диагноза",
            }, {
                "MKB": "H02",
                "descr": "Описание осложнения диагноза",
            }
        ],
        # "recommendations": "",  # Рекомендации
        # "notes": "",  # Примечания
        # "vitaminization": "",  # Витаминизация
        # "nutrition": "",  # Коррекция питания
        # "treatment": "",  # Лечение
    }
}


ticket25_data = {
    "date_open": "2016-11-26",
    "doctor": "999",
    "hospital": "-2",
    "visit_dates": [
        "2016-11-23"
    ],
    "diagnosis": "O15.0",
    "reason": "B00",
    "trauma": "01",
    "visit_type": "1",
    "disease_character": "2",
    "disease_outcome": "improvement",
    "medical_care": "3",
    "medical_care_profile": "2",
    "medical_care_place": "ambulatorno",
    "medical_care_emergency": True,
    "finished_treatment": "1",
    "treatment_result": "01",
    "initial_treatment": "2",
    "payment": "4",
    "medical_services": [
        {
            "medical_service": "00000023",
            "medical_service_doctor": "999",
            "medical_service_quantity": "5"
        }
    ],
    "operations": [
        {
            "operation_code": "00000023",
            "operation_doctor": "999",
            "operation_anesthesia": "1",
            "operation_equipment": "1"
        }
    ],
    "manipulations": [
        {
            "manipulation_doctor": "999",
            "manipulation_quantity": 3,
            "manipulation": "A16.06.016.005"
        }
    ],
    "sick_leaves": [
        {
            "sick_leave_reason": "1",
            "sick_leave_date_open": "2016-11-26",
            "sick_leave_type": "2",
            "sick_leave_date_close": "2016-11-26"
        }
    ],
}
