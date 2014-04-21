# -*- coding: utf-8 -*-

from flask import abort, request
from flask.helpers import make_response

from application.systemwide import db
from application.lib.utils import jsonify, get_new_uuid
from blueprints.patients.app import module
from application.lib.sphinx_search import SearchPatient
from blueprints.schedule.views.jsonify import (ClientVisualizer, Format)
from blueprints.patients.lib.utils import *

__author__ = 'mmalkov'


class ClientSaveException(Exception):
    def __init__(self, message, data):
        super(ClientSaveException, self).__init__(message)
        self.data = data


@module.errorhandler(ClientSaveException)
def handle_client_error(err):
    return make_response(jsonify({'name': err.message,
                                  'data': err.data},
                                 422, 'error')[0],
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
    context = ClientVisualizer(Format.JSON)
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
            'clientData': context.make_client_info(client),
            'appointments': context.make_appointments(client),
            'events': context.make_events(client)
        })
    else:
        client = Client()
        db.session.add(client)
        return jsonify({
            'clientData': context.make_client_info(client)
        })


@module.route('/api/save_patient_info.json', methods=['POST'])
def api_patient_save():
    j = request.json
    try:
        client_info = j['client_info']
        client_id = client_info.get('id')
        if client_id:
            client = Client.query.get(int(client_id))
        else:
            client = create_new_client()

        client.lastName = client_info['lastName']
        client.firstName = client_info['firstName']
        client.patrName = client_info['patrName']
        client.sexCode = client_info['sex']['id'] if client_info['sex']['id'] != 0 else 1 # todo: fix
        client.SNILS = client_info['SNILS'].replace(" ", "").replace("-", "") if client_info['SNILS'] else ''
        client.notes = client_info['notes'] if client_info['notes'] else ''
        client.birthDate = client_info['birthDate']
        if not client.uuid:
            new_uuid = get_new_uuid()
            client.uuid = new_uuid

        db.session.add(client)

        if client_info['document'].get('documentType'):
            if not client.document:
                client_document = get_new_document(client_info['document'])
                client.documents.append(client_document)
            else:
                docs = get_modified_document(client, client_info['document'])
                db.session.add(docs[0])
                if docs[1]:
                    client.documents.append(docs[1])

        if client_info['compulsoryPolicy'].get('policyType'):
            if not client.compulsoryPolicy:
                policy = get_new_policy(client_info['compulsoryPolicy'])
                client.policies.append(policy)
            else:
                policies = get_modified_policy(client, client_info['compulsoryPolicy'])
                db.session.add(policies[0])
                if policies[1]:
                    client.policies.append(policies[1])

        if client_info['voluntaryPolicy'].get('policyType'):
            if not client.voluntaryPolicy:
                policy = get_new_policy(client_info['voluntaryPolicy'])
                client.policies.append(policy)
            else:
                policies = get_modified_policy(client, client_info['voluntaryPolicy'])
                db.session.add(policies[0])
                if policies[1]:
                    client.policies.append(policies[1])

        for ss_info in client_info['socStatuses']:
            if not 'id' in ss_info:
                ss = get_new_soc_status(ss_info)
                client.socStatuses.append(ss)
            else:
                ss = get_modified_soc_status(client, ss_info)
                db.session.add(ss)

        for blood_info in client_info['bloodHistory']:
            if not 'id' in blood_info:
                blood = get_new_blood(blood_info)
                client.blood_history.append(blood)

        for allergy_info in client_info['allergies']:
            if not 'id' in allergy_info:
                allergy = get_new_allergy(allergy_info)
                client.allergies.append(allergy)
            else:
                allergy = get_modified_allergy(client, allergy_info)
                db.session.add(allergy)

        for intolerance_info in client_info['intolerances']:
            if not 'id' in intolerance_info:
                intolerance = get_new_intolerance(intolerance_info)
                client.intolerances.append(intolerance)
            else:
                intolerance = get_modified_intolerance(client, intolerance_info)
                db.session.add(intolerance)

        for id_info in client_info['identifications']:
            if not 'id' in id_info:
                id_ext = get_new_identification(id_info)
                client.identifications.append(id_ext)
            else:
                id_ext = get_modified_identification(client, id_info)
                db.session.add(id_ext)

        for relation_info in client_info['direct_relations']:
            if not 'id' in relation_info:
                rel = get_new_direct_relation(relation_info)
                client.direct_relations.append(rel)
            else:
                rel = get_modified_direct_relation(client, relation_info)
                db.session.add(rel)

        for relation_info in client_info['reversed_relations']:
            if not 'id' in relation_info:
                rel = get_new_reversed_relation(relation_info)
                client.reversed_relations.append(rel)
            else:
                rel = get_modified_reversed_relation(client, relation_info)
                db.session.add(rel)

        for contact_info in client_info['contacts']:
            if not 'id' in contact_info:
                contact = get_new_contact(contact_info)
                client.contacts.append(contact)
            else:
                contact = get_modified_contact(client, contact_info)
                db.session.add(contact)

        for doc_info in client_info['documentHistory']:
            if doc_info['deleted'] == 1:
                doc = get_deleted_document(client, doc_info)
                db.session.add(doc)

        db.session.commit()
    except KeyError, e:
        db.session.rollback()
        raise
        raise ClientSaveException(u'Ошибка сохранения данных клиента', str(e))
    # except ValueError:
    #     db.session.rollback()
    #     raise
    #     return abort(404)
    except:
        db.session.rollback()
        raise
        return abort(404)

    return jsonify(int(client))