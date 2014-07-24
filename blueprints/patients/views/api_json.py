# -*- coding: utf-8 -*-

from flask import abort, request

from application.systemwide import db
from application.lib.utils import jsonify, logger, parse_id, public_endpoint
from blueprints.patients.app import module
from application.lib.sphinx_search import SearchPatient
from application.lib.jsonify import ClientVisualizer
from application.models.client import Client
from blueprints.patients.lib.utils import *


__author__ = 'mmalkov'


@module.errorhandler(ClientSaveException)
def handle_client_error(err):
    return jsonify({
        'name': err.message,
        'data': {
            'err_msg': err.data
        }
    }, 422, 'error')


@module.route('/api/search_clients.json')
def api_search_clients():
    try:
        query_string = request.args['q']
        limit = int(request.args.get('limit', 100))
    except KeyError or ValueError:
        return abort(404)

    base_query = Client.query
    id_list = []

    if query_string:
        result = SearchPatient.search(query_string)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            base_query = base_query.filter(Client.id.in_(id_list))
        else:
            return jsonify([])
    clients = base_query.order_by(db.func.field(Client.id, *id_list)).limit(limit).all()
    context = ClientVisualizer()
    if 'short' in request.args:
        return jsonify(map(context.make_short_client_info, clients))
    else:
        return jsonify(map(context.make_search_client_info, clients))


@module.route('/api/patient.json')
def api_patient_get():
    client_id = parse_id(request.args, 'client_id')
    if client_id is False:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)

        if 'for_servicing' in request.args:
            return jsonify(context.make_client_info_for_servicing(client))
        elif 'short' in request.args:
            return jsonify(context.make_short_client_info(client))
        return jsonify({
            'client_data': context.make_client_info(client)
        })
    else:
        client = Client()
        db.session.add(client)  # требуется привязанный к сессии клиент для доступа к некоторым атрибутам (documents)
        return jsonify({
            'client_data': context.make_client_info(client)
        })

@module.route('/api/appointments.json')
@public_endpoint
def api_patient_appointments():
    client_id = parse_id(request.args, 'client_id')
    every = request.args.get('every', False)
    if client_id is False:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
        return jsonify(
            context.make_appointments(client, every)
        )
    return jsonify(None, 400, 'Can\'t!')


@module.route('/api/save_patient_info.json', methods=['POST'])
def api_patient_save():
    client_data = request.json
    client_id = parse_id(client_data, 'client_id', True)
    if client_id is False:
        return abort(404)

    err_msg = u'Ошибка сохранения данных пациента'
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

            reg_addr_info = client_data.get('reg_addresses')
            actual_reg_address = None
            if reg_addr_info:
                for reg_addr in reg_addr_info:
                    ra = add_or_update_address(client, reg_addr)
                    if ra.deleted != 1 and ra.deleted != 2:
                        actual_reg_address = ra
                    db.session.add(ra)

            live_addr_info = client_data.get('live_addresses')
            if live_addr_info:
                for live_addr in live_addr_info:
                    same_as_reg = live_addr.get('synced', False)
                    if same_as_reg:
                        la = add_or_update_copy_address(client, live_addr, actual_reg_address)
                    else:
                        la = add_or_update_address(client, live_addr)
                    db.session.add(la)

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

            allergy_info = client_data.get('allergies')
            if allergy_info:
                for allergy in allergy_info:
                    alg = add_or_update_allergy(client, allergy)
                    db.session.add(alg)

            intolerance_info = client_data.get('intolerances')
            if intolerance_info:
                for intolerance in intolerance_info:
                    intlr = add_or_update_intolerance(client, intolerance)
                    db.session.add(intlr)

            ss_info = client_data.get('soc_statuses')
            if ss_info:
                for ss in ss_info:
                    sstat = add_or_update_soc_status(client, ss)
                    db.session.add(sstat)

            relation_info = client_data.get('relations')
            if relation_info:
                for relation in relation_info:
                    rel = add_or_update_relation(client, relation)
                    db.session.add(rel)

            contact_info = client_data.get('contacts')
            if contact_info:
                for contact in contact_info:
                    cont = add_or_update_contact(client, contact)
                    db.session.add(cont)
        else:
            client = Client()
            client_info = client_data.get('info')
            if not client_info:
                raise ClientSaveException(err_msg, u'Отсутствует основная информация о пациенте.')
            client = set_client_main_info(client, client_info)
            db.session.add(client)

            id_doc_info = client_data.get('id_docs')
            if id_doc_info:
                for id_doc in id_doc_info:
                    doc = add_or_update_doc(client, id_doc)
                    db.session.add(doc)

            reg_addr_info = client_data.get('reg_addresses')
            actual_reg_address = None
            if reg_addr_info:
                for reg_addr in reg_addr_info:
                    ra = add_or_update_address(client, reg_addr)
                    if ra.deleted != 1 and ra.deleted != 2:
                        actual_reg_address = ra
                    db.session.add(ra)

            live_addr_info = client_data.get('live_addresses')
            if live_addr_info:
                for live_addr in live_addr_info:
                    same_as_reg = live_addr.get('synced', False)
                    if same_as_reg:
                        la = add_or_update_copy_address(client, live_addr, actual_reg_address)
                    else:
                        la = add_or_update_address(client, live_addr)
                    db.session.add(la)

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

            allergy_info = client_data.get('allergies')
            if allergy_info:
                for allergy in allergy_info:
                    alg = add_or_update_allergy(client, allergy)
                    db.session.add(alg)

            intolerance_info = client_data.get('intolerances')
            if intolerance_info:
                for intolerance in intolerance_info:
                    intlr = add_or_update_intolerance(client, intolerance)
                    db.session.add(intlr)

            ss_info = client_data.get('soc_statuses')
            if ss_info:
                for ss in ss_info:
                    sstat = add_or_update_soc_status(client, ss)
                    db.session.add(sstat)

            relation_info = client_data.get('relations')
            if relation_info:
                for relation in relation_info:
                    rel = add_or_update_relation(client, relation)
                    db.session.add(rel)

            contact_info = client_data.get('contacts')
            if contact_info:
                for contact in contact_info:
                    cont = add_or_update_contact(client, contact)
                    db.session.add(cont)

    #     for id_info in client_info['identifications']:
    #         if not 'id' in id_info:
    #             id_ext = get_new_identification(id_info)
    #             client.identifications.append(id_ext)
    #         else:
    #             id_ext = get_modified_identification(client, id_info)
    #             db.session.add(id_ext)
        db.session.commit()
    except ClientSaveException:
        raise
    except Exception, e:
        logger.error(e, exc_info=True)
        db.session.rollback()
        return jsonify(
            {
                'name': err_msg,
                'data': {
                    'err_msg': 'INTERNAL SERVER ERROR'
                }
            },
            500,
            'save client data error'
        )

    return jsonify(int(client))

# for tests without external kladr
@module.route('/api/kladr_city.json', methods=['GET'])
def api_kladr_city_get():
    from application.models.kladr_models import Kladr
    val = request.args['city']
    res = Kladr.query.filter(Kladr.NAME.startswith(val)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])


@module.route('/api/kladr_street.json', methods=['GET'])
def api_kladr_street_get():
    from application.models.kladr_models import Street
    city = request.args['city']
    street = request.args['street']
    res = Street.query.filter(Street.CODE.startswith(city[:-2]), Street.NAME.startswith(street)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])