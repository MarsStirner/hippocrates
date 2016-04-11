#! coding:utf-8
"""


@author: BARS Group
@date: 06.04.2016

"""

test_pc_data = {
    "external_id": "12345",
    # "exam_obs_id": "",
    "general_info": {
        "date": "2016-03-31",  # *
        "hospital": "-1",  # *
        "doctor": "22",  # *
        "height": 120,  # *
        "weight": 120  # *
    },
    "somatic_status": {
        "state": "tajeloe",  # * Общ. состояние ["srednejtajesti", "tajeloe", "udovletvoritel_noe"]
        "subcutaneous_fat": "",  # * Подкожно жир. клетчатка ["izbytocnorazvita", "nedostatocnorazvita", "umerennorazvita"]
        "tongue": ["vlajnyj"],  # * Язык ["01", "02", "03", "04", "vlajnyj"]
        "complaints": ["moving", "golovnaabol_"],  # * Жалобы ["epigastrii", "golovnaabol_", "moving", "net", "oteki", "rvota", "tosnota", "zrenie"]
        "skin": [],  # * Кожа ["naliciekrovoizlianij", "naliciesypi", "obycnojokraskiivlajnosticistaa", "povysennojvlajnosti", "suhaa"]
        "lymph": [],  # * Лимфоузлы ["boleznennye", "neboleznennye", "nepal_piruutsa", "neuvelicennye", "pal_piruutsa", "uvelicennye"]
        "breast": [],  # * Молочные железы ["bezpatologiceskihizmenenij", "mestnoeuplotnenie", "nagrubanie", "pokrasnenie", "tresinysoskov"]
        "heart_tones": [],  # * Тоны сердца ["akzentIItona", "aritmicnye", "asnye", "gluhie", "prigluseny", "proslusivautsa", "ritmicnye"]
        "pulse": ["defizitpul_sa"],  # * Пульс ["defizitpul_sa", "udovletvoritel_nogonapolnenia"]
        "nipples": [],  # * Состояние сосков ["norma", "tresiny", "vospalenie"]
        "mouth": "",  # * Полость рта ["nujdaetsavsanazii", "sanirovana"]
        "respiratory": [],  # * Органы дыхания ["dyhaniejestkoe", "dyhanievezikularnoe", "hripyotsutstvuut", "hripysuhie", "hripyvlajnye"]
        "abdomen": [],  # * Органы брюшной полости ["jivotmagkijbezboleznennyj", "jivotnaprajennyj", "jivotuvelicenzascetberemennojmatki"]
        "liver": [],  # * Печень ["nepal_piruetsa","uvelicena"]
        "urinoexcretory": [],  # * Мочевыводящая система ["moceispuskanieucasennoe", "moceispuskanievnorme", "СindromPasternazkogo"]
        "ad_right_high": 0,  # *
        "ad_left_high": 0,  # *
        "ad_right_low": 0,  # *
        "ad_left_low": 0,  # *
        "edema": u"Средние",  #  "Отёки"
        "veins": "",  # * Состояние вен ["noma", "poverhnostnyjvarikoz", "varikoznoerassirenieven"]
        "bowel_and_bladder_habits": "",  # Физиологические отправления",
        "heart_rate": 70  # *
    },
    "obstetric_status": {  # Акушерский статус",
        # "horiz_diagonal": None,  # Горизонтальная диагональ"
        # "vert_diagonal": None,  # Вертикальная диагональ"
        # "abdominal_circumference": None,  # Окружность живота"
        # "fundal_height": None,  # Высота стояния дна матки"
        "uterus_state": "",  # * Состояние матки ["gipertonus", "normal_nyjtonus"]
        "dssp": 0,  # * Ds.SP
        "dscr": 0,  # * Ds.Cr
        "dstr": 0,  # * Ds.Tr
        "cext": 0,  # * C.Ext
        # "cdiag": None,  # C.Diag
        # "cvera": None,  # C.Vera
        "soloviev_index": 0,  # * Индекс Соловьёва
        # "pelvis_narrowness": None,  # Степень сужения таза ["IIIsteen_", "IIstepen_", "IVstepen_", "Istepen_", "norma"]
        # "pelvis_form": None,  # Форма таза ["normal_nyj", "obseravnomernosujennyj", "obsesujennyjploskij", "ploskorahiticeskij", "poperecnosujennyj", "prostojploskij"]
    },
    "fetus": [  # Плод
        {
            "fetus_lie": "prodol_noe",  # Положение плода ["kosoe", "poperecnoe", "prodol_noe"]
            "fetus_position": "vtoraa",  # Позиция плода ["pervaa", "vtoraa"]
            "fetus_type": "perednij",  # Вид плода ["perednij", "zadnij"]
            "fetus_presentation": "zatylocnoepredlejanie",  # Предлежащая часть плода ["cistoagodicnoepredlejanie", "golovnoepredlejanie", "lizevoepredlejanie", "lobnoepredlejanie", "nojnoepredlejanie", "perednegolovnoepredlejanie", "smesannoeagodicnoepredlejanie", "tazovoepredlejanie", "zatylocnoepredlejanie"]
            # "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heartbeat": "ritmicnoe",  # Сердцебиение плода ["asnoe", "ritmicnoe"]
            "fetus_heart_rate": 121  # ЧСС плода
        },
        # {
        #     "fetus_lie": "kosoe",  # Положение плода ["kosoe", "poperecnoe", "prodol_noe"]
        #     "fetus_position": "vtoraa",  # Позиция плода ["pervaa", "vtoraa"]
        #     "fetus_type": "",  # Вид плода ["perednij", "zadnij"]
        #     "fetus_presentation": "golovnoepredlejanie",  # Предлежащая часть плода ["cistoagodicnoepredlejanie", "golovnoepredlejanie", "lizevoepredlejanie", "lobnoepredlejanie", "nojnoepredlejanie", "perednegolovnoepredlejanie", "smesannoeagodicnoepredlejanie", "tazovoepredlejanie", "zatylocnoepredlejanie"]
        #     # "fetus_heartbeat": ["ritmicnoe"],  # Сердцебиение плода ["asnoe", "ritmicnoe"]
        #     "fetus_heartbeat": "asnoe",  # Сердцебиение плода ["asnoe", "ritmicnoe"]
        #     "fetus_heart_rate": 121  # ЧСС плода
        # }
    ],
    "vaginal_examination": {  # Влагалищное исследование
        "vagina": "",  # * Влагалище ["svobodnoe", "uzkoe"]
        "cervix": "",  # * Шейка матки ["koniceskaacistaa", "koniceskaaerozirovannaa", "zilindriceskaacistaa", "zilindriceskaaerozirovanaa"]
        # "cervix_length": None,  # Длина шейки матки ["bolee2sm", "menee1sm", "menee2smnobolee1sm"]
        # "cervical_canal": None,  # Цервикальный канал ["narujnyjzevprohodimdla1poperecnogopal_za", "narujnyjzevzakryt", "vnutrennijzevpriotkryt"]
        # "cervix_consistency": None,  # Консистенция шейки матки ["magkaa", "plotnaa", "razmagcennaa"]
        # "cervix_position": None,  # Позиция шейки матки ["kperediotprovodnoj", "kzadiotprovodnojosi", "poprovodnojositaza"]
        # "cervix_maturity": None,  # Зрелость шейки матки ["nezrelaa", "sozrevausaa", "zrelaa"]
        # "body_of_uterus": [],  # Тело матки ["bezboleznennopripal_pazii", "boleznennopripal_pazii", "magkovatojkonsistenzii", "nepodvijno", "podvijno"]
        # "adnexa": None,  # Придатки ["bezosobennostej", "uveliceny"]
        # "specialities": "",  # Особенности
        # "vulva": "",  # Наружные половые органы
        # "parametrium": [],  # Околоматочное пространство ["", "", ""]
        # "vaginal_smear": False,  # Отделяемое из влагалища взято на анализ
        # "cervical_canal_smear": False,  # Отделяемое из цервикального канала взято на анализ
        # "onco_smear": False,  # Мазок на онкоцитологию взято на анализ
        # "urethra_smear": False,  # Отделяемое и при наличии данных з уретры взято на анализ
    },
    "medical_report": {  # Заключение
        "pregnancy_week": 12,  # * Беременность (недель)
        "next_visit_date": "2016-04-15",  # * Плановая дата следующей явки
        "pregnancy_continuation": True,  # * Возможность сохранения беременности
        "abortion_refusal": True,  # * Отказ от прерывания
        # "working_conditions": "",  # Изменение условий труда ["osvobojdenieotnocnyhsmen", "vsmenerabotynenujdaetsa"]
        "diagnosis_osn": "A03",  # Основной диагноз
        # "diagnosis_sop": [],  # Диагноз сопутствующий
        # "diagnosis_osl": [],  # Диагноз осложнения
        # "recommendations": "",  # Рекомендации
        # "notes": "",  # Примечания
    }
}
