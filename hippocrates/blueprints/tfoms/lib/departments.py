# -*- encoding: utf-8 -*-
from ..lib.service_client import TFOMSClient as Client
from ..app import _config


class Departments(object):

    def __init__(self, infis_code):
        self.client = None
        self.infis_code = infis_code

    def __get_client(self):
        if self.client is None:
            self.client = Client(_config('core_service_url'))

    def __get_from_core(self):
        self.__get_client()
        return self.client.get_departments(self.infis_code)

    def get_departments(self):
        data = self.__get_from_core()
        return data
