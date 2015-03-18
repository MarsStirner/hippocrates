# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
import unittest
import time, re


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


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


class HippoSimpleTest(SimpleTestCase):

    def test_simple_test(self):
        driver = self.driver
        driver.get(self.base_url + "/")
        driver.find_element_by_link_text(u"Расписание").click()
        driver.find_element_by_link_text(u"Поиск врача").click()
        driver.find_element_by_link_text(u"Поиск пациента").click()
        driver.find_element_by_link_text(u"График врача").click()
        driver.find_element_by_xpath("//select[@name='year']/option[text()='2013']").click()
        driver.find_element_by_xpath("//select[@name='year']/option[text()='2015']").click()
        driver.find_element_by_xpath("//select[@name='year']/option[text()='2014']").click()
        driver.find_element_by_xpath("//select[@name='month']/option[text()='Март']").click()
        driver.find_element_by_xpath("//select[@name='month']/option[text()='Сентябрь']").click()
        driver.find_element_by_xpath("//select[@name='month']/option[text()='Февраль']").click()


test_cases = (HippoSimpleTest, )


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
# if __name__ == '__main__':
#     unittest.main()
