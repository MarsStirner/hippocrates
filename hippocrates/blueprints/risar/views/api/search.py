# -*- coding: utf-8 -*-
import datetime
import math

from flask import request
from flask.ext.login import current_user

from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_int
from nemesis.lib.vesta import Vesta
from nemesis.models.enums import PrenatalRiskRate
from nemesis.models.exists import Organisation, Person
from blueprints.risar.app import module


__author__ = 'mmalkov'


def sphinx_days(date_string):
    from calendar import timegm
    from pytz import timezone
    from nemesis.app import app

    date_string = date_string[:10]
    # Шайтан!
    date = datetime.datetime.strptime(date_string, '%Y-%m-%d') \
        .replace(tzinfo=timezone(app.config['TIME_ZONE'])) \
        .astimezone(timezone('UTC')) \
        .date()
    return int(timegm(date.timetuple()) / 86400)


def search_events(**kwargs):
    from nemesis.lib.sphinx_search import Search, SearchConfig

    query = Search(indexes=['risar_events'], config=SearchConfig)
    if 'fio' in kwargs and kwargs['fio']:
        query = query.match(u'@name {0}'.format(kwargs['fio']), raw=True)
    if 'areas' in kwargs:
        areas = [area['code'][:5] for area in kwargs['areas']]
        query = query.filter(area__in=areas)
    if 'org_id' in kwargs:
        query = query.filter(org_id__eq=int(kwargs['org_id']))
    if 'doc_id' in kwargs:
        query = query.filter(exec_person_id__eq=int(kwargs['doc_id']))
    if 'external_id' in kwargs:
        query = query.filter(external_id__eq=kwargs['external_id'])
    if 'risk' in kwargs:
        if isinstance(kwargs['risk'], basestring):
            risk = map(int, kwargs['risk'].split(','))
        else:
            risk = kwargs['risk']
        query = query.filter(risk__in=risk)
    if 'bdate_from' in kwargs:
        query = query.filter(bdate__gte=sphinx_days(kwargs['bdate_from']))
    if 'bdate_to' in kwargs:
        query = query.filter(bdate__lte=sphinx_days(kwargs['bdate_to']))
    if 'psdate' in kwargs:
        query = query.filter(psdate__eq=sphinx_days(kwargs['psdate']))
    if 'checkup_date_from' in kwargs:
        query = query.filter(checkups__gte=sphinx_days(kwargs['checkup_date_from']))
    if 'checkup_date_to' in kwargs:
        query = query.filter(checkups__lte=sphinx_days(kwargs['checkup_date_to']))
    if 'closed' in kwargs:
        if kwargs['closed']:
            query = query.filter(exec_date__neq=0)
        else:
            query = query.filter(exec_date__eq=0)

    per_page = kwargs.get('per_page', 10)
    page = kwargs.get('page', 1)
    from_ = (page - 1) * per_page
    result = query.limit(from_, per_page).ask()
    return result


def search_events_ambulance(**kwargs):
    from nemesis.lib.sphinx_search import Search, SearchConfig

    query = Search(indexes=['risar_events'], config=SearchConfig)
    if 'query' in kwargs and kwargs['query']:
        query = query.match(u'@(name,document,policy) {0}'.format(kwargs['query']), raw=True)
        query = query.options(field_weights={'lastName': 100,
                                             'firstName': 80,
                                             'patrName': 70,
                                             'document': 50,
                                             'policy': 50})
    if 'closed' in kwargs:
        if kwargs['closed']:
            query = query.filter(exec_date__neq=0)
        else:
            query = query.filter(exec_date__eq=0)
    per_page = kwargs.get('per_page', 10)
    page = kwargs.get('page', 1)
    from_ = (page - 1) * per_page
    to_ = page * per_page
    result = query.limit(from_, to_).ask()
    return result


@module.route('/api/0/search/', methods=['POST', 'GET'])
@api_method
def api_0_event_search():
    data = dict(request.args)
    if request.json:
        data.update(request.json)
    per_page = safe_int(data.get('per_page')) or 10
    data['per_page'] = per_page
    result = search_events(**data)

    total = safe_int(result['result']['meta']['total_found'])
    pages = int(math.ceil(total / float(per_page)))
    today = datetime.date.today()
    return {
        'count': total,
        'total_pages': pages,
        'events': [
            {
                'event_id': row['id'],
                'client_id': row['client_id'],
                'name': row['name'],
                'set_date': datetime.date.fromtimestamp(row['set_date']) if row['set_date'] else None,
                'exec_date': datetime.date.fromtimestamp(row['exec_date']) if row['exec_date'] else None,
                'external_id': row['external_id'],
                'exec_person_name': row['person_name'],
                'risk': PrenatalRiskRate(row['risk']),
                'mdate': datetime.date.fromtimestamp(row['card_modify_date']) if 'card_modify_date' in row else None,
                'pddate': datetime.date.fromtimestamp(row['bdate']) if row['bdate'] else None,
                'week':((
                    (min(today, datetime.date.fromtimestamp(row['bdate'])) if row['bdate'] else today) -
                    datetime.date.fromtimestamp(row['psdate'])
                ).days / 7 + 1) if row['psdate'] else None
            }
            for row in result['result']['items']
        ]
    }


@module.route('/api/0/search_ambulance/', methods=['POST', 'GET'])
@api_method
def api_0_event_search_ambulance():
    data = dict(request.args)
    if request.json:
        data.update(request.json)
    per_page = safe_int(data.get('per_page')) or 5
    data['per_page'] = per_page
    result = search_events_ambulance(**data)

    total = safe_int(result['result']['meta']['total_found'])
    pages = int(math.ceil(total / float(per_page)))
    return {
        'count': total,
        'total_pages': pages,
        'events': [
            {
                'event_id': row['id'],
                'client_id': row['client_id'],
                'name': row['name'],
                'birth_date': row['birth_date'],
                'snils': row['snils'],
                'document': row['document'],
                'document_type': row['document_type'],
                'policy': row['policy'],
            }
            for row in result['result']['items']
        ]
    }


@module.route('/api/0/area_list.json', methods=['POST', 'GET'])
@api_method
def api_0_area_list():
    level1 = {}
    level2 = []
    organisation = Organisation.query.get(current_user.org_id)
    risar_regions = [organisation.area[:2].ljust(11, '0')] if organisation else None
    if not risar_regions:
        risar_regions = app.config.get('RISAR_REGIONS', [])
    for region in risar_regions:
        l1 = Vesta.get_kladr_locality(region)
        l2 = Vesta.get_kladr_locality_list("2", region)
        level1[l1.code] = l1.name
        level2.extend(l2) if l2 else level2.append(l1)
    return level1, sorted(level2, key=lambda x: x.name)


@module.route('/api/0/area_lpu_list.json', methods=['POST', 'GET'])
@api_method
def api_0_area_lpu_list():
    j = request.get_json()
    areas = j.get('areas')
    query = Organisation.query
    query = query.filter(
        Organisation.deleted == 0,
        Organisation.isLPU == 1,
    )
    if areas:
        regex = '^' + '|^'.join([area['code'][:5] for area in areas if area['code']])
        query = query.filter(Organisation.area.op('regexp')(regex))
    return query.all()


@module.route('/api/0/lpu_doctors_list.json', methods=['POST', 'GET'])
@api_method
def api_0_lpu_doctors_list():
    result = []
    j = request.get_json()
    org_ids = [org['id'] for org in j.get('orgs')]
    if org_ids:
        query = Person.query
        query = query.filter(
            Person.deleted == 0, Person.org_id.in_(org_ids)
        )
        result = [
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
    return result