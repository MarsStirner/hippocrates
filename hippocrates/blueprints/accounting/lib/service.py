# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import exists
from sqlalchemy.orm import join

from nemesis.models.accounting import Service, PriceListItem, Invoice, InvoiceItem
from nemesis.models.client import Client
from nemesis.models.actions import Action
from nemesis.lib.utils import safe_int, safe_unicode, safe_double, safe_decimal
from nemesis.lib.apiutils import ApiException

from blueprints.accounting.lib.contract import BaseModelController, BaseSelecter, BaseSphinxSearchSelecter, \
    ContractController
from nemesis.lib.sphinx_search import SearchEventService
from nemesis.lib.data import int_get_atl_dict_all, create_action, update_action, format_action_data
from nemesis.lib.agesex import recordAcceptableEx


class ServiceController(BaseModelController):
    class DataKind(object):
        abstract = 0
        mis_action = 1

    def __init__(self):
        super(ServiceController, self).__init__()
        self.contract_ctrl = ContractController()

    def get_selecter(self):
        return ServiceSelecter()

    def get_new_service(self, params=None):
        if params is None:
            params = {}
        service = Service()
        price_list_item_id = safe_int(params.get('price_list_item_id'))
        if price_list_item_id:
            service.priceListItem_id = price_list_item_id
        service.amount = 1
        service.deleted = 0
        return service

    def get_service(self, service_id):
        contract = self.session.query(Service).get(service_id)
        return contract

    def update_service(self, service, json_data):
        json_data = self._format_service_data(json_data)
        for attr in ('amount', 'priceListItem_id', 'price_list_item'):
            if attr in json_data:
                setattr(service, attr, json_data.get(attr))
        # self.update_contract_ca_payer(contract, json_data['payer'])
        return service

    def _format_service_data(self, data):
        data['amount'] = safe_double(data['service']['amount'])
        data['priceListItem_id'] = safe_int(data['service']['price_list_item_id'])
        data['price_list_item'] = self.session.query(PriceListItem).filter(
            PriceListItem.id == data['service']['price_list_item_id']
        ).first()
        return data

    def search_mis_action_services(self, args):
        contract_id = safe_int(args.get('contract_id'))
        if not contract_id:
            raise ApiException(422, u'`contract_id` required')
        pricelist_id_list = self.contract_ctrl.get_contract_pricelist_id_list(contract_id)
        service_sphinx = ServiceSphinxSearchSelecter()
        service_sphinx.apply_filter(pricelist_id_list=pricelist_id_list, **args)
        search_result = service_sphinx.get_all()
        data = search_result['result']['items']
        for item in data:
            item['amount'] = 1
            item['sum'] = item['price'] * item['amount']
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

    def get_grouped_services_by_event(self, event_id):
        args = {
            'event_id': event_id
        }
        service_list = self.get_listed_data(args)
        grouped = []
        sg_map = {}
        for service in service_list:
            key = u'{0}/{1}'.format(service.price_list_item.service_id, service.action.actionType_id)
            if key not in sg_map:
                sg_map[key] = len(grouped)
                grouped.append({
                    'sg_data': {
                        'service_code': service.price_list_item.serviceCodeOW,
                        'service_name': service.price_list_item.serviceNameOW,
                        'at_name': service.action.actionType.name,
                        'price': service.price_list_item.price,
                        'total_amount': 0,
                        'total_sum': 0
                    },
                    'sg_list': []
                })
            idx = sg_map[key]
            grouped[idx]['sg_list'].append({
                'service': service,
                'action': service.action
            })
            grouped[idx]['sg_data']['total_amount'] += service.amount
            grouped[idx]['sg_data']['total_sum'] += (service.price_list_item.price * safe_decimal(service.amount))
        return {
            'grouped': grouped,
            'sg_map': sg_map
        }

    def get_new_service_action(self, service_data, event_id):
        action_type_id = safe_int(service_data['action']['action_type_id'])
        action = create_action(action_type_id, event_id)
        return action

    def get_service_action(self, action_id):
        contract = self.session.query(Action).get(action_id)
        return contract

    def update_service_action(self, action, json_data):
        # json_data = format_action_data(json_data)
        # action = update_action(action, **json_data)
        # TODO:
        return action

    def save_service_list(self, grouped_service_list, event_id):
        result = []
        for service_group in grouped_service_list:
            for service_data in service_group['sg_list']:
                service_id = service_data['service'].get('id')
                if service_id:
                    service = self.get_service(service_id)
                    action = self.get_service_action(service.action_id)
                else:
                    service = self.get_new_service(service_data)
                    action = self.get_new_service_action(service_data, event_id)
                    service.action = action
                service = self.update_service(service, service_data)
                action = self.update_service_action(action, service_data)
                result.append(service)
                result.append(action)
        return result

    def check_service_in_invoice(self, service):
        if not service.id:
            return False
        return self.session.query(
            exists().select_from(
                join(Service, InvoiceItem, InvoiceItem.service).join(Invoice)
            ).where(Service.id == service.id).where(Invoice.deleted == 0).where(Service.deleted == 0)
        ).scalar()


class ServiceSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Service)
        super(ServiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        if 'event_id' in flt_args:
            event_id = safe_int(flt_args['event_id'])
            self.query = self.query.join(Action).filter(
                Action.event_id == event_id,
                Action.deleted == 0,
                Service.deleted == 0
            )
        return self


class ServiceSphinxSearchSelecter(BaseSphinxSearchSelecter):

    def __init__(self):
        search = SearchEventService.get_search()
        super(ServiceSphinxSearchSelecter, self).__init__(search)

    def apply_filter(self, **flt_args):
        if 'query' in flt_args:
            self.search = self.search.match(safe_unicode(flt_args['query']))
        if 'pricelist_id_list' in flt_args:
            id_list = flt_args['pricelist_id_list']
            if not id_list:
                self.search = self.search.filter(pricelist_id__in=[-1])
            else:
                self.search = self.search.filter(pricelist_id__in=id_list)
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