# -*- encoding: utf-8 -*-
from ast import literal_eval
from flask import render_template, abort, request, redirect, url_for, current_app, session

from jinja2 import TemplateNotFound, Environment, PackageLoader

from ..app import module, _config
from ..lib.data import Log_Data
from ..lib.helpers import datetimeformat_filter, strpdatetime_filter, nl2br_filter
from datetime import datetime, timedelta
from ..config import MODULE_NAME


ROWS_PER_PAGE = 20


@module.route('/', methods=['GET', 'POST'])
@module.route('/<int:page>/', methods=['GET', 'POST'])
def index(page=None):
    current_app.jinja_env.filters['datetimeformat'] = datetimeformat_filter
    current_app.jinja_env.filters['strptime'] = strpdatetime_filter
    current_app.jinja_env.filters['nl2br'] = nl2br_filter
    log_obj = Log_Data()
    levels = log_obj.get_levels()
    owners = log_obj.get_owners()
    find = dict()
    if request.form:
        if MODULE_NAME in session:
            session[MODULE_NAME] = dict()
        session[MODULE_NAME] = request.form

    if MODULE_NAME in session and session[MODULE_NAME]:
        owner = session[MODULE_NAME].get('owner')
        if owner:
            try:
                owner = literal_eval(owner)
            except ValueError as e:
                print e
            except Exception as e:
                print e
            find['owner'] = owner
        level = session[MODULE_NAME].get('level')
        if level:
            find['level'] = level
        start = session[MODULE_NAME].get('start')
        end = session[MODULE_NAME].get('end')
        if start:
            find['start'] = datetime.strptime(start, '%d.%m.%Y')
        if end:
            find['end'] = datetime.strptime(end, '%d.%m.%Y') + timedelta(hours=23, minutes=59, seconds=59)

    if page is None:
        page = 1
    skip = (page - 1) * ROWS_PER_PAGE
    _count = log_obj.get_count(find=find)
    num_rows = 0
    if _count:
        num_rows = _count['result']
    data = log_obj.get_list(find=find, skip=skip, limit=ROWS_PER_PAGE)
    try:
        return render_template('logging/index.html',
                               levels=levels.get('level') if levels else None,
                               owners=owners.get('result') if owners else None,
                               data=data.get('result') if data else None,
                               form_data=session[MODULE_NAME] if MODULE_NAME in session else dict(),
                               page=page,
                               num_pages=num_rows/ROWS_PER_PAGE)
    except TemplateNotFound:
        abort(404)
