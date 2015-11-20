# -*- coding: utf-8 -*-

from blueprints.accounting.lib.utils import get_contragent_type
from nemesis.models.enums import Gender, ContragentType
from nemesis.lib.utils import format_date


class ContractRepr(object):

    def __init__(self):
        self.ca_repr = ContragentRepr()
        self.contingent_repr = ContingentRepr()

    def represent_contract_full(self, contract):
        data = self.represent_contract(contract)
        data.update({
            'recipient': self.ca_repr.represent_contragent(contract.recipient),
            'payer': self.ca_repr.represent_contragent(contract.payer),
            'contingent': [
                self.contingent_repr.represent_contingent(cont)
                for cont in contract.contingent
            ],
            'pricelist_list': []
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
            'client': self.represent_client(contingent.client)
        }

    def represent_client(self, client):
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }