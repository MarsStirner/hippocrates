# coding: utf-8

from ..test import make_login, make_api_request
from test_data import org_data


def create_org(session, data):
    url = u'/risar/api/integration/0/organization/'
    result = make_api_request('post', url, session, data)
    return result


def update_org(session, org_code, data):
    url = u'/risar/api/integration/0/organization/%s' % org_code
    result = make_api_request('put', url, session, data)
    return result


def test_create_update_organization():
    with make_login() as session:
        result = create_org(session, org_data['org_data'])
        new_org = result['result']
        print u'new organization: {0}'.format(repr(new_org).decode("unicode-escape"))

        try:
            result = create_org(session, org_data['org_data'])
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        org_data['org_data']['full_name'] = u'Измененное название лпу'
        result = update_org(session, org_data['org_code'], org_data['org_data'])
        edited_org = result['result']
        print u'edited organization: {0}'.format(repr(edited_org).decode("unicode-escape"))
