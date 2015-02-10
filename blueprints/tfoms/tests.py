# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
import unittest
import logging
import time

from lib.service_client import TFOMSClient
from lib.data import DownloadWorker
from .app import _config
from selenium import webdriver
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
import selenium.webdriver.support.ui as ui


from models import Template, TemplateType

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from application.app import app, db

logging.basicConfig()
logging.getLogger('suds.client').setLevel(logging.DEBUG)

db.app = app


class TestPatients(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.client = TFOMSClient(_config('core_service_url'))
            self.lpu_infis_code = _config('lpu_infis_code')
            self.app = app
            self.template_id = (db.session.query(Template)
                                .join(TemplateType)
                                .filter(TemplateType.code == 'patients')
                                .first())

    def tearDown(self):
        del self.client
        del self.app

    def testGetPatients(self):
        beginDate = datetime(2013, 01, 01)
        endDate = datetime(2013, 02, 01)
        patients = self.client.get_patients(self.lpu_infis_code, beginDate, endDate)
        if patients:
            self.assertIsInstance(patients, list)

    def testDowloadPatients(self):
        start = datetime(2013, 01, 01)
        end = datetime(2013, 02, 01)
        worker = DownloadWorker()
        with app.app_context():
            file_url = worker.do_download(self.template_id, start, end, self.lpu_infis_code)
            self.assertIsNotNone(file_url)


class TestServices(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.client = TFOMSClient(_config('core_service_url'))
            self.lpu_infis_code = _config('lpu_infis_code')
            self.app = app
            self.template_id = (db.session.query(Template)
                                .join(TemplateType)
                                .filter(TemplateType.code == 'services')
                                .first())

    def tearDown(self):
        del self.client
        del self.app

    def testGetServices(self):
        beginDate = datetime(2013, 01, 01)
        endDate = datetime(2013, 02, 01)
        patients = self.client.get_patients(self.lpu_infis_code, beginDate, endDate)
        patient_ids = []
        for patient in patients:
            patient_ids.append(patient.patientId)
            patients[patient.patientId] = patient

        services = self.client.get_patient_events(infis_code=self.lpu_infis_code,
                                                  start=beginDate,
                                                  end=endDate,
                                                  patients=patient_ids)
        if services:
            self.assertIsInstance(services, list)

    def testDowloadServices(self):
        start = datetime(2013, 01, 01)
        end = datetime(2013, 02, 01)
        worker = DownloadWorker()
        with app.app_context():
            file_url = worker.do_download(self.template_id, start, end, self.lpu_infis_code)
            self.assertIsNotNone(file_url)


class TestDBF(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.client = TFOMSClient(_config('core_service_url'))
            self.lpu_infis_code = _config('lpu_infis_code')
            self.app = app
            self.template_id = (db.session.query(Template)
                                .join(TemplateType)
                                .filter(TemplateType.code == 'dbf')
                                .first())

    def tearDown(self):
        del self.client
        del self.app

    def testGetDBFData(self):
        beginDate = datetime(2013, 01, 01)
        endDate = datetime(2013, 02, 01)
        patients = self.client.get_dbf_data(self.lpu_infis_code, beginDate, endDate)
        if patients:
            self.assertIsInstance(patients, list)

    def testDowloadDBF(self):
        start = datetime(2013, 01, 01)
        end = datetime(2013, 02, 01)
        worker = DownloadWorker()
        with app.app_context():
            file_url = worker.do_download(self.template_id, start, end, self.lpu_infis_code)
            self.assertIsNotNone(file_url)


class SimpleTestCase(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True

    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True


######## FireFox
class ClickTabs(SimpleTestCase):

    def test_click_tubs(self):
        driver = self.driver
        driver.get(self.base_url + "tfoms/")
        driver.find_element_by_link_text("Выгрузка").click()
        driver.find_element_by_link_text("Выгрузка DBF").click()
        driver.find_element_by_link_text("Загрузка").click()
        driver.find_element_by_link_text("Отчёты").click()
        #time.sleep(2)
        driver.find_element_by_id("drop1").click()
        wait = ui.WebDriverWait(self.driver, 15)
        wait.until(lambda driver: driver.find_element_by_class_name("dropdown-menu"))
        driver.find_element_by_link_text("Шаблоны").click()
        driver.find_element_by_link_text("Сведения об оказанной мед.помощи (XML)").click()
        driver.find_element_by_link_text("Поликлиника (DBF)").click()
        driver.find_element_by_link_text("Стационар (DBF)").click()

        time.sleep(1)
        driver.find_element_by_id("drop1").click()
        #time.sleep(2)
        wait = ui.WebDriverWait(self.driver, 15)
        wait.until(lambda driver: driver.find_element_by_class_name("dropdown-menu"))
        driver.find_element_by_link_text("Общие настройки").click()


class EmptyTemplateName(SimpleTestCase):

    def test_empty_template_name(self):
        driver = self.driver
        driver.get(self.base_url + "tfoms/settings_template/services/")
        driver.find_element_by_link_text("Сведения об оказанной мед.помощи (XML)").click()
        time.sleep(1)
        driver.find_element_by_id("Save").click()
        time.sleep(2)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Необходимо указать наименование шаблона![\s\S]*$")
        driver.find_element_by_link_text("Сведения о персональных данных (XML)").click()
        time.sleep(1)
        driver.find_element_by_id("Save").click()
        time.sleep(2)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Необходимо указать наименование шаблона![\s\S]*$")
        driver.find_element_by_link_text("Поликлиника (DBF)").click()
        time.sleep(1)
        driver.find_element_by_id("Save").click()
        time.sleep(2)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Необходимо указать наименование шаблона![\s\S]*$")
        driver.find_element_by_link_text("Стационар (DBF)").click()
        time.sleep(1)
        driver.find_element_by_id("Save").click()
        time.sleep(2)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Необходимо указать наименование шаблона![\s\S]*$")


class SaveDeleteNewTemplate(SimpleTestCase):

    def test_save_delete_new_template(self):
        #wait = ui.WebDriverWait(self.driver, 15)
        driver = self.driver
        driver.get(self.base_url + "tfoms/settings_template/patients/")
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate")
        driver.find_element_by_id("Save").click()
        self.assertTrue(self.is_element_present(By.LINK_TEXT, "TestTemplate"))
        time.sleep(3)
        driver.find_element_by_link_text("TestTemplate").click()
        time.sleep(1)
        driver.find_element_by_id("confirm-delete").click()
        time.sleep(1)
        link_yes = driver.find_element_by_xpath("//*[@id='modal-from-dom']/div[3]/a[2]")
        time.sleep(3)
        link_yes.click()
        #wait.until(lambda driver: driver.find_element_by_xpath("//*[@id='modal-from-dom'][contains(@style,'display: none')]"))
        time.sleep(4)
        deleteLinks = driver.find_elements_by_link_text("TestTemplate")
        self.assertTrue(not deleteLinks)

        driver.find_element_by_link_text("Сведения об оказанной мед.помощи (XML)").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_usl")
        driver.find_element_by_id("Save").click()
        time.sleep(1)
        self.assertTrue(self.is_element_present(By.LINK_TEXT, "TestTemplate_usl"))
        time.sleep(1)
        driver.find_element_by_id("confirm-delete").click()
        time.sleep(3)
        driver.find_element_by_xpath("//*[@id='modal-from-dom']/div[3]/a[2]").click()
        #wait.until(lambda driver: driver.find_element_by_xpath("//*[@id='modal-from-dom'][contains(@style,'display: none')]"))
        time.sleep(4)
        deleteLinks = driver.find_elements_by_link_text("TestTemplate_usl")
        self.assertTrue(not deleteLinks)

        driver.find_element_by_link_text("Поликлиника (DBF)").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_policlinic")
        driver.find_element_by_id("Save").click()
        time.sleep(1)
        self.assertTrue(self.is_element_present(By.LINK_TEXT, "TestTemplate_policlinic"))
        time.sleep(1)
        driver.find_element_by_id("confirm-delete").click()
        time.sleep(3)
        driver.find_element_by_xpath("//*[@id='modal-from-dom']/div[3]/a[2]").click()
        time.sleep(4)
        deleteLinks = driver.find_elements_by_link_text("TestTemplate_policlinic")
        self.assertTrue(not deleteLinks)

        driver.find_element_by_link_text("Стационар (DBF)").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_hospital")
        driver.find_element_by_id("Save").click()
        time.sleep(1)
        self.assertTrue(self.is_element_present(By.LINK_TEXT, "TestTemplate_hospital"))
        time.sleep(1)
        driver.find_element_by_id("confirm-delete").click()
        time.sleep(3)
        driver.find_element_by_xpath("//*[@id='modal-from-dom']/div[3]/a[2]").click()
        time.sleep(4)
        deleteLinks = driver.find_elements_by_link_text("TestTemplate_hospital")
        self.assertTrue(not deleteLinks)


class UniqueTemplateName(SimpleTestCase):

    def test_unique_template_name(self):
        driver = self.driver
        driver.get(self.base_url + "tfoms/settings_template/patients/")
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate")
        driver.find_element_by_id("Save").click()
        time.sleep(7)
        driver.find_element_by_link_text("Создать").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate")
        time.sleep(2)
        driver.find_element_by_id("Save").click()
        # Warning: assertTextPresent may require manual changes
        time.sleep(5)
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Наименования шаблонов должны быть уникальны![\s\S]*$")
        time.sleep(1)
        driver.find_element_by_link_text("Сведения об оказанной мед.помощи (XML)").click()
        time.sleep(2)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_usl")
        driver.find_element_by_id("Save").click()
        time.sleep(7)
        driver.find_element_by_link_text("Создать").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_usl")
        time.sleep(2)
        driver.find_element_by_id("Save").click()
        # Warning: assertTextPresent may require manual changes
        time.sleep(5)
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Наименования шаблонов должны быть уникальны![\s\S]*$")
        time.sleep(1)
        driver.find_element_by_link_text("Поликлиника (DBF)").click()
        time.sleep(2)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_policlinic")
        driver.find_element_by_id("Save").click()
        time.sleep(7)
        driver.find_element_by_link_text("Создать").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_policlinic")
        time.sleep(2)
        driver.find_element_by_id("Save").click()
        time.sleep(5)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Наименования шаблонов должны быть уникальны![\s\S]*$")
        time.sleep(1)
        driver.find_element_by_link_text("Стационар (DBF)").click()
        time.sleep(2)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_hospital")
        driver.find_element_by_id("Save").click()
        time.sleep(7)
        driver.find_element_by_link_text("Создать").click()
        time.sleep(1)
        driver.find_element_by_id("name").clear()
        driver.find_element_by_id("name").send_keys("TestTemplate_hospital")
        time.sleep(2)
        driver.find_element_by_id("Save").click()
        time.sleep(5)
        # Warning: assertTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text.encode('utf8'),
                                 r"^[\s\S]*Внимание! Наименования шаблонов должны быть уникальны![\s\S]*$")
        time.sleep(1)

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

        template = Template.query.filter_by(name="TestTemplate").first()
        template_usl = Template.query.filter_by(name="TestTemplate_usl").first()
        template_policlinic = Template.query.filter_by(name="TestTemplate_policlinic").first()
        template_hospital = Template.query.filter_by(name="TestTemplate_hospital").first()
        db.session.delete(template)
        db.session.delete(template_usl)
        db.session.delete(template_policlinic)
        db.session.delete(template_hospital)
        db.session.commit()


######## Opera
class ClickTabsOpera(ClickTabs):

    def setUp(self):
        self.driver = webdriver.Opera("path to selenium-server")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class EmptyTemplateNameOpera(EmptyTemplateName):

    def setUp(self):
        self.driver = webdriver.Opera("path to selenium-server")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class SaveDeleteNewTemplateOpera(SaveDeleteNewTemplate):

    def setUp(self):
        self.driver = webdriver.Opera("path to selenium-server")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class UniqueTemplateNameOpera(UniqueTemplateName):

    def setUp(self):
        self.driver = webdriver.Opera("path to selenium-server")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


####### Chrome
class ClickTabsChrome(ClickTabs):

    def setUp(self):
        self.driver = webdriver.Chrome("path to chromedriver")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class EmptyTemplateNameChrome(EmptyTemplateName):

    def setUp(self):
        self.driver = webdriver.Chrome("path to chromedriver")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class SaveDeleteNewTemplateChrome(SaveDeleteNewTemplate):
    def setUp(self):
        self.driver = webdriver.Chrome("path to chromedriver")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


class UniqueTemplateNameChrome(UniqueTemplateName):

    def setUp(self):
        self.driver = webdriver.Chrome("path to chromedriver")
        self.driver.implicitly_wait(20)
        self.base_url = "http://127.0.0.1:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True


test_cases = (UniqueTemplateNameOpera, )


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
#
# if __name__ == "__main__":
#     unittest.main()
