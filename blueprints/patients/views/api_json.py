# -*- coding: utf-8 -*-
import json

from flask import abort, request

from application.database import db
from application.lib.utils import public_endpoint, jsonify, get_new_uuid
from blueprints.patients.app import module
from application.lib.sphinx_search import SearchPatient
from application.models.exists import (rbPolicyType,
    rbSocStatusClass, rbSocStatusType, rbAccountingSystem, rbContactType, rbRelationType,
    rbBloodType, Bloodhistory, rbPrintTemplate)
from blueprints.schedule.views.jsonify import (ClientVisualizer, PrintTemplateVisualizer,
    Format)
from blueprints.patients.lib.utils import *
from flask.helpers import make_response

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
@public_endpoint
def api_search_clients():
    try:
        query_string = request.args['q']
    except KeyError or ValueError:
        return abort(404)

    if query_string:
        result = SearchPatient.search(query_string)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            clients = Client.query.filter(Client.id.in_(id_list)).all()
        else:
            clients = []
    else:
        clients = Client.query.limit(100).all()
    print_templates = rbPrintTemplate.query.filter(rbPrintTemplate.context == 'token').all()
    context = ClientVisualizer(Format.JSON)
    print_context = PrintTemplateVisualizer()
    return jsonify({'clients': map(context.make_client_info, clients),
                    'print_templates': map(print_context.make_template_info, print_templates),
                    })


@module.route('/api/patient.json')
@public_endpoint
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
@public_endpoint
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
        client.sexCode = 1 if client_info['sex'] == u'М' else 2
        client.SNILS = client_info['SNILS'].replace(" ", "").replace("-", "") if client_info['SNILS'] else ''
        client.notes = client_info['notes'] if client_info['notes'] else ''
        client.birthDate = client_info['birthDate']
        if not client.uuid:
            new_uuid = get_new_uuid()
            client.uuid = new_uuid

        db.session.add(client)

        if client_info['document']['typeCode']:
            if not client.document:
                client_document = get_new_document(client_info['document'])
                client.documents.append(client_document)
            else:
                doc = get_modified_document(client, client_info['document'])
                db.session.add(doc)

        if client_info['compulsoryPolicy'].get('typeCode'):
            if not client.compulsoryPolicy:
                policy = get_new_policy(client_info['compulsoryPolicy'])
                client.policies.append(policy)
            else:
                policies = get_modified_policy(client, client_info['compulsoryPolicy'])
                client.policies.extend(policies)

        if client_info['voluntaryPolicy'].get('typeCode'):
            if not client.voluntaryPolicy:
                policy = get_new_policy(client_info['voluntaryPolicy'])
                client.policies.append(policy)
            else:
                policies = get_modified_policy(client, client_info['voluntaryPolicy'])
                client.policies.extend(policies)

        for ss_info in client_info['socStatuses']:
            if not 'id' in ss_info:
                ss = get_new_soc_status(ss_info)
                client.socStatuses.append(ss)
            else:
                ss = get_modified_soc_status(client, ss_info)

        # for allergy in client_info['allergies']:
        #     if not 'id' in allergy:
        #         item = create_new_allergy(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == allergy['id'], client.allergies)[0]
        #     item.name = allergy['nameSubstance']
        #     item.createDate = allergy['createDate'].split('T')[0]
        #     item.power = allergy['power']
        #     item.notes = allergy['notes']
        #     item.deleted = allergy['deleted']
        #
        # for intolerance in client_info['intolerances']:
        #     if not 'id' in intolerance:
        #         item = create_new_intolerance(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == intolerance['id'], client.intolerances)[0]
        #     item.name = intolerance['nameMedicament']
        #     item.createDate = intolerance['createDate'].split('T')[0]
        #     item.power = intolerance['power']
        #     item.notes = intolerance['notes']
        #     item.deleted = intolerance['deleted']
        #
        # for identification in client_info['identifications']:
        #     if not 'id' in identification:
        #         item = create_new_identification(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == identification['id'], client.identifications)[0]
        #     item.accountingSystems = rbAccountingSystem.query.filter(rbAccountingSystem.code == identification['accountingSystem_code']).first()
        #     item.checkDate = identification['checkDate'].split('T')[0]
        #     item.identifier = identification['identifier']
        #     item.deleted = identification['deleted']
        #
        # for blood in client_info['bloodHistory']:
        #     if not 'id' in blood:
        #         item = Bloodhistory()
        #         item.client_id = client.id
        #         db.session.add(item)
        #         item.bloodType = rbBloodType.query.filter(rbBloodType.code == blood['bloodGroup_code']).first()
        #         item.bloodDate = blood['bloodDate'].split('T')[0]
        #         item.person_id = blood['person_id']
        #
        # for relation in client_info['direct_relations']:
        #     if not 'id' in relation:
        #         item = create_new_direct_relation(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == relation['id'], client.direct_relations)[0]
        #     item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
        #     item.other = Client.query.filter(Client.id == relation['other_id']).first()
        #
        # for relation in client_info['reversed_relations']:
        #     if not 'id' in relation:
        #         item = create_new_reversed_relation(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == relation['id'], client.reversed_relations)[0]
        #     item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
        #     item.other = Client.query.filter(Client.id == relation['other_id']).first()
        #
        # for contact in client_info['contacts']:
        #     if not 'id' in contact:
        #         item = create_new_contact(client.id)
        #         db.session.add(item)
        #     else:
        #         item = filter(lambda x: x.id == contact['id'], client.contacts)[0]
        #     item.contactType = rbContactType.query.filter(rbContactType.code == contact['contactType_code']).first()
        #     item.contact = contact['contact']
        #     item.deleted = contact['deleted']
        #     item.notes = contact['notes']

        db.session.commit()
    except KeyError, e:
        db.session.rollback()
        raise
        raise ClientSaveException(u'Ошибка сохранения данных клиента', str(e))
    except ValueError:
        db.session.rollback()
        raise
        return abort(404)
    except:
        db.session.rollback()
        raise
        return abort(404)

    return ''


@module.route('/api/save_delete_document.json')
@public_endpoint
def api_delete_document():
    document_info = json.loads(request.args['document'])
    if 'documentText' in document_info:
        document = ClientDocument.query.get(document_info['id'])
    elif 'policyText' in document_info:
        document = ClientPolicy.query.get(document_info['id'])
    document.deleted = 1
    db.session.add(document)
    db.session.commit()
    return ''