# -*- encoding: utf-8 -*-
from flask import render_template, abort
from jinja2 import TemplateNotFound
from ..app import module
from flask.ext.login import current_user

# noinspection PyUnresolvedReferences
from . import api_json
from application.lib.utils import breadcrumb


@module.route('/')
def index():
    try:
        return render_template('event/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/event.html')
def html_event_info():
    # event_id = int(request.args['event_id'])
    # В зависимости от ролей и прав разный лейаут
    if current_user.role_in('admin'):
        form_role = 'admin'
    elif current_user.role_in('doctor'):
        form_role = 'doctor'
    elif current_user.role_in(('rRegistartor', 'clinicRegistrator')):
        form_role = 'receptionist'
    else:
        raise
    return render_template('event/event_info.html', form_role=form_role)


@module.route('/event_new.html')
@breadcrumb(u'Новое обращение')
def new_event():
    return html_event_info()