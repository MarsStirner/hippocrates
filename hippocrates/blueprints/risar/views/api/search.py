# -*- coding: utf-8 -*-
import datetime
import json
import math
import time

from blueprints.reports.jasper_client import JasperReport
from blueprints.risar.lib.represent import represent_age
from blueprints.risar.lib.search import get_workgroupname_by_code
from flask import request, make_response
from flask.ext.login import current_user

from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_int
from nemesis.lib.vesta import Vesta
from nemesis.models.enums import PerinatalRiskRate
from nemesis.models.exists import Organisation, Person
from blueprints.risar.app import module
from nemesis.models.organisation import OrganisationCurationAssoc
from nemesis.models.person import PersonCurationAssoc, rbOrgCurationLevel


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


def sphinx_local_days(date_string):
    date_string = date_string[:10]
    date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    return int(time.mktime(date.timetuple()))


def search_events(paginated=True, **kwargs):
    from nemesis.lib.sphinx_search import Search, SearchConfig

    query = Search(indexes=['risar_events'], config=SearchConfig)
    if 'fio' in kwargs and kwargs['fio']:
        query = query.match(u'@name {0}'.format(kwargs['fio']), raw=True)
    if 'areas' in kwargs:
        areas = [area['code'][:5] for area in kwargs['areas']]
        query = query.filter(area__in=areas)
    if 'org_ids' in kwargs:
        query = query.filter(org_id__in=list(kwargs['org_ids']))
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
    client_workgroup = kwargs.get('client_workgroup')
    if client_workgroup:
        work_code = client_workgroup.get('code')
        if work_code:
            query = query.match('@client_work_code %s' % work_code, raw=True)
    age_min = safe_int(kwargs.get('age_min'))
    if age_min:
        query = query.filter(client_age__gte=age_min)
    age_max = safe_int(kwargs.get('age_max'))
    if age_max:
        query = query.filter(client_age__lte=age_max)
    
    if 'closed' in kwargs:
        if kwargs['closed']:
            query = query.filter(exec_date__neq=0)
        else:
            query = query.filter(exec_date__eq=0)

    if paginated:
        per_page = kwargs.get('per_page', 10)
        page = kwargs.get('page', 1)
        from_ = (page - 1) * per_page
        query = query.limit(from_, per_page)
    else:
        query = query.limit(0, 99999)
    query = query.options(max_matches=10000)
    result = query.ask()
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
                'org_name': row["org_name"],
                'set_date': datetime.date.fromtimestamp(row['set_date']) if row['set_date'] else None,
                'exec_date': datetime.date.fromtimestamp(row['exec_date']) if row['exec_date'] else None,
                'external_id': row['external_id'],
                'exec_person_name': row['person_name'],
                'client_age': row.get('client_age', 0),
                'client_workgroup': get_workgroupname_by_code(row.get('client_work_code', '')),
                'literal_age': represent_age(row.get('client_age', 0)),
                'risk': PerinatalRiskRate(row['risk']),
                'mdate': datetime.date.fromtimestamp(row['card_modify_date'] * 86400)
                    if 'card_modify_date' in row and row['card_modify_date'] else None,
                'pddate': datetime.date.fromtimestamp(row['bdate'] * 86400) if row['bdate'] else None,
                'curators': get_org_curators(safe_int(row['org_id']), '2'),
                'week':((
                    (min(today, datetime.date.fromtimestamp(row['bdate'])) if row['bdate'] else today) -
                    datetime.date.fromtimestamp(row['psdate'])
                ).days / 7 + 1) if row['psdate'] else None
            }
            for row in result['result']['items']
        ]
    }


@module.route('/api/0/search-print/', methods=['POST'])
def api_0_event_print():
    data = dict(request.args)
    if request.form and request.form.get('json'):
        data.update(json.loads(request.form.get('json')))
    file_format = data.get('print_format')
    result = search_events(paginated=False, **data)

    today = datetime.date.today()
    data = (
        {
            'name': row['name'],
            'external_id': row['external_id'],
            'exec_person_name': row['person_name'],
            'risk': PerinatalRiskRate(row['risk']).name,
            'curators': get_org_curators(safe_int(row['org_id']), '2'),
            'week':((
                (min(today, datetime.date.fromtimestamp(row['bdate'])) if row['bdate'] else today) -
                datetime.date.fromtimestamp(row['psdate'])
            ).days / 7 + 1) if row['psdate'] else None
        }
        for row in result['result']['items']
    )
    jasper_report = JasperReport(
        'SearchPrint',
        '/reports/Hippocrates/Risar/SearchPrint',
        fields=('name', 'external_id', 'exec_person_name', 'risk', 'curators', 'week')
    )
    jasper_report.generate(file_format, data)
    return make_response(jasper_report.get_response_data())


def get_org_curators(org_id, curation_level):
    query_val = Person.query.join(
        PersonCurationAssoc, Person.id == PersonCurationAssoc.person_id
    ).join(
        OrganisationCurationAssoc, PersonCurationAssoc.id == OrganisationCurationAssoc.personCuration_id
    ).join(
        rbOrgCurationLevel, rbOrgCurationLevel.id == PersonCurationAssoc.orgCurationLevel_id
    ).filter(
        OrganisationCurationAssoc.org_id == org_id,
        Person.deleted == 0,
        rbOrgCurationLevel.code == curation_level,
    ).values(
        Person.lastName, Person.firstName
    )
    return u', '.join((u' '.join(x) for x in query_val))

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
    organisation = Organisation.query.get(current_user.org_id) if current_user.org_id else None
    risar_regions = [organisation.area[:2].ljust(11, '0')] if organisation and organisation.area else None
    if not risar_regions:
        risar_regions = app.config.get('RISAR_REGIONS', [])
    for region in risar_regions:
        l1 = Vesta.get_kladr_locality(region)
        l2 = Vesta.get_kladr_locality_list(None, region)
        level1[l1.code] = l1.name
        level2.extend(l2) if l2 else level2.append(l1)
    return level1, sorted(level2, key=lambda x: x.name)


@module.route('/api/0/area_curator_list.json', methods=['POST', 'GET'])
@api_method
def api_0_area_curator_list():
    j = request.get_json()
    areas = j.get('areas')
    query = Person.query
    query = query.join(
        PersonCurationAssoc, Person.id == PersonCurationAssoc.person_id
    ).join(
        OrganisationCurationAssoc, PersonCurationAssoc.id == OrganisationCurationAssoc.personCuration_id
    ).join(
        Organisation, Organisation.id == OrganisationCurationAssoc.org_id
    ).join(
        rbOrgCurationLevel, rbOrgCurationLevel.id == PersonCurationAssoc.orgCurationLevel_id
    ).filter(
        Person.deleted == 0,
        Organisation.deleted == 0,
        Organisation.isLPU == 1,
    )
    if areas:
        regex = '^$|^' + '|^'.join([area['code'][:5] for area in areas if area['code']])
        query = query.filter(Organisation.area.op('regexp')(regex))
    query = query.group_by(
        PersonCurationAssoc.id
    ).order_by(
        Person.lastName, Person.firstName, Person.patrName, rbOrgCurationLevel.name
    )
    return list(query.values(PersonCurationAssoc.id, Person.lastName, Person.firstName, Person.patrName,
                             Person.id.label('person_id'), rbOrgCurationLevel.name))


@module.route('/api/0/curator_lpu_list.json', methods=['POST', 'GET'])
@api_method
def api_0_curator_lpu_list():
    j = request.get_json()
    areas = j.get('areas')
    curators_ids = (x['id'] for x in j.get('curators'))
    query = Organisation.query
    query = query.join(
        OrganisationCurationAssoc, Organisation.id == OrganisationCurationAssoc.org_id
    ).filter(
        OrganisationCurationAssoc.personCuration_id.in_(curators_ids),
        Organisation.deleted == 0,
        Organisation.isLPU == 1,
    )
    if areas:
        regex = '^$|^' + '|^'.join([area['code'][:5] for area in areas if area['code']])
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