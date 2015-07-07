# -*- coding: utf-8 -*-
from flask import request
from sqlalchemy.orm import joinedload

from ..app import module
from blueprints.useraccount.models import UserMail
from nemesis.lib.apiutils import api_method
from nemesis.models.exists import Person
from nemesis.models.utils import safe_current_user_id

__author__ = 'viruzzz-kun'


@module.route('/api/mail')
@api_method
def api_mail():
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 10))
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))
    query = UserMail.query \
        .filter(UserMail.recipient_id == safe_current_user_id()) \
        .order_by(UserMail.id.desc()) \
        .options(
            joinedload(UserMail.sender),
            joinedload(UserMail.recipient),
        )
    if ids:
        return query.filter(UserMail.id.in_(ids)).all()
    if skip:
        query = query.offset(skip)
    if limit:
        query = query.limit(limit)
    return query.all()


@module.route('/api/persons/<int:user_id>')
@api_method
def api_person(user_id):
    j = request.args
    summary = j.get('summary', False)
    person = Person.query.get(user_id)
    return {
        'id': person.id,
        'name': person.nameText,
    }
