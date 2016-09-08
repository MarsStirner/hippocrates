# coding: utf-8

from ..test import make_login, make_api_request
from test_data import create_scheds_data


def create_scheds(session, lpu_code, doctor_code, data):
    url = u'/risar/api/integration/0/schedule/%s/%s' % (lpu_code, doctor_code)
    result = make_api_request('post', url, session, data)
    return result


def test_create_schedules():
    with make_login() as session:
        result = create_scheds(
            session,
            create_scheds_data['lpu_code'],
            create_scheds_data['doctor_code'],
            create_scheds_data['scheds']
        )
        scheds = result['result']
        print u'new sheds: {0}'.format(repr(scheds).decode("unicode-escape"))
