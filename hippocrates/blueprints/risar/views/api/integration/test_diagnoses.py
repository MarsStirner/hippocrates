# coding: utf-8

import os
import unittest
import logging
import datetime

from copy import deepcopy
from sqlalchemy import text

from blueprints.risar.lib.card import PregnancyCard, _clear_caches as clear_preg_card_cache
from blueprints.risar.lib.represent import represent_action_diagnoses
from blueprints.risar.views.api.integration.checkup_obs_first.xform import CheckupObsFirstXForm
from blueprints.risar.views.api.integration.checkup_obs_second.xform import CheckupObsSecondXForm
from blueprints.risar.views.api.integration.childbirth.xform import ChildbirthXForm
from blueprints.risar.views.api.integration.specialists_checkup.xform import SpecialistsCheckupXForm
from blueprints.risar.views.api.integration.hospitalization.xform import HospitalizationXForm
from blueprints.risar.views.api.integration.checkup_pc.xform import CheckupPCXForm
from blueprints.risar.views.api.integration.checkup_puerpera.xform import CheckupPuerperaXForm
from blueprints.risar.views.api.integration.utils import get_person_by_codes
from nemesis.systemwide import db
from nemesis.lib.utils import safe_dict, safe_date, safe_datetime
from nemesis.models.event import Event


TEST_DATA = {
    'person1': {'hosp': '-1', 'doctor': '22'},
    'person2': {'hosp': '-2', 'doctor': '-2'},

    'measure_spec_checkup1': {'measure_code': '0003'},
}


class TestEnvironment(object):

    def __init__(self, client_id, card_id=None):
        self.client_id = client_id
        self.card_id = card_id
        self.refresh()

    def refresh(self):
        clear_preg_card_cache()
        event = Event.query.get(self.card_id)
        self.card = PregnancyCard.get_for_event(event)
        self.card.get_card_attrs_action(True)
        self.insp_map = {}
        self.emr_map = {}

        self.initialize()

    def initialize(self):
        if not self.card_id:
            self.card = self.create_new_card()
            self.card_id = self.card.event.id

    def close(self):
        self._delete_everything()
        self.refresh()

    def _delete_everything(self):
        db.session.rollback()
        db.engine.execute(text(u'''\
delete ad.* \
from Diagnostic d join Diagnosis ds on d.diagnosis_id = ds.id \
left join Action_Diagnosis ad on ad.diagnosis_id = ds.id \
where ds.client_id = {0}'''.format(self.client_id)))
        db.engine.execute(text(u'''\
delete ed.* \
from Diagnostic d join Diagnosis ds on d.diagnosis_id = ds.id \
left join Event_Diagnosis ed on ed.diagnosis_id = ds.id \
where ds.client_id = {0}'''.format(self.client_id)))

        db.engine.execute(text(u'''\
delete d.*, ds.*
from Diagnostic d join Diagnosis ds on d.diagnosis_id = ds.id
left join Action_Diagnosis ad on ad.diagnosis_id = ds.id
where ds.client_id = {0}'''.format(self.client_id)))
        db.engine.execute(text(u'''\
delete from EventMeasure where event_id = {0}'''.format(self.card_id)))
        db.engine.execute(text(u'''\
delete fs.*
from RisarFetusState fs join Action a on fs.action_id = a.id
where a.event_id = {0}'''.format(self.card_id)))
        db.engine.execute(text(u'''\
delete ai.*
from ActionIdentification ai join Action a on ai.action_id = a.id
where a.event_id = {0}'''.format(self.card_id)))
        db.engine.execute(text(u'''\
delete ap.*
from ActionProperty ap join Action a on ap.action_id = a.id
where a.event_id = {0}'''.format(self.card_id)))
        db.engine.execute(text(u'''\
delete a.* \
from Action a \
where a.event_id = {0}'''.format(self.card_id)))

        db.session.close()

    def create_new_card(self):
        raise NotImplementedError

    def get_diagnoses_by_action(self):
        clear_preg_card_cache()

        return dict(
            (action_id, [self._make_diagnosis_info(diag_data)
                         for diag_data in represent_action_diagnoses(action)])
            for action_id, action in self.insp_map.items()
        )

    def get_diagnoses_in_event(self):
        clear_preg_card_cache()

        diagns = self.card.get_client_diagnostics(self.card.event.setDate, self.card.event.execDate, True)
        def make_diag_data(ds, dg):
            return {
                'id': ds.id,
                'set_date': ds.setDate,
                'end_date': ds.endDate,
                'client_id': ds.client_id,
                'deleted': ds.deleted,
                'person': {
                    'id': ds.person_id
                } if ds.person_id else None,
                'diagnostic': {
                    'id': dg.id,
                    'set_date': dg.setDate,
                    'end_date': dg.endDate,
                    'createDatetime': dg.createDatetime,
                    'mkb': dg.mkb,
                    'mkbex': dg.mkb_ex,
                    'deleted': dg.deleted,
                    'action_id': dg.action_id,
                    'modify_person': {
                        'id': dg.modifyPerson_id
                    } if dg.modifyPerson_id else None

                } if dg else None
            }
        diag_data_list = [make_diag_data(diagn.diagnosis, diagn) for diagn in diagns]

        return [self._make_diagnosis_info(diag_data) for diag_data in diag_data_list]

    def _make_diagnosis_info(self, data):
        return {
            'ds_id': data['id'],
            'ds_deleted': data['deleted'],
            'ds_set_date': data['set_date'],
            'ds_end_date': data['end_date'],
            'ds_person_id': data['person']['id'],
            'mkb': data['diagnostic']['mkb'].DiagID,
            'dg_id': data['diagnostic']['id'],
            'dg_deleted': data['diagnostic']['deleted'],
            'dg_set_date': data['diagnostic']['set_date'],
            'dg_create_date': data['diagnostic']['createDatetime'],
            'dg_person_id': data['diagnostic']['modify_person']['id'],
            'dg_action_id': data['diagnostic']['action_id'],
            'diagnosis_types': dict((dt_code, dk.code) for dt_code, dk in data['diagnosis_types'].items()),
        }

    def update_first_inspection(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = CheckupObsFirstXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        xform.store()
        xform.generate_measures()
        if create:
            self.insp_map[xform.target_obj.id] = xform.target_obj
        return xform.target_obj.id

    def delete_first_inspection(self, id_, api_version=0):
        xform = CheckupObsFirstXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()

    def update_second_inspection(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = CheckupObsSecondXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        xform.store()
        xform.generate_measures()
        if create:
            self.insp_map[xform.target_obj.id] = xform.target_obj
        return xform.target_obj.id

    def delete_second_inspection(self, id_, api_version=0):
        xform = CheckupObsSecondXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()
        xform.generate_measures()

    def update_childbirth(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = ChildbirthXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()

        xform.store()
        xform.reevaluate_data()
        xform.store()
        if create:
            self.insp_map[xform.target_obj.id] = xform.target_obj
        return xform.target_obj.id

    def delete_childbirth(self, api_version=0):
        xform = ChildbirthXForm(api_version)
        xform.check_params(None, self.card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()

    def update_specialist_checkup_emr(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = SpecialistsCheckupXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        xform.store()
        em = xform.get_em()
        if create:
            self.emr_map[em.id] = em
        return em

    def delete_specialist_checkup_emr(self, id_=None, api_version=0):
        xform = SpecialistsCheckupXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()

    def update_hospitalization_emr(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = HospitalizationXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        xform.store()
        em = xform.get_em()
        if create:
            self.emr_map[em.id] = em
        return em

    def delete_hospitalization_emr(self, id_=None, api_version=0):
        xform = HospitalizationXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()

    def update_inspection_pc(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = CheckupPCXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        xform.store()
        xform.generate_measures()
        if create:
            self.insp_map[xform.target_obj.id] = xform.target_obj
        return xform.target_obj.id

    def delete_inspection_pc(self, id_, api_version=0):
        xform = CheckupPCXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()
        xform.reevaluate_data()
        xform.store()
        xform.generate_measures()

    def update_inspection_puerpera(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = CheckupPuerperaXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        if create:
            self.insp_map[xform.target_obj.id] = xform.target_obj
        return xform.target_obj.id

    def delete_inspection_puerpera(self, id_, api_version=0):
        xform = CheckupPuerperaXForm(api_version)
        xform.check_params(id_, card_id)
        xform.delete_target_obj()
        xform.store()


class BaseDiagTest(unittest.TestCase):
    client_id = None
    card_id = None

    prim_insp1 = {
        "external_id": "12345",
        "general_info": {
            "date": "2016-04-30",  # *
            "hospital": "-1",  # *
            "doctor": "22",  # *
            "height": 180,  # *
            "weight": 80  # *
        },
        "medical_report": {  # Заключение
            "pregnancy_week": 12,  # * Беременность (недель)
            "next_visit_date": "2016-04-15",  # * Плановая дата следующей явки
            "pregnancy_continuation": True,  # * Возможность сохранения беременности
            "abortion_refusal": True,  # * Отказ от прерывания
            "diagnosis_osn": "D01",  # Основной диагноз
            "diagnosis_sop": ["G01"],  # Диагноз сопутствующий
            "diagnosis_osl": ["N01"],  # Диагноз осложнения
        }
    }
    rep_insp1 = {
        "external_id": "123456",
        "dynamic_monitoring": {
            "date": "2016-06-09",  # *
            "hospital": "-1",  # *
            "doctor": "22",  # *
            "ad_right_high": 120,  # *
            "ad_left_high": 120,  # *
            "ad_right_low": 80,  # *
            "ad_left_low": 80,  # *
            "weight": 51,  # *
        },
        "medical_report": {  # Заключение
            "pregnancy_week": 15,  # * Беременность (недель)
            "next_visit_date": "2016-07-15",  # * Плановая дата следующей явки
            "pregnancy_continuation": True,  # * Возможность сохранения беременности
            "abortion_refusal": False,  # * Отказ от прерывания
            "diagnosis_osn": "D01",  # Основной диагноз
            "diagnosis_sop": ["G01"],  # Диагноз сопутствующий
            "diagnosis_osl": ["H01", "H02"],  # Диагноз осложнения
        }
    }
    chbirth1 = {
        "general_info": {  # Общая информация
            "admission_date": "2016-04-14",  # Дата поступления
            "pregnancy_duration": 40,  # * Срок родоразрешения
            "delivery_date": "2016-04-14",  # * Дата родоразрешения
            "delivery_time": "13:30",  # * Время родоразрешения
            "maternity_hospital": "6202",  # * ЛПУ, принимавшее роды (код)
            "diagnosis_osn": "Z34.0",  # Основной диагноз, код диагноза по МКБ-10
            "diagnosis_sop": ["O30.2", "O42.0", "A00", "B05.0", "A04.3"],  # Диагноз сопутствующий (массив, код диагноза по МКБ-10)
            "diagnosis_osl": [],  # Диагноз осложнения (массив, код диагноза по МКБ-10)
            "pregnancy_speciality": u"течение родовое",  # Особенности течения беременности
            "postnatal_speciality": u"течение послеродовое",  # Особенности течения послеродового периода
            "help": u"помощь",  # Оказанная помощь
            "pregnancy_final": "rodami",  # Исход беременности, справочник rbRisarPregnancy_Final ["rodami",]
            # "abortion": None,  # Вид аборта, справочник rbRisarAbort ["samoproizvol_nyj",]
            "maternity_hospital_doctor": "33",  # Лечащий врач роддома (код)
            "curation_hospital": "6202",  # ЛПУ курации новорождённого
        },
        "mother_death": {  # Информация о смерти матери
            "death": True,  # Смерть матери
            "reason_of_death": u"нет",  # * Причина смерти матери
            "death_date": "2016-04-07",  # * Дата смерти матери
            "death_time": "00:30",  # * Время смерти матери
            "pat_diagnosis_osn": "Z34.0",  # Основной патологоанатомический диагноз, код диагноза по МКБ-10
            "pat_diagnosis_sop": ["O30.2", "O42.0", "A00", "A04.3"],  # Диагноз сопутствующий (массив, код диагноза по МКБ-10)
            "pat_diagnosis_osl": ["B05.0"],  # Диагноз осложнения (массив, код диагноза по МКБ-10)
            "control_expert_conclusion": u"лкккк",  # Заключение ЛКК
        },
        "kids": [  # Сведения о родившихся детях
            {
                "alive": True,  # * Живой
                "sex": 1,  # * Пол
                "weight": 3000,  # * Масса
                "length": 40,  # * Длина
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
        ],
    }
    emr_spec_ch1 = {
        'external_id': '12346',
        'measure_id': None,
        'measure_type_code': None,
        'checkup_date': '2016-05-24',
        'lpu_code': '-1',
        'doctor_code': '22',
        'diagnosis': 'A00',
    }
    emr_hospitalization1 = {
        'external_id': '12345',
        'measure_id': None,
        'date_in': '2016-03-28',
        'date_out': '2016-04-04',
        'hospital': '6202',
        'doctor': '33',
        'pregnancy_week': 14,
        'diagnosis_in': 'A01.1',
        'diagnosis_out': 'A03.3',
    }
    insp_pc1 = {
        "external_id": "12345",
        "general_info": {
            "date": "2016-04-30",  # *
            "hospital": "-1",  # *
            "doctor": "22",  # *
            "height": 180,  # *
            "weight": 80  # *
        },
        "medical_report": {  # Заключение
            "pregnancy_week": 12,  # * Беременность (недель)
            "next_visit_date": "2016-04-15",  # * Плановая дата следующей явки
            "pregnancy_continuation": True,  # * Возможность сохранения беременности
            "abortion_refusal": True,  # * Отказ от прерывания
            "diagnosis_osn": "D01",  # Основной диагноз
            "diagnosis_sop": ["G01"],  # Диагноз сопутствующий
            "diagnosis_osl": ["N01"],  # Диагноз осложнения
        }
    }
    insp_pp1 = {
        "external_id": "12345",
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
    }

    @classmethod
    def parametrize(cls, client_id, card_id):
        cls.client_id = client_id
        cls.card_id = card_id

    def setUp(self):
        self.env = TestEnvironment(self.client_id, self.card_id)

    def tearDown(self):
        self.env.close()

    def _formatComparedDiags(self, diag_list, expected_list):
        s = u'expected:\n\t* {0}\nactual:\n\t* {1}'.format(
                u'\n\t* '.join(unicode(e) for e in expected_list),
                u'\n\t* '.join(unicode(d) for d in diag_list)
            )
        return s

    def assertDiagsLikeExpected(self, diag_list, expected_list, msg=None, debug=False):
        actual_list = diag_list[:]
        if debug:
            print self._formatComparedDiags(diag_list, expected_list)
        for expected in expected_list:
            for idx, diag in enumerate(actual_list):
                # try this diag
                for attr, exp_val in expected.iteritems():
                    if attr not in diag or diag[attr] != exp_val:
                        if debug:
                            print 'attr:', attr, 'not found' if attr not in diag else (
                                'expected: {0}, actual {1}.'.format(exp_val, diag[attr])
                            )
                        break
                else:
                    # this diag matches one of expected
                    break
            else:
                # neither of diags matches expected
                break
            # diag at idx matches one of the expected, remove it
            del actual_list[idx]
        else:
            if len(actual_list) == 0:
                # all good
                return
        # fail
        standardMsg = u'Diags data does not match expected data:\n{0}'.format(
            self._formatComparedDiags(diag_list, expected_list))
        return self.fail(self._formatMessage(msg, standardMsg))

    def make_expected_diag(self, **kwargs):
        conv = {
            'ds_id': lambda x: x,
            'ds_set_date': lambda x: safe_date(x),
            'ds_end_date': lambda x: safe_datetime(x),
            'ds_person_id': lambda x: get_person_by_codes(*self._decode_person_codes(x)).id,
            'mkb': lambda x: x,
            'diagnosis_types': lambda x: x,
            'dg_id': lambda x: x,
            'dg_set_date': lambda x: safe_datetime(safe_date(x)),
            'dg_end_date': lambda x: safe_datetime(x),
            'dg_create_date': lambda x: safe_datetime(safe_date(x)),
            'dg_person_id': lambda x: get_person_by_codes(*self._decode_person_codes(x)).id,
            'dg_action_id': lambda x: x,
            'dg_deleted': lambda x: x,
        }
        return dict((k, conv[k](v)) for k, v in kwargs.items())

    def _final_main(self):
        return {'final': 'main'}

    def _final_compl(self):
        return {'final': 'complication'}

    def _final_assoc(self):
        return {'final': 'associated'}

    def _pat_main(self):
        return {'pathanatomical': 'main'}

    def _pat_compl(self):
        return {'pathanatomical': 'complication'}

    def _pat_assoc(self):
        return {'pathanatomical': 'associated'}

    def _encode_person_codes(self, person_code, hospital_code):
        return u'{0} &? {1}'.format(person_code, hospital_code)

    def _decode_person_codes(self, code):
        return code.split(u' &? ')

    def _change_test_prinsp_data(self, insp, **kwargs):
        if 'date' in kwargs:
            insp['general_info']['date'] = kwargs['date']
        if 'hospital' in kwargs:
            insp['general_info']['hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            insp['general_info']['doctor'] = kwargs['doctor']
        if 'mkb_main' in kwargs:
            mkb_main = kwargs['mkb_main']
            if mkb_main is None:
                del insp['medical_report']['diagnosis_osn']
            else:
                insp['medical_report']['diagnosis_osn'] = mkb_main
        if 'mkb_compl' in kwargs:
            mkb_compl = kwargs['mkb_compl']
            if mkb_compl is None:
                del insp['medical_report']['diagnosis_osl']
            else:
                insp['medical_report']['diagnosis_osl'] = mkb_compl
        if 'mkb_assoc' in kwargs:
            mkb_assoc = kwargs['mkb_assoc']
            if mkb_assoc is None:
                del insp['medical_report']['diagnosis_sop']
            else:
                insp['medical_report']['diagnosis_sop'] = mkb_assoc
        return insp

    def _change_test_repinsp_data(self, insp, **kwargs):
        if 'date' in kwargs:
            insp['dynamic_monitoring']['date'] = kwargs['date']
        if 'external_id' in kwargs:
            insp['external_id'] = kwargs['external_id']
        if 'hospital' in kwargs:
            insp['dynamic_monitoring']['hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            insp['dynamic_monitoring']['doctor'] = kwargs['doctor']
        if 'mkb_main' in kwargs:
            mkb_main = kwargs['mkb_main']
            if mkb_main is None:
                del insp['medical_report']['diagnosis_osn']
            else:
                insp['medical_report']['diagnosis_osn'] = mkb_main
        if 'mkb_compl' in kwargs:
            mkb_compl = kwargs['mkb_compl']
            if mkb_compl is None:
                del insp['medical_report']['diagnosis_osl']
            else:
                insp['medical_report']['diagnosis_osl'] = mkb_compl
        if 'mkb_assoc' in kwargs:
            mkb_assoc = kwargs['mkb_assoc']
            if mkb_assoc is None:
                del insp['medical_report']['diagnosis_sop']
            else:
                insp['medical_report']['diagnosis_sop'] = mkb_assoc
        return insp

    def _change_test_childbirth_data(self, chb, **kwargs):
        if 'date' in kwargs:
            chb['general_info']['delivery_date'] = kwargs['date']
            chb['general_info']['delivery_time'] = '10:00'
            chb['general_info']['admission_date'] = kwargs['date']
        if 'hospital' in kwargs:
            chb['general_info']['maternity_hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            chb['general_info']['maternity_hospital_doctor'] = kwargs['doctor']
        if 'mkb_main' in kwargs:
            mkb_main = kwargs['mkb_main']
            if mkb_main is None:
                del chb['general_info']['diagnosis_osn']
            else:
                chb['general_info']['diagnosis_osn'] = mkb_main
        if 'mkb_compl' in kwargs:
            mkb_compl = kwargs['mkb_compl']
            if mkb_compl is None:
                del chb['general_info']['diagnosis_osl']
            else:
                chb['general_info']['diagnosis_osl'] = mkb_compl
        if 'mkb_assoc' in kwargs:
            mkb_assoc = kwargs['mkb_assoc']
            if mkb_assoc is None:
                del chb['general_info']['diagnosis_sop']
            else:
                chb['general_info']['diagnosis_sop'] = mkb_assoc
        if 'mkb_main_pat' in kwargs:
            mkb_main = kwargs['mkb_main_pat']
            if mkb_main is None:
                del chb['mother_death']['pat_diagnosis_osn']
            else:
                chb['mother_death']['pat_diagnosis_osn'] = mkb_main
        if 'mkb_compl_pat' in kwargs:
            mkb_compl = kwargs['mkb_compl_pat']
            if mkb_compl is None:
                del chb['mother_death']['pat_diagnosis_osl']
            else:
                chb['mother_death']['pat_diagnosis_osl'] = mkb_compl
        if 'mkb_assoc_pat' in kwargs:
            mkb_assoc = kwargs['mkb_assoc_pat']
            if mkb_assoc is None:
                del chb['mother_death']['pat_diagnosis_sop']
            else:
                chb['mother_death']['pat_diagnosis_sop'] = mkb_assoc
        return chb

    def _change_test_specialist_checkup_emr_data(self, emr, **kwargs):
        if 'measure_code' in kwargs:
            emr['measure_type_code'] = kwargs['measure_code']
        if 'date' in kwargs:
            emr['checkup_date'] = kwargs['date']
        if 'external_id' in kwargs:
            emr['external_id'] = kwargs['external_id']
        if 'measure_id' in kwargs:
            emr['measure_id'] = kwargs['measure_id']
        if 'hospital' in kwargs:
            emr['lpu_code'] = kwargs['hospital']
        if 'doctor' in kwargs:
            emr['doctor_code'] = kwargs['doctor']
        if 'mkb' in kwargs:
            mkb = kwargs['mkb']
            if mkb is None:
                del emr['diagnosis']
            else:
                emr['diagnosis'] = mkb
        return emr

    def _change_test_hospitalization_emr_data(self, emr, **kwargs):
        if 'date' in kwargs:
            emr['date_out'] = kwargs['date']
        if 'external_id' in kwargs:
            emr['external_id'] = kwargs['external_id']
        if 'measure_id' in kwargs:
            emr['measure_id'] = kwargs['measure_id']
        if 'hospital' in kwargs:
            emr['hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            emr['doctor'] = kwargs['doctor']
        if 'mkb' in kwargs:
            mkb = kwargs['mkb']
            if mkb is None:
                del emr['diagnosis_out']
            else:
                emr['diagnosis_out'] = mkb
        return emr

    def _change_test_insp_pc_data(self, insp, **kwargs):
        if 'date' in kwargs:
            insp['general_info']['date'] = kwargs['date']
        if 'hospital' in kwargs:
            insp['general_info']['hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            insp['general_info']['doctor'] = kwargs['doctor']
        if 'external_id' in kwargs:
            insp['general_info']['external_id'] = kwargs['external_id']
        if 'mkb_main' in kwargs:
            mkb_main = kwargs['mkb_main']
            if mkb_main is None:
                del insp['medical_report']['diagnosis_osn']
            else:
                insp['medical_report']['diagnosis_osn'] = mkb_main
        if 'mkb_compl' in kwargs:
            mkb_compl = kwargs['mkb_compl']
            if mkb_compl is None:
                del insp['medical_report']['diagnosis_osl']
            else:
                insp['medical_report']['diagnosis_osl'] = mkb_compl
        if 'mkb_assoc' in kwargs:
            mkb_assoc = kwargs['mkb_assoc']
            if mkb_assoc is None:
                del insp['medical_report']['diagnosis_sop']
            else:
                insp['medical_report']['diagnosis_sop'] = mkb_assoc
        return insp

    def _change_test_insp_puerpera_data(self, insp, **kwargs):
        if 'date' in kwargs:
            insp['date'] = kwargs['date']
        if 'hospital' in kwargs:
            insp['hospital'] = kwargs['hospital']
        if 'doctor' in kwargs:
            insp['doctor'] = kwargs['doctor']
        if 'external_id' in kwargs:
            insp['external_id'] = kwargs['external_id']
        if 'mkb_main' in kwargs:
            mkb_main = kwargs['mkb_main']
            if mkb_main is None:
                del insp['diagnosis']
            else:
                insp['diagnosis'] = mkb_main
        return insp

    def _get_ds_id_from_diags(self, diags, mkb):
        for d in diags:
            if d['mkb'] == mkb:
                return d['ds_id']
        else:
            assert False, u'Не найден диагноз, который должен существовать'

    def _get_dg_id_from_diags(self, diags, mkb):
        for d in diags:
            if d['mkb'] == mkb:
                return d['dg_id']
        else:
            assert False, u'Не найден диагноз, который должен существовать'


class SimpleTestCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_single_inspection_base(self):
        a_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'D01'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        first_person = self._encode_person_codes(doctor_code, hosp_code)
        D01_ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)
        D01_dg_main_id_a1 = self._get_dg_id_from_diags(insp1_diags, mkb_main)
        G01_ds_assoc_id = self._get_ds_id_from_diags(insp1_diags, mkb_assoc[0])

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date,
                                                  ds_person_id=first_person, dg_person_id=first_person),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date,
                                                  ds_person_id=first_person, dg_person_id=first_person),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a_date,
                                                  ds_person_id=first_person, dg_person_id=first_person)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test nothing changed
        insp1_id = self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date,
                                                  ds_person_id=first_person, dg_person_id=first_person,
                                                  ds_id=D01_ds_main_id, dg_id=D01_dg_main_id_a1),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test doctor changed
        hosp_code = TEST_DATA['person2']['hosp']
        doctor_code = TEST_DATA['person2']['doctor']
        insp1 = self._change_test_prinsp_data(insp1, hospital=hosp_code, doctor=doctor_code)
        insp1_id = self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        second_person = self._encode_person_codes(doctor_code, hosp_code)
        dg_main_id_a2 = self._get_dg_id_from_diags(insp1_diags, mkb_main)

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date,
                                                  ds_person_id=second_person, dg_person_id=second_person,
                                                  ds_id=D01_ds_main_id, dg_id=dg_main_id_a2),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test diag changed
        mkb_main = 'D03'
        mkb_compl = None
        insp1 = self._change_test_prinsp_data(insp1, date=a_date, mkb_main=mkb_main, mkb_compl=mkb_compl)
        insp1_id = self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        D03_ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date,
                                                  ds_id=D03_ds_main_id),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test date moved to left
        a_date = '2016-03-25'
        insp1 = self._change_test_prinsp_data(insp1, date=a_date)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date,
                                                  ds_id=D03_ds_main_id),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

    # @unittest.skip('debug')
    def test_multiple_inspections_base(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'Z34.0'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)

        # 2 insp to right
        a2_date = '2016-06-09'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main2 = 'Z34.0'
        mkb_compl2 = ['H01', 'H02']
        mkb_assoc2 = ['G01']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2, mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)
        # prev
        a1_enddatetime = (datetime.datetime.strptime(a2_date, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0], ds_end_date=a1_enddatetime,
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(act_diags_map[insp1_id], expected_diags)

        # 3 insp between 1 and 2
        a3_date = "2016-05-15"
        external_id3 = "a3"
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main3 = 'Z34.0'
        mkb_compl3 = ['H01']
        mkb_assoc3 = ['G01']
        insp3 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a3_date, external_id=external_id3,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main3, mkb_compl=mkb_compl3, mkb_assoc=mkb_assoc3)
        insp3_id = self.env.update_second_inspection(insp3, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp3_diags = act_diags_map[insp3_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main3,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc3[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date),
                          self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_compl3[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)
        # next
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(act_diags_map[insp2_id], expected_diags)
        # prev
        a1_enddatetime = (datetime.datetime.strptime(a3_date, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0], ds_end_date=a1_enddatetime,
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(act_diags_map[insp1_id], expected_diags)

        # 4 insp between 1 and 3
        a4_date = "2016-05-09"
        external_id4 = "a4"
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main4 = 'Z34.0'
        mkb_compl4 = ['H01']
        mkb_assoc4 = None
        insp4 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a4_date, external_id=external_id4,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main4, mkb_compl=mkb_compl4, mkb_assoc=mkb_assoc4)
        insp4_id = self.env.update_second_inspection(insp4, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp4_diags = act_diags_map[insp4_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main4,
                                                  diagnosis_types=self._final_main(), dg_set_date=a4_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_compl4[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date)]
        self.assertDiagsLikeExpected(insp4_diags, expected_diags)
        # next
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_assoc3[0],  # ds.id != ds1.id
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date),
                          self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_compl3[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date)]
        self.assertDiagsLikeExpected(act_diags_map[insp3_id], expected_diags)
        ds_id_D03_prev = self._get_ds_id_from_diags(act_diags_map[insp1_id], mkb_assoc3[0])
        ds_id_D03_next = self._get_ds_id_from_diags(act_diags_map[insp3_id], mkb_assoc3[0])
        self.assertNotEqual(ds_id_D03_prev, ds_id_D03_next)
        # prev
        a4_beforedate = (datetime.datetime.strptime(a4_date, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0], ds_end_date=a4_beforedate,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0], ds_end_date=a4_beforedate,
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(act_diags_map[insp1_id], expected_diags)

    # @unittest.skip('debug')
    def test_multiple_sequential_inspections(self):
        """Последовательное добавление осмотров"""
        a1_date1 = '2016-04-30'
        hosp1_code = TEST_DATA['person1']['hosp']
        doctor1_code = TEST_DATA['person1']['doctor']
        mkb1_main1 = 'D01'
        mkb1_compl1 = ['N01']
        mkb1_assoc1 = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date1,
            hospital=hosp1_code, doctor=doctor1_code, mkb_main=mkb1_main1, mkb_compl=mkb1_compl1,
            mkb_assoc=mkb1_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        D01_ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb1_main1)
        N01_ds_compl_id = self._get_ds_id_from_diags(insp1_diags, mkb1_compl1[0])
        G01_ds_assoc_id = self._get_ds_id_from_diags(insp1_diags, mkb1_assoc1[0])

        # 2nd
        a2_date1 = '2016-06-29'
        hosp2_code = TEST_DATA['person1']['hosp']
        doctor2_code = TEST_DATA['person1']['doctor']
        mkb2_main1 = 'Z34.0'
        mkb2_compl1 = ['N01']
        mkb2_assoc1 = ['G01', 'G02']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date1,
            hospital=hosp2_code, doctor=doctor2_code, mkb_main=mkb2_main1, mkb_compl=mkb2_compl1,
            mkb_assoc=mkb2_assoc1)
        insp2_id = self.env.update_second_inspection(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        Z34_0_ds_main_id = self._get_ds_id_from_diags(insp2_diags, mkb2_main1)
        G02_ds_assoc_id = self._get_ds_id_from_diags(insp2_diags, mkb2_assoc1[1])

        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        insp1_diags = act_diags_map[insp1_id]
        a2_beforedate = (datetime.datetime.strptime(a2_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date1,
                                                  ds_id=D01_ds_main_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date1,
                                                  ds_id=G01_ds_assoc_id, ds_end_date=None)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # 3rd
        a3_date1 = '2016-07-20'
        a3_external_id = 'a3'
        hosp3_code = TEST_DATA['person1']['hosp']
        doctor3_code = TEST_DATA['person1']['doctor']
        mkb3_main1 = 'Z34.0'
        mkb3_compl1 = ['N01', 'N02']
        mkb3_assoc1 = ['G02', 'G03']
        insp3 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a3_date1, external_id=a3_external_id,
            hospital=hosp3_code, doctor=doctor3_code, mkb_main=mkb3_main1, mkb_compl=mkb3_compl1,
            mkb_assoc=mkb3_assoc1)
        insp3_id = self.env.update_second_inspection(insp3, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp3_diags = act_diags_map[insp3_id]

        N02_ds_compl_id = self._get_ds_id_from_diags(insp3_diags, mkb3_compl1[1])
        G03_ds_assoc_id = self._get_ds_id_from_diags(insp3_diags, mkb3_assoc1[1])

        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)

        insp2_diags = act_diags_map[insp2_id]
        a3_beforedate = (datetime.datetime.strptime(a3_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date1,
                                                  ds_id=Z34_0_ds_main_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G01_ds_assoc_id, ds_end_date=a3_beforedate),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G02_ds_assoc_id, ds_end_date=None)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

    # @unittest.skip('debug')
    def test_different_diag_types(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'D01'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp2_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp2_diags, mkb_main)

        # test add epicrisis with different pat diags
        ep1_date = '2016-08-01'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main_cb1 = 'D01'
        mkb_compl_cb1 = None
        mkb_assoc_cb1 = ['J01']
        mkb_main_pat1 = 'O95'
        mkb_compl_pat1 = ['O96.1']
        mkb_assoc_pat1 = ['J01']
        chb = self._change_test_childbirth_data(deepcopy(self.chbirth1), date=ep1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main_cb1, mkb_compl=mkb_compl_cb1,
            mkb_assoc=mkb_assoc_cb1, mkb_main_pat=mkb_main_pat1, mkb_compl_pat=mkb_compl_pat1,
            mkb_assoc_pat=mkb_assoc_pat1)
        chb1_id = self.env.update_childbirth(chb, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]
        O95_compl_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_main_pat1)
        O96_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_compl_pat1[0])
        J01_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_assoc_pat1[0])

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb1,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date, ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_assoc_cb1[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_main_pat1,
                                                  diagnosis_types=dict(self._pat_main(), **self._final_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_compl_pat1[0],
                                                  diagnosis_types=dict(self._pat_compl(), **self._final_assoc()),
                                                  dg_set_date=ep1_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # test nothing changed
        chb1_id = self.env.update_childbirth(chb, card_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb1,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date, ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_assoc_cb1[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_main_pat1,
                                                  diagnosis_types=dict(self._pat_main(), **self._final_assoc()),
                                                  dg_set_date=ep1_date, ds_id=O95_compl_ds_id, dg_deleted=0),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_compl_pat1[0],
                                                  diagnosis_types=dict(self._pat_compl(), **self._final_assoc()),
                                                  dg_set_date=ep1_date, ds_id=O96_1_assoc_ds_id, dg_deleted=0)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # test change date
        ep2_date = '2016-07-30'
        chb = self._change_test_childbirth_data(chb, date=ep2_date)
        chb1_id = self.env.update_childbirth(chb, chb1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb1,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date, ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_assoc_cb1[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date, ds_id=J01_1_assoc_ds_id),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_main_pat1,
                                                  diagnosis_types=dict(self._pat_main(), **self._final_assoc()),
                                                  dg_set_date=ep2_date, ds_id=O95_compl_ds_id,),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_pat1[0],
                                                  diagnosis_types=dict(self._pat_compl(), **self._final_assoc()),
                                                  dg_set_date=ep2_date, ds_id=O96_1_assoc_ds_id)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

    # @unittest.skip('debug')
    def test_measure_results_base(self):
        a1_date = '2016-04-30'
        hosp1_code = TEST_DATA['person1']['hosp']
        doctor1_code = TEST_DATA['person1']['doctor']
        mkb_main1 = 'D01'
        mkb_compl1 = None
        mkb_assoc1 = None
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp1_code, doctor=doctor1_code, mkb_main=mkb_main1, mkb_compl=mkb_compl1,
            mkb_assoc=mkb_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)

        # test add emr after
        emr1_external_id = '12346'
        emr1_measure_code = TEST_DATA['measure_spec_checkup1']['measure_code']
        emr1_measure_id = None
        emr1_date = '2016-05-24'
        emr1_hosp_code = TEST_DATA['person1']['hosp']
        emr1_doctor_code = TEST_DATA['person1']['doctor']
        emr1_mkb = 'A00'
        emr1 = self._change_test_specialist_checkup_emr_data(deepcopy(self.emr_spec_ch1),
             measure_code=emr1_measure_code, date=emr1_date, hospital=emr1_hosp_code,
             doctor=emr1_doctor_code, mkb=emr1_mkb)
        em1 = self.env.update_specialist_checkup_emr(emr1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        # на данный момент ситуация, что в 1ом осмотре (без даты окончания)
        # появился диагноз из результата мероприятия (более позднего), корректна.
        # Впоследствии при изменении такого поведения нужно будет исправить проверки в тестах.
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date),
                          self.make_expected_diag(ds_set_date=emr1_date, mkb=emr1_mkb,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test nothing changed
        emr1 = self._change_test_specialist_checkup_emr_data(emr1, measure_id=em1.id)
        em1 = self.env.update_specialist_checkup_emr(emr1, em1.resultAction_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date),
                          self.make_expected_diag(ds_set_date=emr1_date, mkb=emr1_mkb,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test new inspection after both
        a2_date = '2016-06-10'
        hosp2_code = TEST_DATA['person1']['hosp']
        doctor2_code = TEST_DATA['person1']['doctor']
        mkb_main2 = 'D01'
        mkb_compl2 = ['H01']
        mkb_assoc2 = ['N01', 'A00']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp2_code, doctor=doctor2_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2,
            mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=emr1_date, mkb=mkb_assoc2[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

    # @unittest.skip('debug')
    def test_inspections_delete(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'D01'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)

        # test base deletion
        self.env.delete_first_inspection(insp1_id)
        card_diags = self.env.get_diagnoses_in_event()
        self.assertEqual(card_diags, [])

        # test delete 2nd inspection
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)
        # 2 insp to right
        a2_date = '2016-06-09'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main2 = 'D01'
        mkb_compl2 = ['H01', 'H02']
        mkb_assoc2 = ['G01']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2, mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, None)

        self.env.delete_second_inspection(insp2_id)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test 3 inspections, delete middle
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2, mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, None)

        # 3 insp between 1 and 2
        a3_date = "2016-05-15"
        external_id3 = "a3"
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main3 = 'D01'
        mkb_compl3 = ['H01']
        mkb_assoc3 = ['G01']
        insp3 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a3_date, external_id=external_id3,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main3, mkb_compl=mkb_compl3, mkb_assoc=mkb_assoc3)
        insp3_id = self.env.update_second_inspection(insp3, None)

        self.env.delete_second_inspection(insp3_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)
        insp2_diags = act_diags_map[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

    # @unittest.skip('debug')
    def test_measure_results_delete(self):
        a1_date = '2016-04-30'
        hosp1_code = TEST_DATA['person1']['hosp']
        doctor1_code = TEST_DATA['person1']['doctor']
        mkb_main1 = 'D01'
        mkb_compl1 = None
        mkb_assoc1 = None
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp1_code, doctor=doctor1_code, mkb_main=mkb_main1, mkb_compl=mkb_compl1,
            mkb_assoc=mkb_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)

        emr1_external_id = '12346'
        emr1_measure_code = TEST_DATA['measure_spec_checkup1']['measure_code']
        emr1_measure_id = None
        emr1_date = '2016-05-24'
        emr1_hosp_code = TEST_DATA['person1']['hosp']
        emr1_doctor_code = TEST_DATA['person1']['doctor']
        emr1_mkb = 'A00'
        emr1 = self._change_test_specialist_checkup_emr_data(deepcopy(self.emr_spec_ch1),
             measure_code=emr1_measure_code, date=emr1_date, hospital=emr1_hosp_code,
             doctor=emr1_doctor_code, mkb=emr1_mkb)
        em1 = self.env.update_specialist_checkup_emr(emr1, None)

        # test base deletion
        self.env.delete_specialist_checkup_emr(em1.resultAction_id)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test insp1, emr, insp2, delete emr
        em1 = self.env.update_specialist_checkup_emr(emr1, None)

        a2_date = '2016-06-10'
        hosp2_code = TEST_DATA['person1']['hosp']
        doctor2_code = TEST_DATA['person1']['doctor']
        mkb_main2 = 'D01'
        mkb_compl2 = ['H01']
        mkb_assoc2 = ['N01', 'A00']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp2_code, doctor=doctor2_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2,
            mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, None)

        self.env.delete_specialist_checkup_emr(em1.resultAction_id)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)
        insp2_diags = act_diags_map[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_assoc2[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)


class MeasureResultsCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_emr_hospitalization(self):
        a1_date = '2016-04-30'
        hosp1_code = TEST_DATA['person1']['hosp']
        doctor1_code = TEST_DATA['person1']['doctor']
        mkb_main1 = 'D01'
        mkb_compl1 = None
        mkb_assoc1 = None
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp1_code, doctor=doctor1_code, mkb_main=mkb_main1, mkb_compl=mkb_compl1,
            mkb_assoc=mkb_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)

        # test add emr after
        emr1_external_id = '12346'
        emr1_measure_id = None
        emr1_date = '2016-05-24'
        emr1_hosp_code = TEST_DATA['person1']['hosp']
        emr1_doctor_code = TEST_DATA['person1']['doctor']
        emr1_mkb = 'A00'
        emr1 = self._change_test_hospitalization_emr_data(deepcopy(self.emr_hospitalization1),
             date=emr1_date, hospital=emr1_hosp_code, doctor=emr1_doctor_code, mkb=emr1_mkb)
        em1 = self.env.update_hospitalization_emr(emr1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        # на данный момент ситуация, что в 1ом осмотре (без даты окончания)
        # появился диагноз из результата мероприятия (более позднего), корректна.
        # Впоследствии при изменении такого поведения нужно будет исправить проверки в тестах.
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date),
                          self.make_expected_diag(ds_set_date=emr1_date, mkb=emr1_mkb,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test nothing changed
        emr1 = self._change_test_hospitalization_emr_data(emr1, measure_id=em1.id)
        em1 = self.env.update_hospitalization_emr(emr1, em1.resultAction_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date),
                          self.make_expected_diag(ds_set_date=emr1_date, mkb=emr1_mkb,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # delete emr
        self.env.delete_hospitalization_emr(em1.resultAction_id)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main1, ds_end_date=None,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)


class InspectionPCCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_inspections_pc_base(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'Z34.0'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)

        # 2 insp to right
        a2_date = '2016-06-09'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main2 = 'Z34.0'
        mkb_compl2 = ['H01', 'H02']
        mkb_assoc2 = ['G01']
        insp2 = self._change_test_insp_pc_data(deepcopy(self.insp_pc1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main2, mkb_compl=mkb_compl2, mkb_assoc=mkb_assoc2)
        insp2_id = self.env.update_inspection_pc(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl2[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # delete 2nd
        self.env.delete_inspection_pc(insp2_id)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)


class InspectionPuerperaCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_inspections_pp_base(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'Z38.0'
        insp1 = self._change_test_insp_puerpera_data(deepcopy(self.insp_pp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main)
        insp1_id = self.env.update_inspection_puerpera(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # 2 insp to right
        a2_date = '2016-06-09'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        external_id = 'insp_pp2'
        mkb_main2 = 'Z38.0'
        insp2 = self._change_test_insp_puerpera_data(deepcopy(self.insp_pp1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main2, external_id=external_id)
        insp2_id = self.env.update_inspection_puerpera(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # change 2 insp
        a2_date = '2016-07-11'
        mkb_main2 = 'Z39.0'
        insp2 = self._change_test_insp_puerpera_data(insp2, date=a2_date, mkb_main=mkb_main2)
        insp2_id = self.env.update_inspection_puerpera(insp2, insp2_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # prev
        a1_enddatetime = (datetime.datetime.strptime(a2_date, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_end_date=a1_enddatetime)]
        self.assertDiagsLikeExpected(act_diags_map[insp1_id], expected_diags)

        # change 2 insp back
        a2_date = '2016-06-09'
        mkb_main2 = 'Z38.0'
        insp2 = self._change_test_insp_puerpera_data(insp2, date=a2_date, mkb_main=mkb_main2)
        insp2_id = self.env.update_inspection_puerpera(insp2, insp2_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # prev
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_end_date=None)]
        self.assertDiagsLikeExpected(act_diags_map[insp1_id], expected_diags)

        # delete 1st
        self.env.delete_inspection_puerpera(insp1_id)
        insp2_diags = self.env.get_diagnoses_by_action()[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)


class ChildbirthCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_childbirth_final_diags(self):
        card_id = self.env.card_id
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'Z35.2'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)
        compl_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_compl[0])
        assoc_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_assoc[0])

        # test add epicrisis
        ep1_date = '2016-08-01'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main_cb1 = 'Z35.2'
        mkb_compl_cb1 = ['O20']
        mkb_assoc_cb1 = ['J01']
        chb = self._change_test_childbirth_data(deepcopy(self.chbirth1), date=ep1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main_cb1, mkb_compl=mkb_compl_cb1,
            mkb_assoc=mkb_assoc_cb1, mkb_main_pat=None, mkb_compl_pat=None,
            mkb_assoc_pat=None)
        chb1_id = self.env.update_childbirth(chb, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]
        # O95_compl_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_main_pat1)
        # O96_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_compl_pat1[0])
        # J01_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_assoc_pat1[0])

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb1,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_assoc_cb1[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_compl_cb1[0],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # test nothing changed
        chb1_id = self.env.update_childbirth(chb, chb1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb1,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_assoc_cb1[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date),
                          self.make_expected_diag(ds_set_date=ep1_date, mkb=mkb_compl_cb1[0],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep1_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # test change date and diags
        ep2_date = '2016-08-21'
        mkb_main_cb2 = 'Z35.3'
        mkb_compl_cb2 = ['O20', 'O21']
        mkb_assoc_cb2 = ['G01']
        chb = self._change_test_childbirth_data(chb, date=ep2_date,
            mkb_main=mkb_main_cb2, mkb_compl=mkb_compl_cb2, mkb_assoc=mkb_assoc_cb2)
        chb1_id = self.env.update_childbirth(chb, chb1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_main_cb2,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc_cb2[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_cb2[0],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_cb2[1],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # delete ep
        self.env.delete_childbirth()
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date,
                                                  ds_id=compl_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date,
                                                  ds_id=assoc_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

    # @unittest.skip('debug')
    def test_childbirth_final_and_path_diags(self):
        card_id = self.env.card_id
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'Z35.2'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None)
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        main_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)
        compl_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_compl[0])
        assoc_mkb_ds_id = self._get_ds_id_from_diags(insp1_diags, mkb_assoc[0])

        # test add epicrisis
        ep1_date = '2016-08-01'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main_cb1 = 'Z35.2'
        mkb_compl_cb1 = ['O20']
        mkb_assoc_cb1 = ['J01']
        chb = self._change_test_childbirth_data(deepcopy(self.chbirth1), date=ep1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main_cb1, mkb_compl=mkb_compl_cb1,
            mkb_assoc=mkb_assoc_cb1, mkb_main_pat=None, mkb_compl_pat=None,
            mkb_assoc_pat=None)
        chb1_id = self.env.update_childbirth(chb, None)

        # edit and add path diagnoses
        ep2_date = '2016-07-29'
        mkb_main_cb2 = 'Z35.2'
        mkb_compl_cb2 = ['O20']
        mkb_assoc_cb2 = ['J01', 'J02']
        mkb_main_pat1 = 'O95'
        mkb_compl_pat1 = ['O96.1']
        mkb_assoc_pat1 = ['J02', 'J01']
        chb = self._change_test_childbirth_data(chb, date=ep2_date, mkb_assoc=mkb_assoc_cb2,
            mkb_main_pat=mkb_main_pat1, mkb_compl_pat=mkb_compl_pat1, mkb_assoc_pat=mkb_assoc_pat1)
        chb1_id = self.env.update_childbirth(chb, chb1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]
        # O95_compl_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_main_pat1)
        # O96_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_compl_pat1[0])
        # J01_1_assoc_ds_id = self._get_ds_id_from_diags(chb_diags, mkb_assoc_pat1[0])

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb2,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date, ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_cb2[0],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_assoc_cb2[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_main_pat1,
                                                  diagnosis_types=dict(self._pat_main(), **self._final_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_pat1[0],
                                                  diagnosis_types=dict(self._pat_compl(), **self._final_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_assoc_pat1[0],
                                                  diagnosis_types=dict(self._pat_assoc(), **self._final_assoc()),
                                                  dg_set_date=ep2_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # remove pat diags
        mkb_main_cb3 = 'Z35.2'
        mkb_compl_cb3 = ['O20']
        mkb_assoc_cb3 = ['J01']
        mkb_main_pat2 = None
        mkb_compl_pat2 = None
        mkb_assoc_pat2 = None
        chb = self._change_test_childbirth_data(chb, mkb_main=mkb_main_cb3, mkb_compl=mkb_compl_cb3,
            mkb_assoc=mkb_assoc_cb3, mkb_main_pat=mkb_main_pat2, mkb_compl_pat=mkb_compl_pat2,
            mkb_assoc_pat=mkb_assoc_pat2)
        chb1_id = self.env.update_childbirth(chb, chb1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        chb_diags = act_diags_map[chb1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main_cb3,
                                                  diagnosis_types=dict(self._final_main(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date, ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_compl_cb3[0],
                                                  diagnosis_types=dict(self._final_compl(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date),
                          self.make_expected_diag(ds_set_date=ep2_date, mkb=mkb_assoc_cb3[0],
                                                  diagnosis_types=dict(self._final_assoc(), **self._pat_assoc()),
                                                  dg_set_date=ep2_date)]
        self.assertDiagsLikeExpected(chb_diags, expected_diags)

        # delete ep
        self.env.delete_childbirth()
        insp1_diags = self.env.get_diagnoses_by_action()[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date,
                                                  ds_id=compl_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date,
                                                  ds_id=assoc_mkb_ds_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)


class SingleInspectionCases(BaseDiagTest):

    # @unittest.skip('debug')
    def test_single_inspection_dates(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main1 = 'D01'
        mkb_compl1 = ['N01']
        mkb_assoc1 = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main1, mkb_compl=mkb_compl1, mkb_assoc=mkb_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        D01_ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb_main1)
        N01_ds_compl_id = self._get_ds_id_from_diags(insp1_diags, mkb_compl1[0])
        G01_ds_assoc_id = self._get_ds_id_from_diags(insp1_diags, mkb_assoc1[0])

        # test date moved to right
        a2_date = '2016-06-17'
        insp1 = self._change_test_prinsp_data(insp1, date=a2_date)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test date moved to left
        a3_date = '2016-03-25'
        insp1 = self._change_test_prinsp_data(insp1, date=a3_date)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a3_date, mkb=mkb_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test date moved to right, change diags
        a4_date = '2016-06-19'
        mkb_main2 = 'Z34.0'
        mkb_compl2 = ['N01', 'N06']
        mkb_assoc2 = ['H00']
        insp1 = self._change_test_prinsp_data(insp1, date=a4_date, mkb_main=mkb_main2, mkb_compl=mkb_compl2,
            mkb_assoc=mkb_assoc2)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a4_date),
                          self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date),
                          self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_compl2[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date),
                          self.make_expected_diag(ds_set_date=a4_date, mkb=mkb_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a4_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test date moved to left, change diags
        a5_date = '2016-06-07'
        mkb_main3 = 'Z35.1'
        mkb_compl3 = None
        mkb_assoc3 = None
        insp1 = self._change_test_prinsp_data(insp1, date=a5_date, mkb_main=mkb_main3, mkb_compl=mkb_compl3,
            mkb_assoc=mkb_assoc3)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a5_date, mkb=mkb_main3,
                                                  diagnosis_types=self._final_main(), dg_set_date=a5_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)


class InspectionSeqTest(BaseDiagTest):

    def setUp(self):
        super(InspectionSeqTest, self).setUp()
        self._state = None
        self._create_initial_inspections()

    def tearDown(self):
        super(InspectionSeqTest, self).tearDown()

    def _create_initial_inspections(self):
        a1_date1 = '2016-04-30'
        hosp1_code = TEST_DATA['person1']['hosp']
        doctor1_code = TEST_DATA['person1']['doctor']
        mkb1_main1 = 'D01'
        mkb1_compl1 = ['N01']
        mkb1_assoc1 = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date1,
            hospital=hosp1_code, doctor=doctor1_code, mkb_main=mkb1_main1, mkb_compl=mkb1_compl1,
            mkb_assoc=mkb1_assoc1)
        insp1_id = self.env.update_first_inspection(insp1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        D01_ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb1_main1)
        N01_ds_compl_id = self._get_ds_id_from_diags(insp1_diags, mkb1_compl1[0])
        G01_ds_assoc_id = self._get_ds_id_from_diags(insp1_diags, mkb1_assoc1[0])

        # 2nd
        a2_date1 = '2016-06-29'
        hosp2_code = TEST_DATA['person1']['hosp']
        doctor2_code = TEST_DATA['person1']['doctor']
        mkb2_main1 = 'Z34.0'
        mkb2_compl1 = ['N01']
        mkb2_assoc1 = ['G01', 'G02']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date1,
            hospital=hosp2_code, doctor=doctor2_code, mkb_main=mkb2_main1, mkb_compl=mkb2_compl1,
            mkb_assoc=mkb2_assoc1)
        insp2_id = self.env.update_second_inspection(insp2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        Z34_0_ds_main_id = self._get_ds_id_from_diags(insp2_diags, mkb2_main1)
        G02_ds_assoc_id = self._get_ds_id_from_diags(insp2_diags, mkb2_assoc1[1])

        # 3rd
        a3_date1 = '2016-07-20'
        a3_external_id = 'a3'
        hosp3_code = TEST_DATA['person1']['hosp']
        doctor3_code = TEST_DATA['person1']['doctor']
        mkb3_main1 = 'Z34.0'
        mkb3_compl1 = ['N01', 'N02']
        mkb3_assoc1 = ['G02', 'G03']
        insp3 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a3_date1, external_id=a3_external_id,
            hospital=hosp3_code, doctor=doctor3_code, mkb_main=mkb3_main1, mkb_compl=mkb3_compl1,
            mkb_assoc=mkb3_assoc1)
        insp3_id = self.env.update_second_inspection(insp3, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp3_diags = act_diags_map[insp3_id]

        N02_ds_compl_id = self._get_ds_id_from_diags(insp3_diags, mkb3_compl1[1])
        G03_ds_assoc_id = self._get_ds_id_from_diags(insp3_diags, mkb3_assoc1[1])

        self._state = locals()


class ChangeInspectionsDatesCases(InspectionSeqTest):

    # @unittest.skip('debug')
    def test_multiple_sequential_inspections_dates(self):
        """Последовательное добавление осмотров / изменение дат уже существующих
        без перескоков друг относительно друга / удаление"""
        # current state variables
        a1_date1 = self._state['a1_date1']
        a2_date1 = self._state['a2_date1']
        a3_date1 = self._state['a3_date1']
        mkb2_main1 = self._state['mkb2_main1']  # 'Z34.0'
        mkb2_compl1 = self._state['mkb2_compl1']  # ['N01']
        mkb2_assoc1 = self._state['mkb2_assoc1']  # ['G01', 'G02']
        mkb3_main1 = self._state['mkb3_main1']  # 'Z34.0'
        mkb3_compl1 = self._state['mkb3_compl1']  # ['N01', 'N02']
        mkb3_assoc1 = self._state['mkb3_assoc1']  # ['G02', 'G03']
        Z34_0_ds_main_id = self._state['Z34_0_ds_main_id']
        N01_ds_compl_id = self._state['N01_ds_compl_id']
        N02_ds_compl_id = self._state['N02_ds_compl_id']
        D01_ds_main_id = self._state['D01_ds_main_id']
        G01_ds_assoc_id = self._state['G01_ds_assoc_id']
        G02_ds_assoc_id = self._state['G02_ds_assoc_id']
        G03_ds_assoc_id = self._state['G03_ds_assoc_id']

        # move 1st left, change diags
        a1_date2 = '2016-04-25'
        mkb1_main2 = 'D01'
        mkb1_compl2 = ['N01']
        mkb1_assoc2 = ['G02']
        insp1 = self._change_test_prinsp_data(self._state['insp1'], date=a1_date2,
            mkb_main=mkb1_main2, mkb_compl=mkb1_compl2, mkb_assoc=mkb1_assoc2)
        insp1_id = self.env.update_first_inspection(insp1, self._state['insp1_id'])

        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date2,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date2,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date2,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp2_diags = act_diags_map[self._state['insp2_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # move 2nd right, change diags
        a2_date2 = '2016-07-05'
        mkb2_main2 = 'Z34.0'
        mkb2_compl2 = None
        mkb2_assoc2 = ['G01', 'G02']
        insp2 = self._change_test_repinsp_data(self._state['insp2'], date=a2_date2,
            mkb_main=mkb2_main2, mkb_compl=mkb2_compl2, mkb_assoc=mkb2_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, self._state['insp2_id'])

        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date2, mkb=mkb2_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date2,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a2_date2, mkb=mkb2_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date2,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb2_assoc2[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date2,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        a2_beforedate = (datetime.datetime.strptime(a2_date2, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date2,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date2,
                                                  ds_id=N01_ds_compl_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date2,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date2, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)
        new_N01_ds_compl_id = self._get_ds_id_from_diags(insp3_diags, mkb3_compl1[0])
        self.assertNotEqual(new_N01_ds_compl_id, N01_ds_compl_id)

        # del 2nd
        self.env.delete_second_inspection(insp2_id)

        act_diags_map = self.env.get_diagnoses_by_action()

        a3_beforedate = (datetime.datetime.strptime(a3_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        insp1_diags = act_diags_map[insp1_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date2,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date2,
                                                  ds_id=N01_ds_compl_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb1_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date2,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date2, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)

    # @unittest.skip('debug')
    def test_inspections_shifting(self):
        """Изменение дат уже существующих осмотров с перескоком через
        другие осмотры / удаление"""
        # current state variables
        a1_date1 = self._state['a1_date1']
        a2_date1 = self._state['a2_date1']
        a3_date1 = self._state['a3_date1']
        mkb1_main1 = self._state['mkb1_main1']  # 'D01'
        mkb1_compl1 = self._state['mkb1_compl1']  # ['N01']
        mkb1_assoc1 = self._state['mkb1_assoc1']  # ['G01']
        mkb2_main1 = self._state['mkb2_main1']  # 'Z34.0'
        mkb2_compl1 = self._state['mkb2_compl1']  # ['N01']
        mkb2_assoc1 = self._state['mkb2_assoc1']  # ['G01', 'G02']
        mkb3_main1 = self._state['mkb3_main1']  # 'Z34.0'
        mkb3_compl1 = self._state['mkb3_compl1']  # ['N01', 'N02']
        mkb3_assoc1 = self._state['mkb3_assoc1']  # ['G02', 'G03']
        Z34_0_ds_main_id = self._state['Z34_0_ds_main_id']
        N01_ds_compl_id = self._state['N01_ds_compl_id']
        N02_ds_compl_id = self._state['N02_ds_compl_id']
        D01_ds_main_id = self._state['D01_ds_main_id']
        G01_ds_assoc_id = self._state['G01_ds_assoc_id']
        G02_ds_assoc_id = self._state['G02_ds_assoc_id']
        G03_ds_assoc_id = self._state['G03_ds_assoc_id']

        # move 2nd inspection after 3rd
        a2_date2 = '2016-08-15'
        mkb2_main2 = 'Z34.0'
        mkb2_compl2 = ['N01']
        mkb2_assoc2 = ['G02', 'G03']
        insp2 = self._change_test_repinsp_data(self._state['insp2'], date=a2_date2,
            mkb_main=mkb2_main2, mkb_compl=mkb2_compl2, mkb_assoc=mkb2_assoc2)
        insp2_id = self.env.update_second_inspection(insp2, self._state['insp2_id'])

        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_main2,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date2,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_assoc2[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date2,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_assoc2[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date2,
                                                  ds_id=G03_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl2[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date2,
                                                  ds_id=N01_ds_compl_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        a2_beforedate = (datetime.datetime.strptime(a2_date2, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        a3_beforedate = (datetime.datetime.strptime(a3_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        insp1_diags = act_diags_map[self._state['insp1_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date1,
                                                  ds_id=D01_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date1,
                                                  ds_id=G01_ds_assoc_id, ds_end_date=a3_beforedate)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)

        # insert insp between 3 and 2
        a4_date1 = '2016-07-29'
        a4_external_id = 'a4'
        hosp4_code = TEST_DATA['person1']['hosp']
        doctor4_code = TEST_DATA['person1']['doctor']
        mkb4_main1 = 'Z34.0'
        mkb4_compl1 = ['N01', 'N02']
        mkb4_assoc1 = ['G01']
        insp4 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a4_date1, external_id=a4_external_id,
            hospital=hosp4_code, doctor=doctor4_code, mkb_main=mkb4_main1, mkb_compl=mkb4_compl1,
            mkb_assoc=mkb4_assoc1)
        insp4_id = self.env.update_second_inspection(insp4, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp4_diags = act_diags_map[insp4_id]

        new_G01_ds_assoc_id = self._get_ds_id_from_diags(insp4_diags, mkb4_assoc1[0])
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb4_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a4_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb4_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb4_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=N02_ds_compl_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a4_date1, mkb=mkb4_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a4_date1,
                                                  ds_id=new_G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp4_diags, expected_diags)
        # insp3 and insp2 diags should be ok...
        insp2_diags = act_diags_map[insp2_id]
        new_G02_ds_assoc_id = self._get_ds_id_from_diags(insp2_diags, mkb3_assoc1[0])
        new_G03_ds_assoc_id = self._get_ds_id_from_diags(insp2_diags, mkb3_assoc1[1])

        # move 2 to left between 3 and 4
        a2_date3 = '2016-07-25'
        mkb2_main3 = 'Z34.0'
        mkb2_compl3 = ['N01']
        mkb2_assoc3 = ['G01', 'G02', 'G03']
        insp2 = self._change_test_repinsp_data(insp2, date=a2_date3,
            mkb_main=mkb2_main3, mkb_compl=mkb2_compl3, mkb_assoc=mkb2_assoc3)
        insp2_id = self.env.update_second_inspection(insp2, insp2_id)

        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]
        a4_beforedate = (datetime.datetime.strptime(a4_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_main3,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date3,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a2_date3, mkb=mkb2_assoc3[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date3,
                                                  ds_id=new_G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_assoc3[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date3,
                                                  ds_id=G02_ds_assoc_id, ds_end_date=a4_beforedate),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb2_assoc3[2],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date3,
                                                  ds_id=G03_ds_assoc_id, ds_end_date=a4_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl3[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date3,
                                                  ds_id=N01_ds_compl_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        a2_beforedate = (datetime.datetime.strptime(a2_date3, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id, ds_end_date=a4_beforedate),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id, ds_end_date=a4_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id, ds_end_date=a2_beforedate)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)

        insp4_diags = act_diags_map[insp4_id]
        new_N02_ds_compl_id = self._get_ds_id_from_diags(insp4_diags, mkb4_compl1[1])
        a2_beforedate = (datetime.datetime.strptime(a2_date2, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb4_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a4_date1,
                                                  ds_id=Z34_0_ds_main_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb4_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a4_date1, mkb=mkb4_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=new_N02_ds_compl_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a2_date3, mkb=mkb4_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a4_date1,
                                                  ds_id=new_G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp4_diags, expected_diags)
        new_G02_ds_assoc_id_deleted = db.engine.execute('select deleted from Diagnosis where id = {0}'.format(
            new_G02_ds_assoc_id)).first()[0]
        self.assertEqual(new_G02_ds_assoc_id_deleted, 1)


class MeasureResultsExtendedCases(InspectionSeqTest):

    # @unittest.skip('debug')
    def test_measure_result_with_existing_ds(self):
        """Добавление результата мероприятия с уже существующим диагнозом"""
        # current state variables
        a1_date1 = self._state['a1_date1']
        a2_date1 = self._state['a2_date1']
        a3_date1 = self._state['a3_date1']
        mkb1_main1 = self._state['mkb1_main1']  # 'D01'
        mkb1_compl1 = self._state['mkb1_compl1']  # ['N01']
        mkb1_assoc1 = self._state['mkb1_assoc1']  # ['G01']
        mkb2_main1 = self._state['mkb2_main1']  # 'Z34.0'
        mkb2_compl1 = self._state['mkb2_compl1']  # ['N01']
        mkb2_assoc1 = self._state['mkb2_assoc1']  # ['G01', 'G02']
        mkb3_main1 = self._state['mkb3_main1']  # 'Z34.0'
        mkb3_compl1 = self._state['mkb3_compl1']  # ['N01', 'N02']
        mkb3_assoc1 = self._state['mkb3_assoc1']  # ['G02', 'G03']
        Z34_0_ds_main_id = self._state['Z34_0_ds_main_id']
        N01_ds_compl_id = self._state['N01_ds_compl_id']
        N02_ds_compl_id = self._state['N02_ds_compl_id']
        D01_ds_main_id = self._state['D01_ds_main_id']
        G01_ds_assoc_id = self._state['G01_ds_assoc_id']
        G02_ds_assoc_id = self._state['G02_ds_assoc_id']
        G03_ds_assoc_id = self._state['G03_ds_assoc_id']

        # add emr after 3rd
        emr1_external_id = 'emr1'
        emr1_measure_code = TEST_DATA['measure_spec_checkup1']['measure_code']
        emr1_date1 = '2016-07-29'
        emr1_hosp_code1 = TEST_DATA['person1']['hosp']
        emr1_doctor_code1 = TEST_DATA['person1']['doctor']
        emr1_mkb1 = 'N01'
        emr1 = self._change_test_specialist_checkup_emr_data(deepcopy(self.emr_spec_ch1),
             external_id=emr1_external_id, date=emr1_date1, measure_code=emr1_measure_code,
             hospital=emr1_hosp_code1, doctor=emr1_doctor_code1, mkb=emr1_mkb1)
        em1 = self.env.update_specialist_checkup_emr(emr1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=emr1_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=emr1_date1,
                                                  ds_id=N02_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)

        # add emr between 1 and 2
        emr2_external_id = 'emr2'
        emr2_measure_code = TEST_DATA['measure_spec_checkup1']['measure_code']
        emr2_date1 = '2016-06-10'
        emr2_hosp_code1 = TEST_DATA['person1']['hosp']
        emr2_doctor_code1 = TEST_DATA['person1']['doctor']
        emr2_mkb1 = 'G01'
        emr2 = self._change_test_specialist_checkup_emr_data(deepcopy(self.emr_spec_ch1),
             external_id=emr2_external_id, date=emr2_date1, measure_code=emr2_measure_code,
             hospital=emr2_hosp_code1, doctor=emr2_doctor_code1, mkb=emr2_mkb1)
        em2 = self.env.update_specialist_checkup_emr(emr2, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[self._state['insp1_id']]

        a2_beforedate = (datetime.datetime.strptime(a2_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr2_date1,
                                                  ds_id=D01_ds_main_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=emr2_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr2_date1,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp2_diags = act_diags_map[self._state['insp2_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

    # @unittest.skip('debug')
    def test_measure_result_change_dates(self):
        """Добавление результата мероприятия с уже существующим диагнозом"""
        # current state variables
        a1_date1 = self._state['a1_date1']
        a2_date1 = self._state['a2_date1']
        a3_date1 = self._state['a3_date1']
        mkb1_main1 = self._state['mkb1_main1']  # 'D01'
        mkb1_compl1 = self._state['mkb1_compl1']  # ['N01']
        mkb1_assoc1 = self._state['mkb1_assoc1']  # ['G01']
        mkb2_main1 = self._state['mkb2_main1']  # 'Z34.0'
        mkb2_compl1 = self._state['mkb2_compl1']  # ['N01']
        mkb2_assoc1 = self._state['mkb2_assoc1']  # ['G01', 'G02']
        mkb3_main1 = self._state['mkb3_main1']  # 'Z34.0'
        mkb3_compl1 = self._state['mkb3_compl1']  # ['N01', 'N02']
        mkb3_assoc1 = self._state['mkb3_assoc1']  # ['G02', 'G03']
        Z34_0_ds_main_id = self._state['Z34_0_ds_main_id']
        N01_ds_compl_id = self._state['N01_ds_compl_id']
        N02_ds_compl_id = self._state['N02_ds_compl_id']
        D01_ds_main_id = self._state['D01_ds_main_id']
        G01_ds_assoc_id = self._state['G01_ds_assoc_id']
        G02_ds_assoc_id = self._state['G02_ds_assoc_id']
        G03_ds_assoc_id = self._state['G03_ds_assoc_id']

        # add emr between 1 and 2
        emr1_external_id = 'emr1'
        emr1_measure_code = TEST_DATA['measure_spec_checkup1']['measure_code']
        emr1_date1 = '2016-06-10'
        emr1_hosp_code1 = TEST_DATA['person1']['hosp']
        emr1_doctor_code1 = TEST_DATA['person1']['doctor']
        emr1_mkb1 = 'W05'
        emr1 = self._change_test_specialist_checkup_emr_data(deepcopy(self.emr_spec_ch1),
             external_id=emr1_external_id, date=emr1_date1, measure_code=emr1_measure_code,
             hospital=emr1_hosp_code1, doctor=emr1_doctor_code1, mkb=emr1_mkb1)
        em1 = self.env.update_specialist_checkup_emr(emr1, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[self._state['insp1_id']]

        a2_beforedate = (datetime.datetime.strptime(a2_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        W05_ds_assoc_id = self._get_ds_id_from_diags(insp1_diags, emr1_mkb1)
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date1,
                                                  ds_id=D01_ds_main_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=emr1_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date1,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=emr1_date1, mkb=emr1_mkb1,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date1,
                                                  ds_id=W05_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp2_diags = act_diags_map[self._state['insp2_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date1,
                                                  ds_id=G02_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        # move em1 after inpsp2
        emr1_date2 = '2016-07-09'
        emr1_mkb2 = 'W05'
        emr1 = self._change_test_specialist_checkup_emr_data(emr1, date=emr1_date2, mkb=emr1_mkb2)
        em1 = self.env.update_specialist_checkup_emr(emr1, em1.resultAction_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[self._state['insp1_id']]

        a2_beforedate = (datetime.datetime.strptime(a2_date1, "%Y-%m-%d") - datetime.timedelta(seconds=1))
        expected_diags = [self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a1_date1,
                                                  ds_id=D01_ds_main_id, ds_end_date=a2_beforedate),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a1_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb1_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a1_date1,
                                                  ds_id=G01_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        insp2_diags = act_diags_map[self._state['insp2_id']]
        new_W05_ds_assoc_id = self._get_ds_id_from_diags(insp2_diags, emr1_mkb1)
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=emr1_date2,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=emr1_date2,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb2_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date2,
                                                  ds_id=G01_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb2_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date2,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=emr1_date2, mkb=emr1_mkb1,
                                                  diagnosis_types=self._final_assoc(), dg_set_date=emr1_date2,
                                                  ds_id=new_W05_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp2_diags, expected_diags)

        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N02_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a3_date1, mkb=mkb3_assoc1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G03_ds_assoc_id)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)


class BorderingDatesCases(InspectionSeqTest):

    # @unittest.skip('debug')
    def test_inspection_border_dates(self):
        """Добавление осмотра с датой начала как у уже имеющихся осмотров"""
        # current state variables
        a1_date1 = self._state['a1_date1']
        a2_date1 = self._state['a2_date1']
        a3_date1 = self._state['a3_date1']
        mkb2_main1 = self._state['mkb2_main1']  # 'Z34.0'
        mkb2_compl1 = self._state['mkb2_compl1']  # ['N01']
        mkb2_assoc1 = self._state['mkb2_assoc1']  # ['G01', 'G02']
        mkb3_main1 = self._state['mkb3_main1']  # 'Z34.0'
        mkb3_compl1 = self._state['mkb3_compl1']  # ['N01', 'N02']
        mkb3_assoc1 = self._state['mkb3_assoc1']  # ['G02', 'G03']
        Z34_0_ds_main_id = self._state['Z34_0_ds_main_id']
        N01_ds_compl_id = self._state['N01_ds_compl_id']
        N02_ds_compl_id = self._state['N02_ds_compl_id']
        D01_ds_main_id = self._state['D01_ds_main_id']
        G01_ds_assoc_id = self._state['G01_ds_assoc_id']
        G02_ds_assoc_id = self._state['G02_ds_assoc_id']
        G03_ds_assoc_id = self._state['G03_ds_assoc_id']

        # insert insp after 3
        a4_date1 = a3_date1
        a4_external_id = 'a4'
        hosp4_code = TEST_DATA['person1']['hosp']
        doctor4_code = TEST_DATA['person1']['doctor']
        mkb4_main1 = 'Z34.0'
        mkb4_compl1 = ['N01', 'W01']
        mkb4_assoc1 = ['G02']
        insp4 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a4_date1, external_id=a4_external_id,
            hospital=hosp4_code, doctor=doctor4_code, mkb_main=mkb4_main1, mkb_compl=mkb4_compl1,
            mkb_assoc=mkb4_assoc1)
        insp4_id = self.env.update_second_inspection(insp4, None)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp4_diags = act_diags_map[insp4_id]

        W01_ds_compl_id = self._get_ds_id_from_diags(insp4_diags, mkb4_compl1[1])
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb4_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a4_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb4_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=N01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a4_date1, mkb=mkb4_compl1[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a4_date1,
                                                  ds_id=W01_ds_compl_id, ds_end_date=None),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb4_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a4_date1,
                                                  ds_id=G02_ds_assoc_id, ds_end_date=None)]
        self.assertDiagsLikeExpected(insp4_diags, expected_diags)

        insp3_diags = act_diags_map[self._state['insp3_id']]
        expected_diags = [self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_main1,
                                                  diagnosis_types=self._final_main(), dg_set_date=a3_date1,
                                                  ds_id=Z34_0_ds_main_id),
                          self.make_expected_diag(ds_set_date=a1_date1, mkb=mkb3_compl1[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a3_date1,
                                                  ds_id=N01_ds_compl_id),
                          self.make_expected_diag(ds_set_date=a2_date1, mkb=mkb3_assoc1[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=G02_ds_assoc_id),
                          self.make_expected_diag(ds_set_date=a4_date1, mkb=mkb4_compl1[1],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a3_date1,
                                                  ds_id=W01_ds_compl_id, ds_end_date=None)]
        self.assertDiagsLikeExpected(insp3_diags, expected_diags)


def get_application():
    from nemesis.app import app
    from tsukino_usagi.client import TsukinoUsagiClient

    class HippoUsagiTestClient(TsukinoUsagiClient):
        def on_configuration(self, configuration):
            configuration['APP_VERSION'] = 'TEST_VERSION'
            configuration['SQLALCHEMY_ECHO'] = False
            app.config.update(configuration)
            self.bootstrap_test_app()

            from blueprints.accounting.app import module as accounting_module
            from blueprints.reports.app import module as reports_module
            from blueprints.anareports.app import module as anareports_module
            from blueprints.biomaterials.app import module as biomaterials_module
            from blueprints.event.app import module as event_module
            from blueprints.patients.app import module as patients_module
            from blueprints.schedule.app import module as schedule_module
            from blueprints.actions.app import module as actions_module
            from blueprints.useraccount.app import module as useraccount_module
            from blueprints.risar.app import module as risar_module

            app.register_blueprint(accounting_module, url_prefix='/accounting')
            app.register_blueprint(reports_module, url_prefix='/reports')
            app.register_blueprint(anareports_module, url_prefix='/anareports')
            app.register_blueprint(biomaterials_module, url_prefix='/biomaterials')
            app.register_blueprint(event_module, url_prefix='/event')
            app.register_blueprint(patients_module, url_prefix='/patients')
            app.register_blueprint(schedule_module, url_prefix='/schedule')
            app.register_blueprint(actions_module, url_prefix='/actions')
            app.register_blueprint(useraccount_module, url_prefix='/user')
            app.register_blueprint(risar_module, url_prefix='/risar')

            logger = logging.getLogger('simple')
            logger.setLevel(logging.INFO)

        def bootstrap_test_app(self, templates_dir=None):
            import pytz
            from nemesis.systemwide import db, cache, babel, login_manager
            from nemesis.app import init_logger

            if templates_dir:
                app.template_folder = templates_dir

            db.init_app(app)
            babel.init_app(app)
            login_manager.init_app(app)
            cache.init_app(app)

            @babel.timezoneselector
            def get_timezone():
                return pytz.timezone(app.config['TIME_ZONE'])

            import nemesis.models
            import nemesis.views
            import nemesis.context_processors

            init_logger()

    usagi = HippoUsagiTestClient(app.wsgi_app, os.getenv('TSUKINO_USAGI_URL', 'http://127.0.0.1:6602/'), 'hippo')
    app.wsgi_app = usagi.app
    usagi()
    return app


def set_current_user_in_app(user):
    from flask import _request_ctx_stack
    _request_ctx_stack.top.user = user


def get_user(login):
    from nemesis.app import app
    from nemesis.models.person import Person
    from nemesis.lib.user import User
    with app.app_context():
        person = db.session.query(Person).filter(Person.login == login).first()
        return User(person)


if __name__ == '__main__':
    coldstar_url = os.getenv('TEST_COLDSTAR_URL', 'http://127.0.0.1:6098')
    mis_url = os.getenv('TEST_MIS_URL', 'http://127.0.0.1:6600')
    auth_token_name = 'CastielAuthToken'
    session_token_name = 'hippocrates.session.id'
    login = os.getenv('TEST_LOGIN', u'ВнешСис')
    password = os.getenv('TEST_PASSWORD', '')

    client_id = 17739
    card_id = 278

    BaseDiagTest.parametrize(client_id, card_id)

    app = get_application()
    user = get_user(login)

    # emulate user login
    req_ctx = app.test_request_context()
    req_ctx.push()
    set_current_user_in_app(user)

    with app.app_context():
        suite1 = unittest.TestLoader().loadTestsFromTestCase(SimpleTestCases)
        suite2 = unittest.TestLoader().loadTestsFromTestCase(MeasureResultsCases)
        suite3 = unittest.TestLoader().loadTestsFromTestCase(InspectionPCCases)
        suite4 = unittest.TestLoader().loadTestsFromTestCase(InspectionPuerperaCases)
        suite5 = unittest.TestLoader().loadTestsFromTestCase(ChildbirthCases)
        suite6 = unittest.TestLoader().loadTestsFromTestCase(SingleInspectionCases)
        suite7 = unittest.TestLoader().loadTestsFromTestCase(ChangeInspectionsDatesCases)
        suite8 = unittest.TestLoader().loadTestsFromTestCase(MeasureResultsExtendedCases)
        suite9 = unittest.TestLoader().loadTestsFromTestCase(BorderingDatesCases)

        unittest.TextTestRunner(verbosity=2).run(
            unittest.TestSuite([
                suite1,
                suite2,
                suite3,
                suite4,
                suite5,
                suite6,
                suite7,
                suite8,
                suite9
            ])
        )

        # TestEnvironment(client_id, card_id)._delete_everything()
