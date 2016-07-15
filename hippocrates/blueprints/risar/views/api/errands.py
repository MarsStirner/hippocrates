# -*- coding: utf-8 -*-

from flask import request
from sqlalchemy.orm import joinedload

from ...app import module
from nemesis.models.risar import Errand
from nemesis.lib.apiutils import api_method
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db
from nemesis.lib.utils import safe_int
from hippocrates.blueprints.risar.lib.errand import (create_errand, edit_errand, mark_errand_as_read, execute_errand,
    notify_errand_change, cur_user_is_errand_author, delete_errand)
from hippocrates.blueprints.risar.lib.represent import (represent_errand, represent_errand_edit, represent_errand_shortly,
    represent_errand_summary)
from sqlalchemy import func

__author__ = 'viruzzz-kun'


@module.route('/api/0/errands/summary/')
@api_method
def api_0_errands_summary():
    query = Errand.query.filter(
        Errand.execPerson_id == safe_current_user_id(),
        Errand.deleted == 0
    )
    count = query.count()
    query = query.filter(Errand.readingDate.is_(None))
    unread = query.count()
    query = query.limit(10).options(
        joinedload(Errand.event, innerjoin=True).joinedload('client', innerjoin=True)
    )
    errands = [represent_errand_summary(errand) for errand in query.all()]
    return {
        'count': count,
        'unread': unread,
        'errands': errands,
    }


@module.route('/api/0/errands/', methods=["POST"])
@api_method
def api_0_errands_get():
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


@module.route('/api/0/errand/', methods=["GET"])
@module.route('/api/0/errand/<int:errand_id>', methods=["GET"])
@api_method
def api_0_errand_get(errand_id):
    errand = Errand.query.get(errand_id)
    return represent_errand_edit(errand)


@module.route('/api/0/errand/', methods=["POST"])
@module.route('/api/0/errand/<int:errand_id>', methods=["POST"])
@api_method
def api_0_errand_save(errand_id=None):
    data = request.get_json()
    if not errand_id:
        errand = create_errand(data)
    else:
        errand = Errand.query.get(errand_id)
        errand = edit_errand(errand, data)
    db.session.add(errand)
    db.session.commit()
    if not errand_id:
        notify_errand_change(errand, 'new')
    elif cur_user_is_errand_author(errand):
        notify_errand_change(errand, 'markread')
    return represent_errand_edit(errand)


@module.route('/api/0/errands/mark_as_read/', methods=["POST"])
@module.route('/api/0/errands/mark_as_read/<int:errand_id>', methods=["POST"])
@api_method
def api_0_errand_mark_as_read(errand_id):
    data = request.get_json()
    errand = Errand.query.get(errand_id)
    errand = mark_errand_as_read(errand, data)
    db.session.add(errand)
    db.session.commit()
    notify_errand_change(errand, 'markread')
    return represent_errand_shortly(errand)


@module.route('/api/0/errands/execute/', methods=["POST"])
@module.route('/api/0/errands/execute/<int:errand_id>', methods=["POST"])
@api_method
def api_0_errand_execute(errand_id):
    data = request.get_json()
    errand = Errand.query.get(errand_id)
    errand = execute_errand(errand, data)
    db.session.add(errand)
    db.session.commit()
    notify_errand_change(errand, 'execute')
    return represent_errand_shortly(errand)


@module.route('/api/0/errands/delete/', methods=["DELETE"])
@module.route('/api/0/errands/delete/<int:errand_id>', methods=["DELETE"])
@api_method
def api_0_errand_delete(errand_id):
    errand = Errand.query.get(errand_id)
    errand = delete_errand(errand)
    db.session.add(errand)
    db.session.commit()
    notify_errand_change(errand, 'delete')
    return represent_errand_shortly(errand)
