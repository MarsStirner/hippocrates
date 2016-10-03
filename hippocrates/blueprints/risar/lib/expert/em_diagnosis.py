#! coding:utf-8
"""


@author: BARS Group
@date: 22.04.2016

"""


def get_measure_result_mkbs(action, codes):
    res = []
    for code in codes:
        if code in action.propsByCode and action.propsByCode[code].value:
            res.append(action.propsByCode[code].value.DiagID)
    return res
