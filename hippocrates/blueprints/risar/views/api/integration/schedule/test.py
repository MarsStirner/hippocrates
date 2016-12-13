# coding: utf-8

from ..test import make_login, make_api_request
from test_data import create_scheds_data, schedule_full_data


def create_scheds(session, lpu_code, doctor_code, data):
    url = u'/risar/api/integration/0/schedule/%s/%s' % (lpu_code, doctor_code)
    result = make_api_request('post', url, session, data)
    return result


def create_schedule_full(session, data):
    url = u'/risar/api/integration/0/schedule/full/'
    result = make_api_request('post', url, session, data)
    return result


def update_schedule_full(session, schedule_id, data):
    url = u'/risar/api/integration/0/schedule/full/%s' % schedule_id
    result = make_api_request('put', url, session, data)
    return result


def delete_schedule_full(session, schedule_id):
    url = u'/risar/api/integration/0/schedule/full/%s' % schedule_id
    result = make_api_request('delete', url, session)
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


def test_create_update_delete_schedule_full():
    with make_login() as session:
        result = create_schedule_full(session, schedule_full_data)
        sched = result['result']
        sched_id = sched['schedule_id']
        print u'new shed: {0}'.format(repr(sched).decode("unicode-escape"))

        result = update_schedule_full(session, sched_id, schedule_full_data)
        sched = result['result']
        sched_id = sched['schedule_id']
        print u'updated shed: {0}'.format(repr(sched).decode("unicode-escape"))

        result = delete_schedule_full(session, sched_id)
        print u'deleted shed: {0}'.format(sched_id)
