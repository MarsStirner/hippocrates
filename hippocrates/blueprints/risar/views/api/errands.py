# -*- coding: utf-8 -*-
import datetime
from flask import request
from sqlalchemy.orm import joinedload

from ...app import module
from nemesis.models.risar import Errand, rbErrandStatus
from nemesis.lib.apiutils import api_method
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db
from nemesis.lib.utils import safe_int, string_to_datetime
from blueprints.risar.lib.represent import represent_errand
from sqlalchemy import func

__author__ = 'viruzzz-kun'


@module.route('/api/errands/summary/')
@api_method
def api_errands_summary():
    query = Errand.query.filter(
        Errand.execPerson_id == safe_current_user_id()
    )
    count = query.count()
    query = query.filter(Errand.readingDate.is_(None))
    unread = query.count()
    query = query.limit(10)
    errands = [represent_errand(errand) for errand in query.all()]
    return {
        'count': count,
        'unread': unread,
        'errands': errands,
    }


@module.route('/api/errands/', methods=["POST"])
@api_method
def api_errands_get():
    per_page = safe_int(request.args.get('per_page', 5))
    page = safe_int(request.args.get('page', 1))
    filters = request.get_json() or {}

    unread = int(filters.get('unread', '0'))
    exec_person = filters.get('exec_person')
    set_person = filters.get('set_person')
    show_deleted = filters.get('show_deleted')
    create_date_from = filters.get('create_date_from')
    create_date_to = filters.get('create_date_to')
    planned_edate_from = filters.get('planned_edate_from')
    planned_edate_to = filters.get('planned_edate_to')
    edate_from = filters.get('edate_from')
    edate_to = filters.get('edate_to')
    number = filters.get('number')
    status = filters.get('status')

    result = {}

    query = Errand.query
    if unread:
        query = query.filter(Errand.readingDate.is_(None))
    if exec_person:
        query = query.filter(Errand.execPerson_id == exec_person.get('id'))
    if set_person:
        query = query.filter(Errand.setPerson_id == set_person.get('id'))
    if not show_deleted:
        query = query.filter(Errand.deleted == 0)
    if create_date_from:
        query = query.filter(func.DATE(Errand.createDatetime) >= create_date_from)
    if create_date_to:
        query = query.filter(func.DATE(Errand.createDatetime) <= create_date_to)
    if planned_edate_from:
        query = query.filter(func.DATE(Errand.plannedExecDate) >= planned_edate_from)
    if planned_edate_to:
        query = query.filter(func.DATE(Errand.plannedExecDate) <= planned_edate_to)
    if edate_from:
        query = query.filter(func.DATE(Errand.execDate) >= edate_from)
    if edate_to:
        query = query.filter(func.DATE(Errand.execDate) <= edate_to)
    if number:
        query = query.filter(Errand.number == number)
    if status:
        query = query.filter(Errand.status_id == status.get('id'))

    query = query.filter(db.or_(Errand.execPerson_id == safe_current_user_id(),
                                Errand.setPerson_id == safe_current_user_id()))

    result['count'] = query.count()
    query = query \
        .order_by(Errand.id.desc()) \
        .options(
            joinedload(Errand.setPerson),
            joinedload(Errand.execPerson),
        )

    pagination = query.paginate(page, per_page)
    result['total_pages'] = pagination.pages
    result['errands'] = [represent_errand(errand) for errand in pagination.items]
    return result

@module.route('/api/errands/edit/', methods=["POST"])
@module.route('/api/errands/edit/<int:errand_id>', methods=["POST"])
@api_method
def api_errand_edit(errand_id):
    now = datetime.datetime.now()
    data = request.get_json()
    errand = Errand.query.get(errand_id)
    if data:
        errand.execPerson_id = data['exec_person']['id']
        errand.readingDate = string_to_datetime(data['reading_date'])
        errand.text = data['text']
        errand.plannedExecDate = string_to_datetime(data['planned_exec_date'])
        errand.deleted = data.get('deleted', 0)
        errand.result = data['result']
        if data.get('exec', 0):
            if errand.plannedExecDate.date() >= now.date():
                errand.status = rbErrandStatus.query.filter(rbErrandStatus.code == u'executed').first()
            else:
                errand.status = rbErrandStatus.query.filter(rbErrandStatus.code == u'late_execution').first()
            errand.execDate = data['exec_date'] if data['exec_date'] else now
        db.session.add(errand)
        db.session.commit()


@module.route('/api/errands/mark_as_read/', methods=["POST"])
@module.route('/api/errands/mark_as_read/<int:errand_id>', methods=["POST"])
@api_method
def api_errand_mark_as_read(errand_id):
    data = request.get_json()
    reading_date = data.get('reading_date', '')
    errand = Errand.query.get(errand_id)
    errand.readingDate = string_to_datetime(reading_date) if reading_date else datetime.datetime.now()
    db.session.add(errand)
    db.session.commit()
