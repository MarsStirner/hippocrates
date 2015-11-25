# -*- coding: utf-8 -*-

from nemesis.models.enums import ContragentType


def get_contragent_type(contragent):
    return ContragentType(
        ContragentType.individual[0] if contragent.client is not None
        else (
            ContragentType.legal[0] if contragent.org is not None
            else ContragentType.undefined[0]
        )
    )


def check_contract_type_with_insurance_policy(contract):
    pass