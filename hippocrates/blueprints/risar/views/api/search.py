# -*- coding: utf-8 -*-
import datetime
import math

from flask import request

from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_int
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
        query = query.match(kwargs['fio'])
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
                'set_date': datetime.date.fromtimestamp(row['set_date'] * 86400) if row['set_date'] else None,
                'exec_date': datetime.date.fromtimestamp(row['exec_date'] * 86400) if row['exec_date'] else None,
                'external_id': row['external_id'],
                'exec_person_name': row['person_name'],
                'risk': PrenatalRiskRate(row['risk']),
                'mdate': datetime.date.fromtimestamp(row['modify_date']),
                'pddate': datetime.date.fromtimestamp(row['bdate'] * 86400) if row['bdate'] else None,
                'week':((
                    (min(today, datetime.date.fromtimestamp(row['bdate'] * 86400)) if row['bdate'] else today) -
                    datetime.date.fromtimestamp(row['psdate'] * 86400)
                ).days / 7 + 1) if row['psdate'] else None
            }
            for row in result['result']['items']
        ]
    }


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