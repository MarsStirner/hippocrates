# -*- coding: utf-8 -*-
from flask import request

from application.lib.utils import jsonify
from application.models.event import Event, EventType
from application.models.exists import Organisation, Person, rbRequestType
from blueprints.risar.app import module

__author__ = 'mmalkov'


@module.route('/api/0/search/', methods=['POST', 'GET'])
def api_0_event_search():
    data = request.args
    query = Event.query \
        .join(EventType, rbRequestType) \
        .filter(rbRequestType.code == 'pregnancy')
    if 'org_id' in data:
        query = query.filter(Event.org_id == data['org_id'])
    if 'doc_id' in data:
        query = query.filter(Event.execPerson_id == data['doc_id'])
    return jsonify([
        {
            'event_id': row.id,
            'client_id': row.client_id,
            'name': row.client.nameText,
            'set_date': row.setDate,
            'exec_date': row.execDate,
        }
        for row in query
    ])


@module.route('/api/0/lpu_list.json', methods=['POST', 'GET'])
def api_0_lpu_list():
    query = Organisation.query
    query = query.filter(
        Organisation.deleted == 0,
        Organisation.isHospital == 1,  # This is not right, however, f**k it
    )
    return jsonify(query.all())


@module.route('/api/0/lpu_doctors_list.json', methods=['POST', 'GET'])
def api_0_lpu_doctors_list():
    query = Person.query
    query = query.filter(
        Person.deleted == 0
    )
    if 'org_id' in request.args:
        query = query.filter(
            Person.org_id == request.args['org_id']
        )
    return jsonify([
        {
            'id': row.id,
            'name': row.nameText,
            'full_name': u'%s%s' % (row.nameText, u' (%s)' % row.speciality if row.speciality else ''),
            'code': row.code,
            'federal_code': row.federalCode,
            'regional_code': row.regionalCode,
            'org_name': row.organisation.shortName if row.org_id else None,
            'org_id': row.org_id,
        }
        for row in query
    ])