# -*- coding: utf-8 -*-
from application.models.kladr_models import Kladr

from flask import abort, request
from flask.helpers import make_response

from application.systemwide import db
from application.lib.utils import jsonify, string_to_datetime, safe_date
from blueprints.patients.app import module
from application.lib.sphinx_search import SearchPatient
from application.lib.jsonify import ClientVisualizer
from blueprints.patients.lib.utils import *


__author__ = 'mmalkov'


@module.errorhandler(ClientSaveException)
def handle_client_error(err):
    return make_response(jsonify({'name': err.message,
                                  'data': err.data},
                                 422, 'save client data error')[0],
                         422)


@module.route('/api/search_clients.json')
def api_search_clients():
    try:
        query_string = request.args['q']
    except KeyError or ValueError:
        return abort(404)

    base_query = Client.query

    if query_string:
        result = SearchPatient.search(query_string)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            base_query = base_query.filter(Client.id.in_(id_list))
        else:
            return jsonify([])
    clients = base_query.order_by(Client.lastName, Client.firstName, Client.patrName).limit(100).all()
    context = ClientVisualizer()
    return jsonify(map(context.make_client_info, clients))


@module.route('/api/patient.json')
def api_patient_get():
    try:
        client_id = request.args['client_id']
        if client_id != 'new':
            client_id = int(client_id)
    except KeyError or ValueError:
        return abort(404)
    context = ClientVisualizer()
    if client_id and client_id != 'new':
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
        return jsonify({
            'client_data': context.make_client_info(client),
            'appointments': context.make_appointments(client),
            'events': context.make_events(client)
        })
    else:
        client = Client()
        db.session.add(client)
        return jsonify({
            'client_data': context.make_client_info(client)
        })


def parse_id(request_data, identifier, allow_empty=False):
    """
    :param request_data:
    :param identifier:
    :param allow_empty:
    :return: None - empty identifier (new entity), False - parse error, int - correct identifier
    """
    _id = request_data.get(identifier)
    if _id is None and allow_empty or _id == 'new':
        return None
    elif _id is None and not allow_empty:
        return False
    else:
        try:
            _id = int(_id)
        except ValueError:
            return False
    return _id


@module.route('/api/save_patient_info.json', methods=['POST'])
def api_patient_save():
    client_data = request.json
    client_id = parse_id(client_data, 'client_id', True)
    if client_id is False:
        return abort(404)

    try:
        if client_id:
            client = Client.query.get(client_id)
            client_info = client_data.get('info')
            if client_info:
                client = set_client_main_info(client, client_info)
                db.session.add(client)

            id_doc_info = client_data.get('id_docs')
            if id_doc_info:
                for id_doc in id_doc_info:
                    doc = add_or_update_doc(client, id_doc)
                    db.session.add(doc)

            cpol_info = client_data.get('compulsory_policies')
            if cpol_info:
                for cpol in cpol_info:
                    pol = add_or_update_policy(client, cpol)
                    db.session.add(pol)

            vpol_info = client_data.get('voluntary_policies')
            if vpol_info:
                for vpol in vpol_info:
                    pol = add_or_update_policy(client, vpol)
                    db.session.add(pol)

            blood_type_info = client_data.get('blood_types')
            if blood_type_info:
                for bt in blood_type_info:
                    bt = add_or_update_blood_type(client, bt)
                    db.session.add(bt)
        else:
            client = Client()
            client_info = client_data.get('info')
            if not client_info:
                raise ClientSaveException(u'Client main info is empty')
            client = set_client_main_info(client, client_info)
            db.session.add(client)

            id_doc_info = client_data.get('id_docs')
            if id_doc_info:
                for id_doc in id_doc_info:
                    doc = add_or_update_doc(client, id_doc)
                    db.session.add(doc)

            cpol_info = client_data.get('compulsory_policies')
            if cpol_info:
                for cpol in cpol_info:
                    pol = add_or_update_policy(client, cpol)
                    db.session.add(pol)

            vpol_info = client_data.get('voluntary_policies')
            if vpol_info:
                for vpol in vpol_info:
                    pol = add_or_update_policy(client, vpol)
                    db.session.add(pol)

            blood_type_info = client_data.get('blood_types')
            if blood_type_info:
                for bt in blood_type_info:
                    bt = add_or_update_blood_type(client, bt)
                    db.session.add(bt)




    # try:
    #     reg_address = client_info['regAddress']
    #     actual_reg_address = None
    #     if reg_address is not None and (reg_address.get('address') or reg_address.get('free_input')):
    #         reg_address['type'] = 0
    #         if not client.reg_address:
    #             actual_reg_address = address = get_new_address(reg_address)
    #             client.addresses.append(address)
    #         else:
    #             addresses = get_modified_address(client, reg_address)
    #             db.session.add(addresses[0])
    #             if addresses[1]:
    #                 actual_reg_address = addresses[1]
    #                 client.addresses.append(actual_reg_address)
    #
    #     live_address = client_info['liveAddress']
    #
    #     if live_address is not None:
    #         # TODO: check AND FIX!
    #         if live_address.get('same_as_reg', False) and actual_reg_address:
    #             address = get_reg_address_copy(client, actual_reg_address)
    #             client.addresses.append(address)
    #         elif live_address.get('address') or live_address.get('free_input'):
    #             live_address['type'] = 1
    #             if not client.loc_address:
    #                 address = get_new_address(live_address)
    #                 client.addresses.append(address)
    #             else:
    #                 addresses = get_modified_address(client, live_address)
    #                 db.session.add(addresses[0])
    #                 if addresses[1]:
    #                     client.addresses.append(addresses[1])
    #
    #     for ss_info in client_info['socStatuses']:
    #         if not 'id' in ss_info:
    #             ss = get_new_soc_status(ss_info)
    #             client.socStatuses.append(ss)
    #         else:
    #             ss = get_modified_soc_status(client, ss_info)
    #             db.session.add(ss)
    #
    #     for allergy_info in client_info['allergies']:
    #         if not 'id' in allergy_info:
    #             allergy = get_new_allergy(allergy_info)
    #             client.allergies.append(allergy)
    #         else:
    #             allergy = get_modified_allergy(client, allergy_info)
    #             db.session.add(allergy)
    #
    #     for intolerance_info in client_info['intolerances']:
    #         if not 'id' in intolerance_info:
    #             intolerance = get_new_intolerance(intolerance_info)
    #             client.intolerances.append(intolerance)
    #         else:
    #             intolerance = get_modified_intolerance(client, intolerance_info)
    #             db.session.add(intolerance)
    #
    #     for id_info in client_info['identifications']:
    #         if not 'id' in id_info:
    #             id_ext = get_new_identification(id_info)
    #             client.identifications.append(id_ext)
    #         else:
    #             id_ext = get_modified_identification(client, id_info)
    #             db.session.add(id_ext)
    #
    #     for relation_info in client_info['direct_relations']:
    #         if not 'id' in relation_info:
    #             rel = get_new_direct_relation(relation_info)
    #             client.direct_relations.append(rel)
    #         else:
    #             rel = get_modified_direct_relation(client, relation_info)
    #             db.session.add(rel)
    #
    #     for relation_info in client_info['reversed_relations']:
    #         if not 'id' in relation_info:
    #             rel = get_new_reversed_relation(relation_info)
    #             client.reversed_relations.append(rel)
    #         else:
    #             rel = get_modified_reversed_relation(client, relation_info)
    #             db.session.add(rel)
    #
    #     for contact_info in client_info['contacts']:
    #         if not 'id' in contact_info:
    #             contact = get_new_contact(contact_info)
    #             client.contacts.append(contact)
    #         else:
    #             contact = get_modified_contact(client, contact_info)
    #             db.session.add(contact)
    #
    #     for doc_info in client_info['documentHistory']:
    #         if doc_info['deleted'] == 1:
    #             doc = get_deleted_document(client, doc_info)
    #             db.session.add(doc)

        db.session.commit()
    except Exception, e:
        # TODO: LOG!!
        db.session.rollback()
        raise
        return make_response(jsonify({'name': u'Ошибка сохранения данных пациента',
                                      'data': {
                                          'err_msg': 'INTERNAL SERVER ERROR'
                                       }
                                      },
                                     500, 'save client data error')[0],
                             500)

    return jsonify(int(client))


@module.route('/api/kladr_info.json', methods=['GET'])
def api_kladr_city_get():
    val = request.args['city']
    res = Kladr.query.filter(Kladr.NAME.startswith(val)).all()
    return jsonify([{'name': r.NAME,
                    'code': '0000000000000000'} for r in res])
    # name = [" ".join([record.NAME, record.SOCR])]
    # parent = record.parent
    # while parent:
    #     record = Kladr.query.filter(Kladr.CODE == parent.ljust(13, "0")).first()
    #     name.insert(0, " ".join([record.NAME, record.SOCR]))
    #     parent = record.parent
    # return ", ".join(name)