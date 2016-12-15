#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from nemesis.lib.enum import Enum


# copy from sirius
class RisarEntityCode(Enum):
    CLIENT = 'client'
    CARD = 'card'
    CHECKUP_OBS_FIRST_TICKET = 'checkup_obs_first_ticket'
    CHECKUP_OBS_FIRST = 'checkup_obs_first'
    CHECKUP_OBS_SECOND_TICKET = 'checkup_obs_second_ticket'
    CHECKUP_OBS_SECOND = 'checkup_obs_second'
    MEASURE = 'measure'
    MEASURE_RESEARCH = 'measure_research'
    MEASURE_HOSPITALIZATION = 'measure_hospitalization'
    MEASURE_SPECIALISTS_CHECKUP = 'measure_specialists_checkup'
    EPICRISIS = 'epicrisis'
    ORGANIZATION = 'organization'
    DOCTOR = 'doctor'
    SCHEDULE = 'schedule'
    SCHEDULE_TICKET = 'schedule_ticket'
    CHILDBIRTH = 'childbirth'
    CHECKUP_PC_TICKET = 'checkup_pc_ticket'
    RISAR_REFBOOK_NAME = 'risar_refbook_name'
    RISAR_REFBOOK = 'risar_refbook'
    VESTA_REFBOOK = 'vesta_refbook'
    EXCHANGE_CARD = 'exchange_card'
    APPOINTMENT = 'appointment'
