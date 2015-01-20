# -*- coding: utf-8 -*-
import datetime

from flask import request

from application.lib.apiutils import api_method
from application.models.enums import PrenatalRiskRate
from application.models.exists import Organisation, Person
from blueprints.risar.app import module


__author__ = 'mmalkov'


def search_events(**kwargs):
    from calendar import timegm
    from application.lib.sphinx_search import Search, SearchConfig
    from application.lib.utils import safe_date

    import pprint
    pprint.pprint(kwargs)

    query = Search(indexes=['risar_events'], config=SearchConfig)
    if 'fio' in kwargs and kwargs['fio']:
        query = query.match(kwargs['fio'])
    if 'org_id' in kwargs:
        query = query.filter(org_id__eq=int(kwargs['org_id']))
    if 'doc_id' in kwargs:
        query = query.filter(exec_person_id__eq=int(kwargs['doc_id']))
    if 'external_id' in kwargs:
        query = query.filter(external_id__eq=kwargs['external_id'])
    if 'risk' in kwargs:
        query = query.filter(risk__eq=kwargs['risk'])
    if 'bdate' in kwargs:
        query = query.filter(bdate__eq=int(timegm(safe_date(kwargs['bdate']).timetuple())/86400))
    if 'psdate' in kwargs:
        query = query.filter(psdate__eq=int(timegm(safe_date(kwargs['psdate']).timetuple())/86400))
    if 'checkup_date' in kwargs:
        query = query.filter(checkups__eq=int(timegm(safe_date(kwargs['checkup_date']).timetuple())/86400))
    if 'quick' in kwargs:
        query = query.filter(exec_date__eq=0)
    result = query.limit(0, 100).ask()
    return result


@module.route('/api/0/search/', methods=['POST', 'GET'])
@api_method
def api_0_event_search():
    data = dict(request.args)
    if request.json:
        data.update(request.json)
    result = search_events(**data)
    return [
        {
            'event_id': row['id'],
            'client_id': row['client_id'],
            'name': row['name'],
            'set_date': datetime.date.fromtimestamp(row['set_date'] * 86400) if row['set_date'] else None,
            'exec_date': datetime.date.fromtimestamp(row['exec_date'] * 86400) if row['exec_date'] else None,
            'external_id': row['external_id'],
            'exec_person_name': row['person_name'],
            'risk': PrenatalRiskRate(row['risk']),
            'mdate': datetime.date.fromtimestamp(row['modify_date']),
            'pddate': datetime.date.fromtimestamp(row['bdate'] * 86400) if row['bdate'] else None,
            'week': min(
                45,
                (datetime.date.today() - datetime.date.fromtimestamp(row['psdate'] * 86400)).days / 7)
            if row['psdate'] else None
        }
        for row in result['result']['items']
    ]


@module.route('/api/0/lpu_list.json', methods=['POST', 'GET'])
@api_method
def api_0_lpu_list():
    query = Organisation.query
    query = query.filter(
        Organisation.deleted == 0,
        Organisation.isHospital == 1,  # This is not right, however, f**k it
    )
    return query.all()


@module.route('/api/0/lpu_doctors_list.json', methods=['POST', 'GET'])
@api_method
def api_0_lpu_doctors_list():
    query = Person.query
    query = query.filter(
        Person.deleted == 0
    )
    if 'org_id' in request.args:
        query = query.filter(
            Person.org_id == request.args['org_id']
        )
    return [
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
    ]