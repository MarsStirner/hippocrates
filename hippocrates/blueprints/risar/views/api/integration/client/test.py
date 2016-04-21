# coding: utf-8

from ..test import make_login, make_api_request
from test_data import test_client_data_1, test_client_data_2


def create_client(session, data):
    url = u'/risar/api/integration/0/client/'
    result = make_api_request('post', url, session, data)
    return result


def edit_client(session, client_id, data):
    url = u'/risar/api/integration/0/client/%s' % client_id
    result = make_api_request('put', url, session, data)
    return result


def test_register_edit_client():
    with make_login() as session:
        result = create_client(session, test_client_data_1)
        client = result['result']
        client_id = client['client_id']
        print u'new client data: {0}'.format(repr(client).decode("unicode-escape"))

        try:
            result = create_client(session, test_client_data_1)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_client(session, client_id, test_client_data_2)
        client = result['result']
        print u'edited client data: {0}'.format(repr(client).decode("unicode-escape"))
