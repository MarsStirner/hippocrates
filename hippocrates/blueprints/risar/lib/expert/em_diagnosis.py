#! coding:utf-8
"""


@author: BARS Group
@date: 22.04.2016

"""


def get_measure_result_mkbs(action, codes):
    res = []
    for code in codes:
        if action.has_property(code):
            val = action.get_prop_value(code)
            if val:
                res.append(val.DiagID)
    return res
