# -*- coding: utf-8 -*-
import json

from flask import abort, request

from application.database import db
from application.lib.utils import public_endpoint, jsonify
from blueprints.patients.app import module
from application.models.exists import (rbPolicyType,
    rbSocStatusClass, rbSocStatusType, rbAccountingSystem, rbContactType, rbRelationType,
    rbBloodType, Bloodhistory)
from blueprints.schedule.views.jsonify import ClientVisualizer
from blueprints.schedule.views.utils import *
from blueprints.schedule.views.uuid_generator import getNewUUID_id

__author__ = 'mmalkov'


@module.route('/api/patient.json')
@public_endpoint
def api_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)
        return jsonify({
            'clientData': context.make_client_info(client),
            'records': context.make_records(client),
            'events': context.make_events(client)
        })
    else:
        client = Client()
        return jsonify({
            'clientData': context.make_client_info(client)
        })


@module.route('/api/save_patient_info.json', methods=['POST'])
@public_endpoint
def api_save_patient_info():
    j = request.json
    try:
        client_info = j['client_info']
        client_id = int(client_info['id'])
        if client_id:
            client = Client.query.get(client_id)
        else:
            client = create_new_client()

        client.lastName = client_info['lastName']
        client.firstName = client_info['firstName']
        client.patrName = client_info['patrName']
        client.sexCode = 1 if client_info['sex'] == u'М' else 2
        client.SNILS = client_info['SNILS'].replace(" ", "").replace("-", "") if client_info['SNILS'] else ''
        client.notes = client_info['notes'] if client_info['notes'] else ''
        client.birthDate = client_info['birthDate']
        client.uuid_id = getNewUUID_id()

        db.session.add(client)
        db.session.commit()

        if not client.document and client_info['document']['number']:
            client_document = create_new_document(client.id, client_info['document'])
            db.session.add(client_document)
        else:
            client.document.serial = client_info['document']['serial']
            client.document.number = client_info['document']['number']
            client.document.date = client_info['document']['begDate']
            client.document.endDate = client_info['document']['endDate']
            client.document.origin = client_info['document']['origin']
            client.document.documentType = rbDocumentType.query.filter(rbDocumentType.code ==
                                                                       client_info['document']['typeCode']).first()

        if client.compulsoryPolicy and check_edit_policy(client.compulsoryPolicy,
                                                         client_info['compulsoryPolicy']['serial'],
                                                         client_info['compulsoryPolicy']['number'],
                                                         client_info['compulsoryPolicy']['typeCode']):
            client.compulsoryPolicy.begDate = client_info['compulsoryPolicy']['begDate']
            client.compulsoryPolicy.endDate = client_info['compulsoryPolicy']['endDate']
            client.compulsoryPolicy.insurer_id = client_info['compulsoryPolicy']['insurer_id']
            client.compulsoryPolicy.modifyDatetime = datetime.datetime.now()
        elif client_info['compulsoryPolicy']['number']:
            client.compulsoryPolicy.deleted = 2
            compulsory_policy = create_new_policy(client_info['compulsoryPolicy'], client.id)
            compulsory_policy.policyType = rbPolicyType.query.filter(rbPolicyType.code ==
                                                                     client_info['compulsoryPolicy']['typeCode']).first()
            db.session.add(compulsory_policy)

        if client.voluntaryPolicy and check_edit_policy(client.compulsoryPolicy,
                                                        client_info['voluntaryPolicy']['serial'],
                                                        client_info['voluntaryPolicyy']['number'],
                                                        client_info['voluntaryPolicy']['typeCode']):
            client.voluntaryPolicy.begDate = client_info['voluntaryPolicy']['begDate']
            client.voluntaryPolicy.endDate = client_info['voluntaryPolicy']['endDate']
            client.voluntaryPolicy.insurer_id = client_info['voluntaryPolicy']['insurer_id']
            client.voluntaryPolicy.modifyDatetime = datetime.datetime.now()
        elif client_info['voluntaryPolicy']['number']:
            client.voluntaryPolicy.deleted = 2
            voluntary_policy = create_new_policy(client_info['voluntaryPolicy'], client.id)
            client.voluntaryPolicy.policyType = rbPolicyType.query.filter(rbPolicyType.code ==
                                                                          client_info['voluntaryPolicy']['typeCode']).first()
            db.session.add(voluntary_policy)

        for soc_status in client_info['socStatuses']:
            if not 'id' in soc_status:
                item = create_new_soc_status(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == soc_status['id'], client.socStatuses)[0]
            item.deleted = soc_status['deleted']
            item.soc_status_class = rbSocStatusClass.query.filter(rbSocStatusClass.code ==
                                                                  soc_status['classCode']).first()
            item.socStatusType = rbSocStatusType.query.filter(rbSocStatusType.code ==
                                                              soc_status['typeCode']).first()
            item.begDate = soc_status['begDate'].split('T')[0]
            if soc_status['endDate']:
                item.endDate = soc_status['endDate'].split('T')[0]

        for allergy in client_info['allergies']:
            if not 'id' in allergy:
                item = create_new_allergy(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == allergy['id'], client.allergies)[0]
            item.name = allergy['nameSubstance']
            item.createDate = allergy['createDate'].split('T')[0]
            item.power = allergy['power']
            item.notes = allergy['notes']
            item.deleted = allergy['deleted']

        for intolerance in client_info['intolerances']:
            if not 'id' in intolerance:
                item = create_new_intolerance(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == intolerance['id'], client.intolerances)[0]
            item.name = intolerance['nameMedicament']
            item.createDate = intolerance['createDate'].split('T')[0]
            item.power = intolerance['power']
            item.notes = intolerance['notes']
            item.deleted = intolerance['deleted']

        for identification in client_info['identifications']:
            if not 'id' in identification:
                item = create_new_identification(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == identification['id'], client.identifications)[0]
            item.accountingSystems = rbAccountingSystem.query.filter(rbAccountingSystem.code == identification['accountingSystem_code']).first()
            item.checkDate = identification['checkDate'].split('T')[0]
            item.identifier = identification['identifier']
            item.deleted = identification['deleted']

        for blood in client_info['bloodHistory']:
            if not 'id' in blood:
                item = Bloodhistory()
                item.client_id = client.id
                db.session.add(item)
                item.bloodType = rbBloodType.query.filter(rbBloodType.code == blood['bloodGroup_code']).first()
                item.bloodDate = blood['bloodDate'].split('T')[0]
                item.person_id = blood['person_id']

        for relation in client_info['direct_relations']:
            if not 'id' in relation:
                item = create_new_direct_relation(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == relation['id'], client.direct_relations)[0]
            item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
            item.other = Client.query.filter(Client.id == relation['other_id']).first()

        for relation in client_info['reversed_relations']:
            if not 'id' in relation:
                item = create_new_reversed_relation(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == relation['id'], client.reversed_relations)[0]
            item.relativeType = rbRelationType.query.filter(rbRelationType.code == relation['relativeType_code']).first()
            item.other = Client.query.filter(Client.id == relation['other_id']).first()

        for contact in client_info['contacts']:
            if not 'id' in contact:
                item = create_new_contact(client.id)
                db.session.add(item)
            else:
                item = filter(lambda x: x.id == contact['id'], client.contacts)[0]
            item.contactType = rbContactType.query.filter(rbContactType.code == contact['contactType_code']).first()
            item.contact = contact['contact']
            item.deleted = contact['deleted']
            item.notes = contact['notes']

        db.session.commit()
    except KeyError or ValueError:
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