# coding: utf-8

from ..test import make_login, make_api_request
from test_data import anamnesis_gyn_data


def create_gyn_anamnesis(session, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/gynecology/' % card_id
    result = make_api_request('post', url, session, data)
    return result


def edit_gyn_anamnesis(session, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/gynecology/' % card_id
    result = make_api_request('put', url, session, data)
    return result


def delete_gyn_anamnesis(session, card_id):
    url = u'/risar/api/integration/0/card/%s/anamnesis/gynecology/' % card_id
    result = make_api_request('delete', url, session)
    return result


def test_register_edit_delete_gyn_anamnesis(card_id):
    with make_login() as session:
        result = create_gyn_anamnesis(session, card_id, anamnesis_gyn_data)
        anamnesis = result['result']
        print u'new anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        try:
            result = create_gyn_anamnesis(session, card_id, anamnesis_gyn_data)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_gyn_anamnesis(session, card_id, anamnesis_gyn_data)
        anamnesis = result['result']
        print u'edited anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = delete_gyn_anamnesis(session, card_id)
        anamnesis = result['result']
        print u'deleted anamnesis'
