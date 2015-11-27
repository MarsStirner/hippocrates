# -*- coding: utf-8 -*-

from blueprints.accounting.lib.utils import get_contragent_type
from nemesis.models.enums import Gender, ContragentType
from nemesis.lib.utils import format_date


class ContractRepr(object):

    def __init__(self):
        self.ca_repr = ContragentRepr()
        self.contingent_repr = ContingentRepr()
        self.pricelist_repr = PriceListRepr()

    def represent_contract_full(self, contract):
        if not contract:
            return None
        data = self.represent_contract(contract)
        data.update({
            'recipient': self.ca_repr.represent_contragent(contract.recipient),
            'payer': self.ca_repr.represent_contragent(contract.payer),
            'contingent_list': [
                self.contingent_repr.represent_contingent(cont)
                for cont in contract.contingent_list if cont.deleted == 0  # TODO: think about selection
            ],
            'pricelist_list': [
                self.pricelist_repr.represent_pricelist_short(pl)
                for pl in contract.pricelist_list if pl.deleted == 0  # TODO: think about selection
            ],
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            }
        })
        return data

    def represent_contract(self, contract):
        return {
            'id': contract.id,
            'number': contract.number,
            'date': contract.date,
            'beg_date': contract.begDate,
            'end_date': contract.endDate,
            'finance': contract.finance,
            'contract_type': contract.contract_type,
            'resolution': contract.resolution,
            'deleted': contract.deleted,
            'draft': contract.draft,
        }

    def make_full_description(self, contract):
        return u'''\
№{0} от {1}. {2}. с {3} по {4}</span>
'''.format(contract.number, format_date(contract.date), contract.resolution or '', format_date(contract.begDate),
           format_date(contract.endDate))

    def make_short_description(self, contract):
        return u'№{0} от {1}. {2}'.format(contract.number, format_date(contract.date), contract.resolution or '')

    def represent_paginated_contracts(self, paginated_data):
        return {
            'count': paginated_data.total,
            'total_pages': paginated_data.pages,
            'contract_list': [
                self.represent_contract_full(contract) for contract in paginated_data.items
            ]
        }

    def represent_listed_contracts(self, contract_list):
        return [
            self.represent_contract_full(contract) for contract in contract_list
        ]


class ContragentRepr(object):

    def represent_contragent(self, contragent):
        if not contragent:
            return None
        ca_type = get_contragent_type(contragent)
        return {
            'id': contragent.id,
            'client': self.represent_ca_client(contragent.client),
            'org': self.represent_ca_org(contragent.org),
            'ca_type': ca_type,
            'ca_type_code': unicode(ca_type),
            'short_descr': self.make_ca_short_descr(contragent),
            'full_descr': self.make_ca_full_descr(contragent)
        }

    def make_ca_short_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.shortName
        elif ca_type.value == ContragentType.individual[0]:
            return contragent.client.nameText

    def make_ca_full_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.fullName
        elif ca_type.value == ContragentType.individual[0]:
            return u'{0}, {1}, {2}'.format(
                contragent.client.nameText,
                Gender.getName(contragent.client.sex),
                format_date(contragent.client.birthDate)
            )

    def represent_ca_client(self, client):
        if client is None:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }

    def represent_ca_org(self, org):
        if org is None:
            return None
        return {
            'id': org.id,
            'short_name': org.shortName,
            'full_name': org.fullName
        }

    def represent_listed_contragents(self, ca_list):
        return [
            self.represent_contragent(contragent) for contragent in ca_list
        ]


class ContingentRepr(object):

    def represent_contingent(self, contingent):
        return {
            'id': contingent.id,
            'contract_id': contingent.contract_id,
            'client': self.represent_client(contingent.client),
            'deleted': contingent.deleted
        }

    def represent_client(self, client):
        if not client:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }


class PriceListRepr(object):

    def represent_pricelist(self, pl):
        return {
            'id': pl.id,
            'code': pl.code,
            'name': pl.name,
            'deleted': pl.deleted,
            'finance': pl.finance,
            'beg_date': pl.begDate,
            'end_date': pl.endDate
        }

    def represent_pricelist_short(self, pl):
        data = self.represent_pricelist(pl)
        data['description'] = {
            'short': self.make_short_description(pl),
        }
        return data

    def make_short_description(self, pl):
        return u'{0} ({1}), с {1} по {2}'.format(pl.name, pl.finance.name,
                                                 format_date(pl.begDate), format_date(pl.endDate))

    def represent_listed_pricelists(self, pl_list):
        return [
            self.represent_pricelist_short(pl) for pl in pl_list
        ]


class ServiceRepr(object):

    def represent_mis_action_service_search_result(self, service_data):
        return {
            'service': {
                'price_list_item_id': service_data['price_list_item_id'],
                'service_id': service_data['service_id'],
                'service_code': service_data['service_code'],
                'service_name': service_data['service_name'],
                'price': service_data['price'],
                'amount': service_data['amount'],
            },
            'action': {
                'action_type_id': service_data['action_type_id'],
                'at_code': service_data['at_code'],
                'at_name': service_data['at_name'],
            }
        }

    def represent_search_result_mis_action_services(self, service_list):
        return [
            self.represent_mis_action_service_search_result(service) for service in service_list
        ]

    def represent_service(self, service):
        return {
            'id': service.id,
            'price_list_item_id': service.priceListItem_id,
            'amount': service.amount,
            'price': service.price_list_item.price,
            'service_id': service.price_list_item.service_id,
            'deleted': service.deleted
        }

    def represent_service_action(self, action):
        return {
            'id': action.id,
            'action_type_id': action.actionType_id,
        }

    def represent_grouped_event_services(self, grouped_data):
        grouped_data['sg_list'] = [
            {
                'service': self.represent_service(service),
                'action': self.represent_service_action(service.action)
            }
            for sg in grouped_data['sg_list'] for service in sg
        ]
        return grouped_data