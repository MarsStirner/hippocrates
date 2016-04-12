#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

test_puerpera_data = {
    "external_id": "12345",
    # "exam_puerpera_id": "",
    "date": "2016-04-01",  # *
    "date_of_childbirth": "2016-11-01",  # *
    "hospital": "-1",  # *
    "doctor": "22",  # *
    "time_since_childbirth": 1,
    "complaints": ["02", "04"],  # * Жалобы ["01", "02", "03", "04", "05"]
    "nipples": ["01"],  # Состояние сосков ["01", "02"]
    "secretion": ["01"],  # Выделения ["01", "02", "03"]
    "breast": ["02", "04"],  # * Молочные железы ["01", "02", "03", "04", "05"]
    "lactation": "01",  # Лактация ["01", "02"]
    "uterus": "02",  # Состояние матки ["01", ..., "05"]
    "scar": "01",  # Состояние послеоперационного рубца ["01", "02"]
    "state": "tajeloe",  # * Общ. состояние ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
    "ad_right_high": 120,  # *
    "ad_left_high": 120,  # *
    "ad_right_low": 80,  # *
    "ad_left_low": 80,  # *
    "veins": "noma",  # Общ. состояние ["poverhnostnyjvarikoz", "varikoznoerassirenieven", "noma"]
    "diagnosis": "A01",  # * Основной диагноз
    "contraception_recommendations": "01",  # Рекомендации по контрацепции ["01", ..., "04"]
    # "treatment": "",  # Лечение
    # "recommendations": "",  # Рекомендации
}
