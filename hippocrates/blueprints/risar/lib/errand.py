# coding: utf-8

import datetime
import requests

from flask_login import current_user

from nemesis.models.risar import Errand
from nemesis.models.exists import rbCounter
from nemesis.models.enums import ErrandStatus
from nemesis.systemwide import db
from nemesis.lib.utils import safe_traverse, safe_datetime
from nemesis.models.utils import safe_current_user_id
from nemesis.app import app


def create_errand(data):
    errand = Errand()
    errand.setPerson_id = data['set_person']['id']
    errand.execPerson_id = data['exec_person']['id']
    errand.text = data.get('text', '')
    errand.number = get_new_errand_number()
    errand.event_id = data['event_id']
    errand.plannedExecDate = data.get('planned_exec_date', datetime.datetime.now())
    errand.status_id = safe_traverse(data, 'status', 'id') or ErrandStatus.waiting[0]
    errand.communications = data.get('communications')
    return errand


def edit_errand(errand, data):
    is_author = cur_user_is_errand_author(errand)
    errand.execPerson_id = data['exec_person']['id']
    if is_author:
        errand.readingDate = None
        errand.execDate = None
    errand.text = data['text']
    errand.plannedExecDate = safe_datetime(data['planned_exec_date'])
    errand.deleted = data.get('deleted', 0)
    errand.result = data['result']
    errand.communications = data.get('communications')
    if 'errand_files' in data:
        errand = edit_errand_attach_files(errand, data['errand_files'])
    return errand


def edit_errand_attach_files(errand, attach_data):
    cur_attaches = dict((at.id, at) for at in errand.attach_files)
    for at_data in attach_data:
        attach = cur_attaches.pop(at_data['id'], None)
        if attach is not None:
            fm = attach.file_meta
            fm.name = at_data['file_meta']['name']
            fm.note = at_data['file_meta']['note']
    for attach in cur_attaches.values():
        attach.deleted = 1
        attach.file_meta.deleted = 1
    return errand


def mark_errand_as_read(errand, data):
    rd = data.get('reading_date') or datetime.datetime.now()
    errand.readingDate = safe_datetime(rd)
    return errand


def execute_errand(errand, data):
    now = datetime.datetime.now()
    if errand.plannedExecDate:
        if errand.plannedExecDate.date() >= now.date():
            errand.status_id = ErrandStatus.executed[0]
        else:
            errand.status_id = ErrandStatus.late_execution[0]
    exec_date = data.get('exec_date') or now
    errand.execDate = safe_datetime(exec_date)
    if 'text' in data:
        errand.text = data['text']
    return errand


def delete_errand(errand):
    errand.deleted = 1
    return errand


def cur_user_is_errand_author(errand):
    return errand.setPerson_id == current_user.id


errand_notify_events = {'new', 'markread', 'execute', 'delete'}


def notify_errand_change(errand, event):
    sender_id = errand.setPerson_id or safe_current_user_id()
    recipient_id = errand.execPerson_id
    if event not in errand_notify_events:
        raise ValueError('unknown errand notify event')
    topic = 'errand:{0}'.format(event)

    requests.post(app.config['SIMARGL_URL'].rstrip('/') + '/simargl-rpc', json={
        'topic': topic,
        'recipient': recipient_id,
        'sender': sender_id,
        'data': {
            'errand_id': errand.id,
            'event_id': errand.event_id,
            'number': errand.number
        },
        'ctrl': True
    })


def get_new_errand_number():
    """Формирование number (номера поручения)."""
    counter = db.session.query(rbCounter).filter(rbCounter.code == '8').with_for_update().first()
    if not counter:
        return ''
    external_id = _get_errand_number_from_counter(counter.prefix,
                                                  counter.value + 1,
                                                  counter.separator)
    counter.value += 1
    db.session.add(counter)
    return external_id


def _get_errand_number_from_counter(prefix, value, separator):
    def get_date_prefix(val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in [0, 2, 4] or val.count('M') > 2 or val.count('d') > 2:
            return None
        # qt -> python date format
        _map = {'yyyy': '%Y', 'yy': '%y', 'mm': '%m', 'dd': '%d'}
        try:
            format_ = _map.get(val, '%Y')
            date_val = datetime.date.today().strftime(format_)
            check = datetime.datetime.strptime(date_val, format_)
        except ValueError, e:
            return None
        return date_val

    prefix_types = {'date': get_date_prefix}

    prefix_parts = prefix.split(';')
    prefix = []
    for p in prefix_parts:
        for t in prefix_types:
            pos = p.find(t)
            if pos == 0:
                val = p[len(t):]
                if val.startswith('(') and val.endswith(')'):
                    val = prefix_types[t](val[1:-1])
                    if val:
                        prefix.append(val)
    return separator.join(prefix + ['%d' % value])
