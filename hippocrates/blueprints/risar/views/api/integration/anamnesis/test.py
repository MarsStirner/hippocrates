# coding: utf-8

from ..test import make_login, make_api_request
from test_data import (anamnesis_m_data, anamnesis_m_data2, anamnesis_f_data, prev_preg_data10, prev_preg_data11,
    prev_preg_data20, prev_preg_data21)


def create_mother_anamnesis(token, session_token, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/mother/' % card_id
    result = make_api_request('post', url, token, session_token, data)
    return result


def edit_mother_anamnesis(token, session_token, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/mother/' % card_id
    result = make_api_request('put', url, token, session_token, data)
    return result


def delete_mother_anamnesis(token, session_token, card_id):
    url = u'/risar/api/integration/0/card/%s/anamnesis/mother/' % card_id
    result = make_api_request('delete', url, token, session_token)
    return result


def create_father_anamnesis(token, session_token, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/father/' % card_id
    result = make_api_request('post', url, token, session_token, data)
    return result


def edit_father_anamnesis(token, session_token, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/father/' % card_id
    result = make_api_request('put', url, token, session_token, data)
    return result


def delete_father_anamnesis(token, session_token, card_id):
    url = u'/risar/api/integration/0/card/%s/anamnesis/father/' % card_id
    result = make_api_request('delete', url, token, session_token)
    return result


def create_prevpregnancy_anamnesis(token, session_token, card_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/prevpregnancy/' % card_id
    result = make_api_request('post', url, token, session_token, data)
    return result


def edit_prevpregnancy_anamnesis(token, session_token, card_id, prevpregnancy_id, data):
    url = u'/risar/api/integration/0/card/%s/anamnesis/prevpregnancy/%s' % (card_id, prevpregnancy_id)
    result = make_api_request('put', url, token, session_token, data)
    return result


def delete_prevpregnancy_anamnesis(token, session_token, card_id, prevpregnancy_id):
    url = u'/risar/api/integration/0/card/%s/anamnesis/prevpregnancy/%s' % (card_id, prevpregnancy_id)
    result = make_api_request('delete', url, token, session_token)
    return result


def test_register_edit_delete_mother_anamnesis(card_id):
    with make_login() as (token, session_token):
        result = create_mother_anamnesis(token, session_token, card_id, anamnesis_m_data)
        anamnesis = result['result']
        print u'new mother anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        try:
            result = create_mother_anamnesis(token, session_token, card_id, anamnesis_m_data)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_mother_anamnesis(token, session_token, card_id, anamnesis_m_data2)
        anamnesis = result['result']
        print u'edited mother anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = delete_mother_anamnesis(token, session_token, card_id)
        anamnesis = result['result']
        print u'deleted mother anamnesis'


def test_register_edit_delete_father_anamnesis(card_id):
    with make_login() as (token, session_token):
        result = create_father_anamnesis(token, session_token, card_id, anamnesis_f_data)
        anamnesis = result['result']
        print u'new father anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        try:
            result = create_father_anamnesis(token, session_token, card_id, anamnesis_f_data)
        except Exception, e:
            if '409' in e.message:
                print e.message
            else:
                raise e

        result = edit_father_anamnesis(token, session_token, card_id, anamnesis_f_data)
        anamnesis = result['result']
        print u'edited father anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = delete_father_anamnesis(token, session_token, card_id)
        anamnesis = result['result']
        print u'deleted father anamnesis'


def test_register_edit_delete_prevpregnancies_anamnesis(card_id):
    with make_login() as (token, session_token):
        result = create_prevpregnancy_anamnesis(token, session_token, card_id, prev_preg_data10)
        anamnesis = result['result']
        anamnesis_id_1 = anamnesis['prevpregnancy_id']
        print u'new prevpregnancy anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = edit_prevpregnancy_anamnesis(token, session_token, card_id, anamnesis_id_1, prev_preg_data11)
        anamnesis = result['result']
        anamnesis_id_1 = anamnesis['prevpregnancy_id']
        print u'edited prevpregnancy anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = create_prevpregnancy_anamnesis(token, session_token, card_id, prev_preg_data20)
        anamnesis = result['result']
        anamnesis_id_2 = anamnesis['prevpregnancy_id']
        print u'new prevpregnancy anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = edit_prevpregnancy_anamnesis(token, session_token, card_id, anamnesis_id_2, prev_preg_data21)
        anamnesis = result['result']
        anamnesis_id_2 = anamnesis['prevpregnancy_id']
        print u'edited prevpregnancy anamnesis data: {0}'.format(repr(anamnesis).decode("unicode-escape"))

        result = delete_prevpregnancy_anamnesis(token, session_token, card_id, anamnesis_id_1)
        anamnesis = result['result']
        print u'deleted prevpregnancy anamnesis id = {0}'.format(anamnesis_id_1)

        result = delete_prevpregnancy_anamnesis(token, session_token, card_id, anamnesis_id_2)
        anamnesis = result['result']
        print u'deleted prevpregnancy anamnesis id = {0}'.format(anamnesis_id_2)
