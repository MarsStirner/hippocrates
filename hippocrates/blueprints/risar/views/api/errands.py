# -*- coding: utf-8 -*-
import datetime
from flask import request
from sqlalchemy.orm import joinedload

from ...app import module
from nemesis.models.risar import Errand
from nemesis.lib.apiutils import api_method
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db
from blueprints.risar.lib.represent import represent_errand

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
    errands = query.all()
    return {
        'count': count,
        'unread': unread,
        'errands': errands,
    }


@module.route('/api/errands/', methods=["POST"])
@api_method
def api_errands_get():
    limit = int(request.args.get('limit', 10))
    filters = request.get_json()

    unread = int(filters.get('unread', '0'))
    exec_person = filters.get('exec_person')
    set_person = filters.get('set_person')
    show_deleted = filters.get('show_deleted')

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

    query = query.filter(db.or_(Errand.execPerson_id == safe_current_user_id(),
                                Errand.setPerson_id == safe_current_user_id()))

    result['count'] = query.count()
    query = query \
        .order_by(Errand.id.desc()) \
        .options(
            joinedload(Errand.setPerson),
            joinedload(Errand.execPerson),
        )
    if limit:
        query = query.limit(limit)
    result['errands'] = [represent_errand(errand) for errand in query.all()]
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
        errand.readingDate = data['reading_date']
        errand.text = data['text']
        errand.plannedExecDate = data['planned_exec_date']
        errand.deleted = data.get('deleted', 0)
        if data['result']:
            errand.result = data['result']
            errand.execDate = data['exec_date'] if data['exec_date'] else now
        db.session.add(errand)
        db.session.commit()


@module.route('/api/errands/mark_as_read/', methods=["POST"])
@module.route('/api/errands/mark_as_read/<int:errand_id>', methods=["POST"])
@api_method
def api_errand_mark_as_read(errand_id):
    data = request.get_json()
    reading_date = data.get('reading_date', datetime.datetime.now())
    errand = Errand.query.get(errand_id)
    errand.readingDate = reading_date
    db.session.add(errand)
    db.session.commit()

