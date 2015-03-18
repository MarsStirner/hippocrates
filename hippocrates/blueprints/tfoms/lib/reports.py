# -*- encoding: utf-8 -*-
from ..lib.service_client import TFOMSClient as Client
from ..app import _config


class Reports(object):

    def __init__(self):
        self.client = Client(_config('core_service_url'))

    def get_bills(self, infis_code):
        return self.client.get_bills(infis_code)

    def get_bill_cases(self, bill_id):
        return self.client.get_bill_cases(bill_id)

    def delete_bill(self, bill_id):
        return self.client.delete_bill(bill_id)

    def get_bill(self, bill_id):
        return self.client.get_bill(bill_id)

    def change_case_status(self, case_id, status, note=None):
        return self.client.change_cases_status(dict(id=case_id, status=status, note=note))
