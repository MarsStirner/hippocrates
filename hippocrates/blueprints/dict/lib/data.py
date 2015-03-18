# -*- coding: utf-8 -*-
import os
import exceptions
import calendar
from datetime import date
import dbf

from ..app import module, _config
from service_client import TARIFFClient as Client
from .thrift_service.TARIFF.ttypes import Tariff as Tariff_Type

DOWNLOADS_DIR = os.path.join(module.static_folder, 'downloads')
UPLOADS_DIR = os.path.join(module.static_folder, 'uploads')


class Tariff(object):

    def __init__(self):
        self.client = Client(_config('core_service_url'))
        self.dbf_keys = ('c_tar', 'summ_tar', 'date_b', 'date_e')

    def __convert_date(self, _date):
        return calendar.timegm(_date.timetuple()) * 1000

    def __check_record(self, c_tar):
        if c_tar[0:6] == _config('old_lpu_infis_code'):
            return True
        return False

    def parse(self, file_path):
        result = list()
        if os.path.isfile(file_path):
            table = dbf.Table(file_path)
            if table:
                table.open()
                for i, record in enumerate(table):
                    value = Tariff_Type(number=i + 1)
                    if self.__check_record(record['c_tar']):
                        for key in self.dbf_keys:
                            if isinstance(record[key], date):
                                setattr(value, key, self.__convert_date(record[key]))
                            else:
                                setattr(value, key, record[key])
                        result.append(value)
                table.close()
        return result

    def send(self, data):
        return self.client.send_tariffs(data, _config('contract_id'))