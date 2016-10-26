# coding: utf-8
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema


class CheckupGynSchema(Schema):
    """
    Схемы для проверки валидности данных гинекологического осмотра
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "gynecological_checkup",
            "description": "Гинекологический осмотр",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "date": {
                    "description": "Дата осмотра",
                    "type": "string",
                    "format": "date"
                },
                "hospital": {
                    "description": "ЛПУ осмотра (код)",
                    "type": "string"
                },
                "doctor": {
                    "description": "Врач (код)",
                    "type": "string"
                },
                "general_info": {
                    "description": "Общие данные осмотра",
                    "type": "object",
                    "properties": {
                        "last_menstruation_date": {
                            "description": "Дата последней менструации",
                            "type": "string",
                            "format": "date"
                        },
                        "last_menstruation_features": {
                            "description": "Особенности последней менструации, справочник rbRisarLastMenstruationFeatures",
                            "type": "string"
                        },
                        "last_menstruation_character": {
                            "description": "Характер последней менструации, массив, справочник rbRisarMenstruationCharacter",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "libido": {
                            "description": "Половое влечение, справочник rbRisarLibido",
                            "type": "string"
                        },
                        "intercourse_partner": {
                            "description": "Половой партнер, справочник rbRisarIntercoursePartner",
                            "type": "string"
                        },
                        "sexual_intercourse": {
                            "description": "Половой акт, массив, справочник rbRisarSexualIntercourse",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "contraception": {
                            "description": "Контрацепция, массив, справочник rbContraception",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "medicament": {
                            "description": "Принимаемые медикаменты",
                            "type": "string"
                        },
                        "pain_location": {
                            "description": "Локализация боли",
                            "type": "string"
                        },
                        "pain_how_long": {
                            "description": "Как давно",
                            "type": "string"
                        },
                        "pain_character": {
                            "description": "Характер боли, массив, справочник rbRisarPainCharacter",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "temperature_rise": {
                            "description": "Повышение температуры до",
                            "type": "number"
                        },
                        "shivers": {
                            "description": "Озноб",
                            "type": "boolean"
                        },
                        "menstrual_disorders": {
                            "description": "Нарушение характера менструаций, массив, справочник rbRisarMenstrualDisorders",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "discharge_consistency": {
                            "description": "Выделения.Консистенция, массив, справочник rbRisarDischargeConsistency",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "discharge_colour": {
                            "description": "Выделения.Цвет, справочник rbRisarDischargeColour",
                            "type": "string"
                        },
                        "discharge_quantity": {
                            "description": "Выделения.Количество, справочник rbRisarDischargeQuantity",
                            "type": "string"
                        },
                        "discharge_smell": {
                            "description": "Выделения.Запах, справочник rbRisarDischargeSmell",
                            "type": "string"
                        },
                        "itch_character": {
                            "description": "Зуд. Характер, массив, справочник rbRisarItchCharacter",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "itch_period": {
                            "description": "Зуд.Как давно",
                            "type": "string"
                        },
                        "pregnancy_failure": {
                            "description": "Отсутствие беременности",
                            "type": "boolean"
                        },
                        "pregnancy_failure_period": {
                            "description": "Срок отсутствия беременности",
                            "type": "string"
                        },
                        "engorged_breasts": {
                            "description": "Молочные железы.Нагрубание",
                            "type": "boolean"
                        },
                        "breasts_pain": {
                            "description": "Молочные железы.Боль",
                            "type": "string"
                        },
                        "breasts_induration": {
                            "description": "Молочные железы.Уплотнения",
                            "type": "string"
                        },
                        "nipples_discharge": {
                            "description": "Молочные железы.Выделения из сосков",
                            "type": "string"
                        },
                        "other_complaints": {
                            "description": "Другие жалобы",
                            "type": "string"
                        }
                    }
                },
                "objective": {
                    "description": "Объективный осмотр",
                    "type": "object",
                    "properties": {
                        "weight": {
                            "description": "Масса",
                            "type": "number"
                        },
                        "height": {
                            "description": "Рост",
                            "type": "number"
                        },
                        "temperature": {
                            "description": "Температура тела",
                            "type": "number"
                        },
                        "heart_rate": {
                            "description": "ЧСС",
                            "type": "integer"
                        },
                        "AD_right_high": {
                            "description": "АД правая рука верхнее",
                            "type": "integer"
                        },
                        "AD_right_low": {
                            "description": "АД правая рука нижнее",
                            "type": "integer"
                        },
                        "AD_left_high": {
                            "description": "АД левая рука верхнее",
                            "type": "integer"
                        },
                        "AD_left_low": {
                            "description": "АД левая рука нижнее",
                            "type": "integer"
                        },
                        "skin": {
                            "description": "Кожа, массив, справочник rbRisarSkin",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "mucous": {
                            "description": "Состояние слизистых, массив, справочник rbRisarMucous",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "lymph": {
                            "description": "Лимфоузлы, массив, справочник rbRisarLymph",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "subcutaneous_fat": {
                            "description": "Подкожно-жировая клетчатка, справочник rbRisarSubcutaneous_Fat",
                            "type": "string"
                        },
                        "breast": {
                            "description": "Молочные железы, массив, справочник rbRisarBreast",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "nipples": {
                            "description": "Состояние сосков, массив, справочник rbRisarNipples",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "stomach": {
                            "description": "Живот, массив, справочник rbRisarStomachGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "pilosis": {
                            "description": "Характер оволосения",
                            "type": "string"
                        },
                        "comments": {
                            "description": "Примечания",
                            "type": "string"
                        }
                    }
                },
                "vulva": {
                    "description": "Осмотр наружных половых органов",
                    "type": "object",
                    "properties": {
                        "vulva_pilosis": {
                            "description": "Наружные половые органы. Характер оволосения, справочник rbRisarVulvaPilosis",
                            "type": "string"
                        },
                        "groin_glands": {
                            "description": "Наружные половые органы.Региональные паховые лимфоузлы, справочник rbRisarGroinGlands",
                            "type": "string"
                        },
                        "vulva_skin": {
                            "description": "Наружные половые органы.Состояние кожи, массив, справочник rbRisarVulvaSkin",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "vulva_skin_adds": {
                            "description": "Наружные половые органы.Состояние кожи.Другое",
                            "type": "string"
                        },

                        "vulva_mucous": {
                            "description": "Наружные половые органы.Состояние слизистой, массив, справочник rbRisarMucous",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "vulva_mucous_adds": {
                            "description": "Наружные половые органы.Состояние слизистой.Другое",
                            "type": "string"
                        },
                        "vulva_germination": {
                            "description": "Степень развития наружных половых органов, справочник rbRisarVulvaGermination",
                            "type": "string"
                        },
                        "urethra": {
                            "description": "Наружные половые органы.Область уретры, справочник rbRisarUrethra",
                            "type": "string"
                        },
                        "urethra_adds": {
                            "description": "Наружные половые органы.Область уретры.Другое",
                            "type": "string"
                        },
                        "perianal_zona": {
                            "description": "Наружные половые органы.Перианальная область, массив, справочник rbRisarPerianalZona",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "vulva_discharge_consistency": {
                            "description": "Наружные половые органы.Консистенция выделений, массив, справочник rbRisarDischargeConsistency",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "vulva_discharge_colour": {
                            "description": "Наружные половые органы.Цвет выделений, справочник rbRisarDischargeColour",
                            "type": "string"
                        },
                        "vulva_discharge_quantity": {
                            "description": "Наружные половые органы.Количество выделений, справочник rbRisarDischargeQuantity",
                            "type": "string"
                        },
                        "vulva_discharge_smell": {
                            "description": "Наружные половые органы.Запах выделений, справочник rbRisarDischargeSmell",
                            "type": "string"
                        },
                        "vulva_comments": {
                            "description": "Наружные половые органы.Дополнительная информация",
                            "type": "string"
                        }
                    }
                },
                "mirrors": {
                    "description": "Осмотр в зеркалах",
                    "type": "object",
                    "properties": {
                        "vagina_mirrors_mirrors": {
                            "description": "Осмотр в зеркалах.Влагалище, справочник rbRisarVaginaGenVisit",
                            "type": "string"
                        },
                        "vagina_mirrors_adds": {
                            "description": "Осмотр в зеркалах.Влагалище.Другое",
                            "type": "string"
                        },
                        "vagina_paries_mirrors": {
                            "description": "Осмотр в зеркалах.Стенки влагалища, справочник rbRisarVaginaParies",
                            "type": "string"
                        },
                        "vagina_paries_mirrors_other": {
                            "description": "Осмотр в зеркалах.Стенки влагалища. Другое",
                            "type": "string"
                        },
                        "cervix_uteri_mirrors": {
                            "description": "Осмотр в зеркалах.Шейка матки, справочник rbRisarCervixUteri",
                            "type": "string"
                        },
                        "cervix_uteri_size_mirrors": {
                            "description": "Осмотр в зеркалах.Размеры шейки матки, справочник rbRisarCervixUteriSize",
                            "type": "string"
                        },
                        "cervix_uteri_shape_mirrors": {
                            "description": "Осмотр в зеркалах.Форма шейки матки, справочник rbRisarCervixUteriShape",
                            "type": "string"
                        },
                        "anabrosis_mirrors": {
                            "description": "Осмотр в зеркалах.Эрозия",
                            "type": "boolean"
                        },
                        "ectropion_mirrors": {
                            "description": "Осмотр в зеркалах.Эрозированный эктропион",
                            "type": "boolean"
                        },
                        "uterus_external_orifice_mirrors": {
                            "description": "Осмотр в зеркалах.Наружный зев, справочник rbRisarUterusExternalOrifice",
                            "type": "string"
                        },
                        "vaginal_fornix_mirrors": {
                            "description": "Осмотр в зеркалах.Своды влагалища, массив, справочник rbRisarVaginalFornix",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "vaginal_fornix_adds_mirrors": {
                            "description": "Осмотр в зеркалах.Своды влагалища.Другое",
                            "type": "string"
                        },
                        "discharge_consistency_mirrors": {
                            "description": "Осмотр в зеркалах.Выделения.Консистенция, массив, справочник rbRisarDischargeConsistency",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "discharge_colour_mirrors": {
                            "description": "Осмотр в зеркалах.Выделения.Цвет, справочник rbRisarDischargeColour",
                            "type": "string"
                        },
                        "discharge_quantity_mirrors": {
                            "description": "Осмотр в зеркалах.Выделения.Количество, справочник rbRisarDischargeQuantity",
                            "type": "string"
                        },
                        "discharge_smell_mirrors": {
                            "description": "Осмотр в зеркалах.Выделения.Запах, справочник rbRisarDischargeSmell",
                            "type": "string"
                        },
                        "comments_mirrors": {
                            "description": "Осмотр в зеркалах.Дополнительная информация",
                            "type": "string"
                        }
                    }
                },
                "bimanual": {
                    "description": "Бимануальное исследование",
                    "type": "object",
                    "properties": {
                        "bimanual_cervix_uteri": {
                            "description": "Бимануальное исследование. Шейка матки, справочник rbRisarCervixUteri",
                            "type": "string"
                        },
                        "bimanual_cervix_consistency": {
                            "description": "Бимануальное исследование. Консистенция шейки матки, справочник rbRisarCervix_Consistency",
                            "type": "string"
                        },
                        "bimanual_uterus_body": {
                            "description": "Бимануальное исследование. Тело матки, массив, справочник rbRisarUterusBodyGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "bimanual_body_of_womb_size": {
                            "description": "Бимануальное исследование. Размеры, справочник rbRisarBody_Of_Womb_Size",
                            "type": "string"
                        },
                        "bimanual_body_of_womb_enlarged": {
                            "description": "Бимануальное исследование. Размеры. Увеличены до",
                            "type": "string"
                        },
                        "bimanual_uteri_position": {
                            "description": "Бимануальное исследование. Положение, массив, справочник rbRisarUteriPositionGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "bimanual_ovary_right": {
                            "description": "Бимануальное исследование.Яичники справа, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "bimanual_ovary_right_oher": {
                            "description": "Бимануальное исследование. Яичники справа.Другое",
                            "type": "string"
                        },
                        "bimanual_ovary_left": {
                            "description": "Бимануальное исследование.Яичники слева, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "bimanual_ovary_left_oher": {
                            "description": "Бимануальное исследование. Яичники слева.Другое",
                            "type": "string"
                        },
                        "bimanual_uterine_tubes_right": {
                            "description": "Бимануальное исследование. Маточные трубы справа",
                            "type": "string"
                        },
                        "bimanual_uterine_tubes_left": {
                            "description": "Бимануальное исследование. Маточные трубы слева",
                            "type": "string"
                        },
                        "bimanual_vaginal_fornix": {
                            "description": "Бимануальное исследование. Своды влагалища, массив, справочник rbRisarVaginalFornix",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "bimanual_comments": {
                            "description": "Бимануальное исследование.Дополнительная информация",
                            "type": "string"
                        }
                    }
                },
                "rectovaginal": {
                    "description": "Ректовагинальное исследование",
                    "type": "object",
                    "properties": {
                        "rectovaginal_cervix_uteri": {
                            "description": "Ректовагинальное исследование. Шейка матки, справочник rbRisarCervixUteri",
                            "type": "string"
                        },
                        "rectovaginal_cervix_consistency": {
                            "description": "Ректовагинальное исследование. Консистенция шейки матки, справочник rbRisarCervix_Consistency",
                            "type": "string"
                        },
                        "rectovaginal_uterus_body": {
                            "description": "Ректовагинальное исследование. Тело матки, массив, справочник rbRisarUterusBodyGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_body_of_womb_size": {
                            "description": "Ректовагинальное исследование. Размеры, справочник rbRisarBody_Of_Womb_Size",
                            "type": "string"
                        },
                        "rectovaginal_body_of_womb_enlarged": {
                            "description": "Ректовагинальное исследование. Размеры. Увеличены до",
                            "type": "string"
                        },
                        "rectovaginal_uteri_position": {
                            "description": "Ректовагинальное исследование. Положение, массив, справочник rbRisarUteriPositionGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_parametrium": {
                            "description": "Ректовагинальное исследование. Параметрическая область широких связок матки, массив, справочник rbRisarParametrium1",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_parametrium_other": {
                            "description": "Ректовагинальное исследование. Параметрическая область широких связок матки. Другое",
                            "type": "string"
                        },
                        "rectovaginal_ovary_right": {
                            "description": "Ректовагинальное исследование.Яичники справа, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_ovary_right_oher": {
                            "description": "Ректовагинальное исследование. Яичники справа.Другое",
                            "type": "string"
                        },
                        "rectovaginal_ovary_left": {
                            "description": "Ректовагинальное исследование.Яичники слева, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_ovary_left_oher": {
                            "description": "Ректовагинальное исследование. Яичники слева.Другое",
                            "type": "string"
                        },
                        "rectovaginal_uterine_tubes_right": {
                            "description": "Ректовагинальное исследование.Маточные трубы справа",
                            "type": "string"
                        },
                        "rectovaginal_uterine_tubes_left": {
                            "description": "Ректовагинальное исследование. Маточные трубы слева",
                            "type": "string"
                        },
                        "rectovaginal_vaginal_fornix": {
                            "description": "Ректовагинальное исследование. Своды влагалища, массив, справочник rbRisarVaginalFornix",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectovaginal_comments": {
                            "description": "Ректовагинальное исследование..Дополнительная информация",
                            "type": "string"
                        }
                    }
                },
                "rectal": {
                    "description": "Ректальное исследование",
                    "type": "object",
                    "properties": {
                        "rectal_perianal_zona": {
                            "description": "Ректальное исследование. Перианальная область, массив, справочник rbRisarPerianalZona",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_rectum": {
                            "description": "Ректальное исследование. Прямая кишка, массив, справочник rbRisarRectum",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_cervix_uteri": {
                            "description": "Ректальное исследование. Шейка матки, справочник rbRisarCervixUteri",
                            "type": "string"
                        },
                        "rectal_cervix_consistency": {
                            "description": "Ректальное исследование. Консистенция шейки матки, справочник rbRisarCervix_Consistency",
                            "type": "string"
                        },
                        "rectal_uterus_body": {
                            "description": "Ректальное исследование. Тело матки, массив, справочник rbRisarUterusBodyGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_body_of_womb_size": {
                            "description": "Ректальное исследование. Размеры, справочник rbRisarBody_Of_Womb_Size",
                            "type": "string"
                        },
                        "rectal_body_of_womb_enlarged": {
                            "description": "Ректальное исследование.Размеры. Увеличены до",
                            "type": "string"
                        },
                        "rectal_uteri_position": {
                            "description": "Ректальное исследование. Положение, массив, справочник rbRisarUteriPositionGenVisit",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_parametrium": {
                            "description": "Ректальное исследование. Параметрическая область широких связок матки, массив, справочник rbRisarParametrium1",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_parametrium_other": {
                            "description": "Ректальное исследование. Параметрическая область широких связок матки. Другое",
                            "type": "string"
                        },
                        "rectal_ovary_right": {
                            "description": "Ректальное исследование.Яичники справа, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_ovary_right_oher": {
                            "description": "Ректальное исследование. Яичники справа.Другое",
                            "type": "string"
                        },
                        "rectal_ovary_left": {
                            "description": "Ректальное исследование.Яичники слева, массив, справочник rbRisarOvary",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_ovary_left_oher": {
                            "description": "Ректальное исследование. Яичники слева.Другое",
                            "type": "string"
                        },
                        "rectal_uterine_tubes_right": {
                            "description": "Ректальное исследование.Маточные трубы справа",
                            "type": "string"
                        },
                        "rectal_uterine_tubes_left": {
                            "description": "Ректальное исследование. Маточные трубы слева",
                            "type": "string"
                        },
                        "rectal_vaginal_fornix": {
                            "description": "Ректальное исследование. Своды влагалища, массив, справочник rbRisarVaginalFornix",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "rectal_comments": {
                            "description": "Ректальное исследование.Дополнительная информация",
                            "type": "string"
                        }
                    }
                },
                "medical_report": {
                    "description": "Заключение",
                    "type": "object",
                    "properties": {
                        "diagnosis_osn": {
                            "description": "Основной диагноз, код диагноза по МКБ-10",
                            "type": "string",
                            "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                        },
                        "diagnosis_osl": {
                            "description": "Диагноз осложнения, массив, код диагноза по МКБ-10",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            }
                        },
                        "diagnosis_sop": {
                            "description": "Диагноз сопутствующий, массив, код диагноза по МКБ-10",
                            "type": "array",
                            "items": {
                                "type": "string",
                                "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                            }
                        },
                        "encompassing_comments": {
                            "description": "Заключение. Примечания",
                            "type": "string"
                        },
                        "encompassing_treatment": {
                            "description": "Заключение. Лечение",
                            "type": "string"
                        },
                        "treatment_recommendations": {
                            "description": "Заключение. Рекомендации",
                            "type": "string"
                        }
                    },
                    "required": ["diagnosis_osn"]
                }
            },
            "required": ["external_id", "date", "hospital", "doctor", "medical_report"]
        }
    ]
