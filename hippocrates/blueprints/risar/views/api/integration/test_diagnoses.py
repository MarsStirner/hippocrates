# coding: utf-8

import os
import unittest
import logging

from copy import deepcopy
from sqlalchemy import text

from blueprints.risar.lib.card import PregnancyCard, _clear_caches as clear_preg_card_cache
from blueprints.risar.lib.represent import represent_action_diagnoses
from blueprints.risar.views.api.integration.checkup_obs_first.xform import CheckupObsFirstXForm
from blueprints.risar.views.api.integration.checkup_obs_second.xform import CheckupObsSecondXForm
from blueprints.risar.views.api.integration.utils import get_person_by_codes
from nemesis.systemwide import db
from nemesis.lib.utils import safe_dict, safe_date, safe_datetime
from nemesis.models.event import Event


class TestEnvironment(object):

    def __init__(self, client_id, card_id=None):
        self.client_id = client_id
        self.card_id = card_id
        self.refresh()

    def refresh(self):
        event = Event.query.get(self.card_id)
        self.card = PregnancyCard.get_for_event(event)
        self.card.get_card_attrs_action(True)
        self.insp_list = []
        self.emr_list = []

        self.initialize()

    def initialize(self):
        if not self.card_id:
            self.card = self.create_new_card()
            self.card_id = self.card.event.id

    def close(self):
        self._delete_everything()
        clear_preg_card_cache()
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
        db.engine.execute(text(u'delete from EventMeasure where event_id = {0}'.format(self.card_id)).execution_options(autocommit=False))
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

    def get_card_diagnoses(self):
        # todo:
        # for print only purposes
        # get all diagnoses by dates, get all diagnostics by diagnoses,
        # get all associations, then format
        diagns = self.card.get_client_diagnostics(self.card.event.setDate, self.card.event.execDate, True)
        return {
            'diagns': diagns
        }

    def get_diagnoses_by_action(self):
        return dict(
            (action.id, [self._make_diagnosis_info(diag_data)
                         for diag_data in represent_action_diagnoses(action)])
            for action in self.insp_list
        )

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

    def update_first_inspection(self, data, idx=None, create=False, api_version=0):
        inspection_id = self.insp_list[idx].id if not create and idx is not None else None

        # why order matters? insert as is?
        xform = CheckupObsFirstXForm(api_version, create)
        xform.check_params(inspection_id, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        db.session.commit()
        xform.generate_measures()
        if create:
            if idx is not None:
                self.insp_list.insert(idx, xform.target_obj)
            else:
                self.insp_list.append(xform.target_obj)
        return xform.target_obj.id

    def update_second_inspection(self, data, idx=None, create=False, api_version=0):
        inspection_id = self.insp_list[idx].id if not create and idx is not None else None

        # why order matters? insert as is?
        xform = CheckupObsSecondXForm(api_version, create)
        xform.check_params(inspection_id, self.card_id, data)
        xform.update_target_obj(data)
        xform.store()
        xform.reevaluate_data()
        db.session.commit()
        xform.generate_measures()
        if create:
            if idx is not None:
                self.insp_list.insert(idx, xform.target_obj)
            else:
                self.insp_list.append(xform.target_obj)
        return xform.target_obj.id

    def add_em_w_result(self):
        pass


class BaseDiagTest(unittest.TestCase):
    client_id = None
    card_id = None

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

    def assertDiagsLikeExpected(self, diag_list, expected_list, msg=None, print_comparable=False):
        if print_comparable:
            print self._formatComparedDiags(diag_list, expected_list)
        for expected in expected_list:
            for idx, diag in enumerate(diag_list):
                # try this diag
                for attr, exp_val in expected.iteritems():
                    if attr not in diag or diag[attr] != exp_val:
                        break
                else:
                    # this diag matches one of expected
                    break
            else:
                # neither of diags matches expected
                break
            # diag at idx mathces one of expected, remove it
            del diag_list[idx]
        else:
            if len(diag_list) == 0:
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
            'ds_end_date': lambda x: safe_datetime(safe_date(x)),
            'ds_person': lambda x: get_person_by_codes(*self._decode_person_codes(x)).id,
            'mkb': lambda x: x,
            'diagnosis_types': lambda x: x,
            'dg_id': lambda x: x,
            'dg_set_date': lambda x: safe_datetime(safe_date(x)),
            'dg_end_date': lambda x: safe_datetime(safe_date(x)),
            'dg_create_date': lambda x: safe_datetime(safe_date(x)),
            'dg_person': lambda x: get_person_by_codes(*self._decode_person_codes(x)).id,
            'dg_action_id': lambda x: x,
        }
        return dict((k, conv[k](v)) for k, v in kwargs.items())

    def _final_main(self):
        return {'final': 'main'}

    def _final_compl(self):
        return {'final': 'complication'}

    def _final_assoc(self):
        return {'final': 'associated'}

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


class SimpleTestCases(BaseDiagTest):

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

    def test_single_inspection(self):
        a_date = '2016-04-30'
        hosp_code = '-1'
        doctor_code = '22'
        mkb_main = 'D01'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None, True)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a_date)]
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

        # todo: change person
        a_date = '2016-03-25'
        mkb_main = 'D03'
        mkb_compl = None
        insp1 = self._change_test_prinsp_data(insp1, mkb_main=mkb_main, mkb_compl=mkb_compl)
        self.env.update_first_inspection(insp1, 0)  # todo: idx
        act_diags_map = self.env.get_diagnoses_by_action()
        insp1_diags = act_diags_map[insp1_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a_date),
                          self.make_expected_diag(ds_set_date=a_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a_date)]
        # todo: как проверить, что было удалено?
        self.assertDiagsLikeExpected(insp1_diags, expected_diags)

    def test_2_inspections_base(self):
        a1_date = '2016-04-30'
        hosp_code = '-1'
        doctor_code = '22'
        mkb_main = 'D01'
        mkb_compl = ['N01']
        mkb_assoc = ['G01']
        insp1 = self._change_test_prinsp_data(deepcopy(self.prim_insp1), date=a1_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp1_id = self.env.update_first_inspection(insp1, None, True)
        insp2_diags = self.env.get_diagnoses_by_action()[insp1_id]
        for d in insp2_diags:
            if d['mkb'] == mkb_main:
                main_mkb_ds_id = d['ds_id']

        a2_date = '2016-06-09'
        hosp_code = '-1'
        doctor_code = '22'
        mkb_main = 'D01'
        mkb_compl = ['H01', 'H02']
        mkb_assoc = ['G01']
        insp2 = self._change_test_repinsp_data(deepcopy(self.rep_insp1), date=a2_date,
            hospital=hosp_code, doctor=doctor_code, mkb_main=mkb_main, mkb_compl=mkb_compl, mkb_assoc=mkb_assoc)
        insp2_id = self.env.update_second_inspection(insp2, None, True)
        act_diags_map = self.env.get_diagnoses_by_action()
        insp2_diags = act_diags_map[insp2_id]

        expected_diags = [self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_main,
                                                  diagnosis_types=self._final_main(), dg_set_date=a2_date,
                                                  ds_id=main_mkb_ds_id),
                          self.make_expected_diag(ds_set_date=a1_date, mkb=mkb_assoc[0],
                                                  diagnosis_types=self._final_assoc(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl[0],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date),
                          self.make_expected_diag(ds_set_date=a2_date, mkb=mkb_compl[1],
                                                  diagnosis_types=self._final_compl(), dg_set_date=a2_date)]
        # как проверить, что было удалено?
        self.assertDiagsLikeExpected(insp2_diags, expected_diags, print_comparable=True)


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
