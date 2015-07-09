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


def int_mail_summary():
    return {
        'inbox_count': UserMail.query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.folder == 'inbox'
        ).count(),
        'unread': UserMail.query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.read == 0,
            UserMail.folder == 'inbox'
        ).count(),
    }

@module.route('/api/mail', methods=["GET"])
@api_method
def api_mail_get():
    summary = 'summary' in request.args
    folder = request.args.get('folder', 'inbox')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 10))
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))

    result = int_mail_summary()

    query = UserMail.query
    if folder == 'sent':
        query = query.filter(UserMail.sender_id == safe_current_user_id())
        result['count'] = UserMail.query.filter(
            UserMail.sender_id == safe_current_user_id()
        ).count()
    elif folder == 'star':
        folder = 'inbox'
        result['count'] = UserMail.query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.folder == folder,
            UserMail.mark == 1,
        ).count()
        query = query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.folder == folder,
            UserMail.mark == 1
        )
    else:
        result['count'] = UserMail.query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.folder == folder,
        ).count()
        query = query.filter(
            UserMail.recipient_id == safe_current_user_id(),
            UserMail.folder == folder
        )

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
    if not summary:
        result['messages'] = query.all()
    return result

@module.route('/api/mail/mark', methods=["POST"])
@api_method
def api_mail_mark():
    mark = request.args.get('mark', '1')
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))
    if not ids:
        raise Exception('ids must me set')
    UserMail.query\
        .filter(
            UserMail.id.in_(ids),
            UserMail.recipient_id == safe_current_user_id(),
        ).update({'mark': int(mark)}, synchronize_session=False)
    db.session.commit()
    return int_mail_summary()


@module.route('/api/mail/read', methods=["POST"])
@api_method
def api_mail_read():
    read = request.args.get('read', '1')
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))
    if not ids:
        raise Exception('ids must me set')
    UserMail.query \
        .filter(
            UserMail.id.in_(ids),
            UserMail.recipient_id == safe_current_user_id(),
        ).update({'read': int(read)}, synchronize_session=False)
    db.session.commit()
    return int_mail_summary()


@module.route('/api/mail/move', methods=["POST"])
@api_method
def api_mail_move():
    folder = request.args.get('folder', 'trash')
    ids = map(int, filter(None, request.args.get('ids', '').split(':')))
    if not ids:
        raise Exception('ids must me set')
    UserMail.query \
        .filter(
            UserMail.id.in_(ids),
            UserMail.recipient_id == safe_current_user_id(),
        ).update({'folder': folder}, synchronize_session=False)
    db.session.commit()
    return int_mail_summary()

