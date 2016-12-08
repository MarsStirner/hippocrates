# coding: utf-8

from ..test import make_login, make_api_request
from test_data import sct_data


def create_sct(session, data):
    url = u'/risar/api/integration/0/schedule_tickets/'
    result = make_api_request('post', url, session, data)
    return result


def update_sct(session, sct_id, data):
    url = u'/risar/api/integration/0/schedule_tickets/%s' % sct_id
    result = make_api_request('put', url, session, data)
    return result


def delete_sct(session, sct_id):
    url = u'/risar/api/integration/0/schedule_tickets/%s' % sct_id
    result = make_api_request('delete', url, session)
    return result


def test_create_update_delete_schedule_tickets():
    with make_login() as session:
        sct = create_sct(session, sct_data)
        print u'new sct: {0}'.format(repr(sct).decode("unicode-escape"))

        sct_id = sct['result']['schedule_ticket_id']

        sct = update_sct(session, sct_id, sct_data)
        print u'edited sct: {0}'.format(repr(sct).decode("unicode-escape"))

        sct_id = sct['result']['schedule_ticket_id']

        sct = delete_sct(session, sct_id)
        print u'deleted sct: {0}'.format(repr(sct).decode("unicode-escape"))
