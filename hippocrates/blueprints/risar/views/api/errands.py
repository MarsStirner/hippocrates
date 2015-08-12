# -*- coding: utf-8 -*-
from flask import request
from sqlalchemy.orm import joinedload

from ...app import module
from nemesis.models.risar import Errand
from nemesis.lib.apiutils import api_method
from nemesis.models.utils import safe_current_user_id

__author__ = 'viruzzz-kun'


@module.route('/api/errands/summary/')
@api_method
def api_errands_summary():
    query = Errand.query.filter(
        Errand.setPerson_id == safe_current_user_id()
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


@module.route('/api/errands/', methods=["GET"])
@api_method
def api_errands_get():
    unread = int(request.args.get('unread', '0'))
    limit = int(request.args.get('limit', 10))

    result = {}

    query = Errand.query
    if unread:
        query = query.filter(Errand.readingDate.is_(None))
    query = query.filter(Errand.execPerson_id == safe_current_user_id())
    result['count'] = query.count()
    query = query \
        .order_by(Errand.id.desc()) \
        .options(
            joinedload(Errand.setPerson),
            joinedload(Errand.execPerson),
        )
    if limit:
        query = query.limit(limit)
    result['errands'] = query.all()
    return result