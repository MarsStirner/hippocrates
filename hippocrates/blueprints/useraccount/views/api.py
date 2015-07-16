# -*- coding: utf-8 -*-
from flask import request
from sqlalchemy.orm import joinedload

from ..app import module
from blueprints.useraccount.models import UserMail
from nemesis.lib.apiutils import api_method
from nemesis.models.exists import Person
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


@module.route('/api/mail/summary/')
@api_method
def api_mail_summary():
    query = UserMail.query.filter(
        UserMail.recipient_id == safe_current_user_id(),
        UserMail.folder == 'inbox'
    )
    count = query.count()
    query = query.filter(UserMail.read == 0)
    unread = query.count()
    query = query.limit(10)
    messages = query.all()
    return {
        'count': count,
        'unread': unread,
        'messages': messages,
    }


@module.route('/api/mail/', methods=["GET"])
@module.route('/api/mail/<folder>', methods=["GET"])
@api_method
def api_mail_get(folder='inbox'):
    unread = int(request.args.get('unread', '0'))
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 10))
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))

    result = {}

    query = UserMail.query
    if unread:
        query = query.filter(UserMail.read == 0)
    if folder == 'star':
        query = query.filter(UserMail.mark == 1)
        folder = 'inbox'
    if folder == 'sent':
        query = query.filter(UserMail.sender_id == safe_current_user_id())
    else:
        query = query.filter(UserMail.recipient_id == safe_current_user_id())
    query = query.filter(UserMail.folder == folder)
    result['count'] = query.count()
    query = query \
        .order_by(UserMail.id.desc()) \
        .options(
            joinedload(UserMail.sender),
            joinedload(UserMail.recipient),
        )
    if ids:
        query = query.filter(UserMail.id.in_(ids)).all()
    else:
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
    result['messages'] = query.all()
    return result


def mail_update(ids, field, value):
    UserMail.query.filter(
        UserMail.id.in_(ids),
    ).update({field: value}, synchronize_session=False)
    db.session.commit()


@module.route('/api/mail/', methods=["PUT", "DELETE"])
@module.route('/api/mail/<uid>/<mode>', methods=["PUT", "DELETE"])
@api_method
def api_mail_mark(uid, mode):
    if mode not in ('read', 'mark'):
        raise
    value = request.method == 'PUT' and 1 or 0
    ids = map(int, filter(None, uid.split(':')))
    if not ids:
        raise Exception('ids must me set')
    mail_update(ids, mode, value)


@module.route('/api/mail/', methods=["MOVE"])
@module.route('/api/mail/<uid>/<folder>', methods=["MOVE"])
@api_method
def api_mail_move(uid, folder):
    ids = map(int, filter(None, uid.split(':')))
    if not ids:
        raise Exception('ids must me set')
    mail_update(ids, 'folder', folder)
