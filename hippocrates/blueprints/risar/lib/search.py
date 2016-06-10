# -*- coding: utf-8 -*-
from nemesis.lib.vesta import Vesta, VestaNotFoundException


def get_workgroupname_by_code(code):
    try:
        if code:
            record = Vesta.get_rb('rbRisarWork_Group', code)
            return record.get('name', '')
    except VestaNotFoundException as e:
        pass
    return ''
