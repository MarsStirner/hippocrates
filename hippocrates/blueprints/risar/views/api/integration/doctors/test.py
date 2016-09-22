# coding: utf-8

from ..test import make_login, make_api_request
from test_data import doctor_data, doctor_data2


def create_doctor(session, data):
    url = u'/risar/api/integration/0/doctor/'
    result = make_api_request('post', url, session, data)
    return result


def update_doctor(session, lpu_code, doctor_code, data):
    url = u'/risar/api/integration/0/doctor/%s/%s' % (lpu_code, doctor_code)
    result = make_api_request('put', url, session, data)
    return result


def test_create_update_doctor():
    with make_login() as session:
        result = create_doctor(session, doctor_data['doctor_data'])
        new_doctor = result['result']
        print u'new doctor: {0}'.format(repr(new_doctor).decode("unicode-escape"))

        try:
            result = create_doctor(session, doctor_data['doctor_data'])
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = update_doctor(session, doctor_data2['lpu_code'], doctor_data2['doctor_code'],
                               doctor_data2['doctor_data'])
        edited_doctor = result['result']
        print u'edited doctor: {0}'.format(repr(edited_doctor).decode("unicode-escape"))
