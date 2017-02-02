#! coding:utf-8
"""


@author: BARS Group
@date: 22.11.2016

"""
from nemesis.lib.enum import Enum


class RisarEvents(Enum):
    CREATE_CARD = 'create_card'
    MAKE_APPOINTMENT = 'make_appointment'
    SAVE_CHECKUP = 'save_checkup'
    CLOSE_CHECKUP = 'close_checkup'
    ENTER_MIS_EMPLOYEE = 'enter_mis_employee'
    CLOSE_CARD = 'close_card'
    CREATE_REFERRAL = 'create_referral'
    SAVE_CHECKUP_PUERPERA = 'save_checkup_puerpera'
