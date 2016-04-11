#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

test_obs_second_data = {
    "external_id": "12345",
    # "exam_obs_id": "",
    "dynamic_monitoring": {
        "date": "2016-04-01",  # *
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
            # "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heartbeat": "ritmicnoe",  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heart_rate": 121,  # ЧСС плода
            "intrauterine_growth_retardation": "otsutstvuet",  # Задержка в развитии плода ["1-2nedeli", "4_and_more", ">3nedel_", "otsutstvuet"]
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
            # "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heartbeat": "asnoe",  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heart_rate": 120,  # ЧСС плода
            "intrauterine_growth_retardation": "otsutstvuet",  # Задержка в развитии плода ["1-2nedeli", "4_and_more", ">3nedel_", "otsutstvuet"]
            "ctg_data": {
                "fhr": "04",  # * Базальный ритм ["04", "03", "02", "01"]
                "fhr_variability_amp": "03",  # * Вариабельность (амплитуда) ["03", "02", "01"]
                "fhr_variability_freq": "02",  # * Вариабельность (частота в минуту) ["03", "02", "01"]
                "fhr_acceleration": "01",  # * Акселерации за 30 минут ["03", "02", "01"]
                "fhr_deceleration": "02",  # * Децелерации за 30 минут ["03", "02", "01"]
            }
        },
    ],
    "medical_report": {  # Заключение
        "pregnancy_week": 07,  # * Беременность (недель)
        "next_visit_date": "2016-04-15",  # * Плановая дата следующей явки
        "pregnancy_continuation": True,  # * Возможность сохранения беременности
        "abortion_refusal": True,  # * Отказ от прерывания
        # "working_conditions": "",  # Изменение условий труда ["osvobojdenieotnocnyhsmen", "vsmenerabotynenujdaetsa"]
        "diagnosis_osn": "A01",  # Основной диагноз
        "diagnosis_sop": ["Z34.0"],  # Диагноз сопутствующий
        # "diagnosis_osl": [],  # Диагноз осложнения
        # "recommendations": "",  # Рекомендации
        # "notes": "",  # Примечания
        # "vitaminization": "",  # Витаминизация
        # "nutrition": "",  # Коррекция питания
        # "treatment": "",  # Лечение
    }
}
