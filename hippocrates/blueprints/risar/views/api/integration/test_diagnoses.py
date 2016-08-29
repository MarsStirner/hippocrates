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
            'dg_end_date': data['diagnostic']['end_date'],
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
        db.session.commit()
        try:
            xform.generate_measures()
        except:
            print 'delete_first_inspection -> xform.generate_measures() error'

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
        db.session.commit()
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

    def update_specialist_checkup_emr(self, data, id_=None, api_version=0):
        create = id_ is None

        xform = SpecialistsCheckupXForm(api_version, create)
        # xform.validate(data)
        xform.check_params(id_, card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        db.session.commit()
        em = xform.get_em()
        if create:
            self.emr_map[em.id] = em
        return em


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
            chb['general_info']['maternity_hospital_doctor'] = kwargs['hospital']
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
        if 'checkup_date' in kwargs:
            emr['checkup_date'] = kwargs['checkup_date']
        if 'external_id' in kwargs:
            emr['external_id'] = emr['external_id']
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
    def test_single_inspection(self):
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
        ds_main_id = self._get_ds_id_from_diags(insp1_diags, mkb_main)
        dg_main_id_a1 = self._get_dg_id_from_diags(insp1_diags, mkb_main)

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
                                                  ds_id=ds_main_id, dg_id=dg_main_id_a1),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date),
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
                                                  ds_id=ds_main_id, dg_id=dg_main_id_a2),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date),
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

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # test date moved to left
        a_date = '2016-03-25'
        insp1 = self._change_test_prinsp_data(insp1, date=a_date)
        self.env.update_first_inspection(insp1, insp1_id)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]
        # todo: ids
        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

    # @unittest.skip('debug')
    def test_multiple_inspections_base(self):
        a1_date = '2016-04-30'
        hosp_code = TEST_DATA['person1']['hosp']
        doctor_code = TEST_DATA['person1']['doctor']
        mkb_main = 'D01'
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
        mkb_main2 = 'D01'
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
        mkb_main3 = 'D01'
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
        mkb_main4 = 'D01'
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
             measure_code=emr1_measure_code, checkup_date=emr1_date, hospital=emr1_hosp_code,
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


class MoarTestCases(BaseDiagTest):

    def test_3(self):
        self.assertEqual(1, 2, 'uf')

    def test_4(self):
        self.assertEqual(2, 2)


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
        suite2 = unittest.TestLoader().loadTestsFromTestCase(MoarTestCases)

        unittest.TextTestRunner(verbosity=2).run(
            unittest.TestSuite(
                [suite1,
                 #suite2
                 ]
            )
        )

        # TestEnvironment(client_id, card_id)._delete_everything()
