# -*- coding: utf-8 -*-

import datetime

from nemesis.models.client import Client
from nemesis.lib.utils import safe_int, safe_unicode

from blueprints.accounting.lib.contract import BaseModelController, BaseSelecter, BaseSphinxSearchSelecter
from nemesis.lib.sphinx_search import SearchEventService
from nemesis.lib.data import int_get_atl_dict_all
from nemesis.lib.agesex import recordAcceptableEx


class ServiceController(BaseModelController):
    class DataKind(object):
        abstract = 0
        mis_action = 1

    def __init__(self):
        super(ServiceController, self).__init__()

    def get_selecter(self):
        return ServiceSelecter()

    # def get_pricelist(self, pricelist_id):
    #     contract = self.session.query(PriceList).get(pricelist_id)
    #     return contract

    def search_mis_action_services(self, args):
        service_sphinx = ServiceSphinxSearchSelecter()
        service_sphinx.apply_filter(**args)
        search_result = service_sphinx.get_all()
        data = search_result['result']['items']
        data = self._filter_mis_action_search_results(args, data)
        return data

    def _filter_mis_action_search_results(self, args, data):
        client_id = safe_int(args.get('client_id'))
        if not client_id:
            return data
        client = self.session.query(Client).get(client_id)
        client_age = client.age_tuple(datetime.date.today())
        ats_apts = int_get_atl_dict_all()

        matched = []
        for item in data:
            at_id = item['action_type_id']
            at_data = ats_apts.get(at_id)
            if at_data and recordAcceptableEx(client.sexCode, client_age, at_data[6], at_data[5]):
                matched.append(item)
        return matched


class ServiceSelecter(BaseSelecter):
    pass

    # def __init__(self):
    #     query = self.session.query(PriceList).order_by(PriceList.begDate)
    #     super(ServiceSelecter, self).__init__(query)
    #
    # def apply_filter(self, **flt_args):
    #     if 'finance_id' in flt_args:
    #         finance_id = safe_int(flt_args['finance_id'])
    #         self.query = self.query.filter(PriceList.finance_id == finance_id)
    #     return self


class ServiceSphinxSearchSelecter(BaseSphinxSearchSelecter):

    def __init__(self):
        search = SearchEventService.get_search()
        super(ServiceSphinxSearchSelecter, self).__init__(search)

    def apply_filter(self, **flt_args):
        if 'query' in flt_args:
            self.search = self.search.match(safe_unicode(flt_args['query']))
        if 'contract_id' in flt_args:
            self.search = self.search.filter(contract_id__eq=safe_int(flt_args['contract_id']))
        return self

    def apply_limit(self, **limit_args):
        self.search = self.search.limit(0, 100)
        return self

    # def search(query, eventType_id=None, contract_id=None, speciality_id=None):
    #     search = search.match(query)
    #     if eventType_id:
    #         search = search.filter(eventType_id__eq=int(eventType_id))
    #     if contract_id:
    #         search = search.filter(contract_id__eq=int(contract_id))
    #     if speciality_id:
    #         search = search.filter(speciality_id__in=[0, int(speciality_id)])
    #     search = search.limit(0, 100)
    #     result = search.ask()
    #     return result