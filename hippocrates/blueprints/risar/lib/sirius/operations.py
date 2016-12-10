#! coding:utf-8
"""


@author: BARS Group
@date: 10.12.2016

"""
from nemesis.lib.enum import Enum


# copy from sirius
class OperationCode(Enum):
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'
    READ_ONE = 'read_one'
    READ_MANY = 'read_many'
